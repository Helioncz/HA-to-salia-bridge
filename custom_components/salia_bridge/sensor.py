"""Sensors for Hardy Barth Salia chargers and the SMA bridge status."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CP_STATE_MAP, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Salia charger sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for coord in data["coordinators"]:
        entities.append(SaliaPowerSensor(coord))
        entities.append(SaliaActualPowerSensor(coord))
        entities.append(SaliaOfferedCurrentSensor(coord))
        entities.append(SaliaCurrentLimitSensor(coord))
        entities.append(SaliaStateSensor(coord))
    async_add_entities(entities)


class _SaliaBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.device_name,
            manufacturer="Hardy Barth",
            model="Salia",
            configuration_url=f"http://{coordinator.host}/",
        )


class SaliaPowerSensor(_SaliaBase):
    _attr_translation_key = "charger_power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power")

    @property
    def native_value(self) -> float | None:
        p0 = self.coordinator.port0()
        try:
            offered = p0["ci"]["evse"]["basic"]["power"]["offered"]
            return round(float(offered))
        except (KeyError, TypeError, ValueError):
            return None


class SaliaActualPowerSensor(_SaliaBase):
    """Actual charging power from the charger's own meter (if it has one)."""

    _attr_translation_key = "charger_actual_power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "actual_power")

    @property
    def native_value(self) -> float | None:
        p0 = self.coordinator.port0()
        meter = (p0.get("metering") or {}).get("meter") or {}
        if str(meter.get("available")) != "1":
            return None  # no meter on this charger
        try:
            return round(float(p0["metering"]["power"]["active_total"]["actual"]))
        except (KeyError, TypeError, ValueError):
            return None


class SaliaOfferedCurrentSensor(_SaliaBase):
    _attr_translation_key = "charger_offered_current"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "offered_current")

    @property
    def native_value(self) -> float | None:
        p0 = self.coordinator.port0()
        try:
            return round(float(p0["ci"]["evse"]["basic"]["current"]["offered"]), 1)
        except (KeyError, TypeError, ValueError):
            return None


class SaliaCurrentLimitSensor(_SaliaBase):
    _attr_translation_key = "charger_current_limit"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "current_limit")

    @property
    def native_value(self) -> float | None:
        p0 = self.coordinator.port0()
        try:
            return float(p0["ci"]["evse"]["basic"]["grid_current_limit"]["actual"])
        except (KeyError, TypeError, ValueError):
            return None


class SaliaStateSensor(_SaliaBase):
    _attr_translation_key = "charger_state"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "state")

    @property
    def native_value(self) -> str | None:
        p0 = self.coordinator.port0()
        state = (p0.get("cp") or {}).get("state")
        if state is None:
            return None
        return CP_STATE_MAP.get(state, state)

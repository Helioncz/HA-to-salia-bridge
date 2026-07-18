"""Number control: set the Salia charging current limit (A)."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SaliaCurrentNumber(c) for c in data["coordinators"])


class SaliaCurrentNumber(CoordinatorEntity, NumberEntity):
    """Set the charging current limit via PUT /api/secc {grid_current_limit}."""

    _attr_has_entity_name = True
    _attr_translation_key = "set_current"
    _attr_native_min_value = 6
    _attr_native_max_value = 16
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_set_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.device_name,
            manufacturer="Hardy Barth",
            model="Salia",
            configuration_url=f"http://{coordinator.host}/",
        )

    @property
    def native_value(self) -> float | None:
        p0 = self.coordinator.port0()
        try:
            return float(p0["ci"]["evse"]["basic"]["grid_current_limit"]["actual"])
        except (KeyError, TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_put({"grid_current_limit": str(int(round(value)))})

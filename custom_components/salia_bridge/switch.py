"""Switch control: enable/pause charging on the Salia."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SaliaChargingSwitch(c) for c in data["coordinators"])


class SaliaChargingSwitch(CoordinatorEntity, SwitchEntity):
    """On = charging allowed, Off = paused (PUT salia/pausecharging)."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging_enabled"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_charging_enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.device_name,
            manufacturer="Hardy Barth",
            model="Salia",
            configuration_url=f"http://{coordinator.host}/",
        )

    @property
    def is_on(self) -> bool | None:
        p0 = self.coordinator.port0()
        pause = (p0.get("salia") or {}).get("pausecharging")
        # Salia omits the flag when idle/no vehicle -> treat as "charging allowed".
        return str(pause) != "1"  # 1 = paused

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_put({"salia/pausecharging": "0"})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_put({"salia/pausecharging": "1"})

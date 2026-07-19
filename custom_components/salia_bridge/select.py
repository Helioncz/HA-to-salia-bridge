"""Select control: charge mode (Eco / Power / Quick) on the Salia."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# Salia internal chargemode values (from /api salia.chargemode).
# eco = PV surplus, power = dynamic load management, manual = quick/full power.
CHARGE_MODES = ["eco", "power", "manual"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SaliaChargeModeSelect(c) for c in data["coordinators"])


class SaliaChargeModeSelect(CoordinatorEntity, SelectEntity):
    """Charge mode selector (PUT /api/secc {salia/chargemode})."""

    _attr_has_entity_name = True
    _attr_translation_key = "charge_mode"
    _attr_icon = "mdi:ev-station"
    _attr_options = CHARGE_MODES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_charge_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.device_name,
            manufacturer="Hardy Barth",
            model="Salia",
            configuration_url=f"http://{coordinator.host}/",
        )

    @property
    def current_option(self) -> str | None:
        p0 = self.coordinator.port0()
        mode = (p0.get("salia") or {}).get("chargemode")
        return mode if mode in CHARGE_MODES else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_put({"salia/chargemode": option})
        await self.coordinator.async_request_refresh()

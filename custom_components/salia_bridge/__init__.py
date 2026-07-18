"""Salia Bridge: emulate an SMA Energy Meter from HA data + read Salia chargers."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SALIA_HOST_1,
    CONF_SALIA_HOST_2,
    CONF_SALIA_NAME_1,
    CONF_SALIA_NAME_2,
    DEFAULT_NAME_1,
    DEFAULT_NAME_2,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SaliaCoordinator
from .sma_emitter import SmaEmitter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Salia Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    cfg = {**entry.data, **entry.options}

    # 1) start the SMA Energy Meter emulator (broadcasts grid power)
    emitter = SmaEmitter(hass, cfg)
    await emitter.async_start()

    # 2) set up coordinators for configured Salia chargers
    coordinators: list[SaliaCoordinator] = []
    for host_key, name_key, default in (
        (CONF_SALIA_HOST_1, CONF_SALIA_NAME_1, DEFAULT_NAME_1),
        (CONF_SALIA_HOST_2, CONF_SALIA_NAME_2, DEFAULT_NAME_2),
    ):
        host = cfg.get(host_key)
        if host:
            coord = SaliaCoordinator(hass, host, cfg.get(name_key) or default)
            await coord.async_config_entry_first_refresh()
            coordinators.append(coord)

    hass.data[DOMAIN][entry.entry_id] = {"emitter": emitter, "coordinators": coordinators}

    if coordinators:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    if data.get("emitter"):
        await data["emitter"].async_stop()
    ok = True
    if data.get("coordinators"):
        ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

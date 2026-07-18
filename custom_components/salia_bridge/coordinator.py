"""Data coordinator that polls a Hardy Barth Salia charger /api/ endpoint."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import SALIA_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SaliaCoordinator(DataUpdateCoordinator):
    """Fetch and cache the /api/ JSON of one Salia charger."""

    def __init__(self, hass: HomeAssistant, host: str, name: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"salia_{host}",
            update_interval=timedelta(seconds=SALIA_SCAN_INTERVAL),
        )
        self.host = host
        self.device_name = name
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        url = f"http://{self.host}/api/"
        try:
            async with async_timeout.timeout(8):
                async with self._session.get(url) as resp:
                    resp.raise_for_status()
                    return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Salia {self.host} unreachable: {err}") from err

    def port0(self) -> dict:
        return (self.data or {}).get("secc", {}).get("port0", {}) or {}

    async def async_put(self, payload: dict) -> None:
        """Send a control command to the charger (PUT /api/secc)."""
        url = f"http://{self.host}/api/secc"
        try:
            async with async_timeout.timeout(8):
                async with self._session.put(url, json=payload) as resp:
                    resp.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Salia %s control failed (%s): %s", self.host, payload, err)
            raise
        await self.async_request_refresh()

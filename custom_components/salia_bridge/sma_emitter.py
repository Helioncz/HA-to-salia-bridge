"""Emulate an SMA Energy Meter (Speedwire multicast) from HA entities.

Broadcasts an SMA EMETER datagram (protocol 0x6069) once per second so that
devices like the Hardy Barth Salia (Mains type = "SMA Energymeter") can read
the grid connection-point power. The datagram layout mirrors a real SMA Energy
Meter and has been verified to be accepted by the Salia charge controller.
"""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
import time

from homeassistant.core import HomeAssistant

from .const import (
    CONF_MCAST_IF,
    CONF_POWER_L1,
    CONF_POWER_L2,
    CONF_POWER_L3,
    CONF_POWER_TOTAL,
    CONF_SIGN_INVERT,
    CONF_SMA_SERIAL,
    CONF_VOLT_L1,
    CONF_VOLT_L2,
    CONF_VOLT_L3,
    DEFAULT_SERIAL,
    DEFAULT_SUSYID,
    SMA_INTERVAL,
    SMA_MCAST_GRP,
    SMA_MCAST_PORT,
)

_LOGGER = logging.getLogger(__name__)


def _u32(v: float) -> bytes:
    return struct.pack(">I", max(0, int(round(v))) & 0xFFFFFFFF)


def _u64(v: float) -> bytes:
    return struct.pack(">Q", max(0, int(round(v))) & 0xFFFFFFFFFFFFFFFF)


def _obis(ch: int, idx: int, typ: int, tar: int) -> bytes:
    return bytes([ch, idx, typ, tar])


class SmaEmitter:
    """Reads configured HA entities and broadcasts an SMA EM datagram."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self.hass = hass
        self.cfg = config
        self.serial = int(config.get(CONF_SMA_SERIAL, DEFAULT_SERIAL))
        self._sock: socket.socket | None = None
        self._task: asyncio.Task | None = None
        self.last_total = 0.0
        self.running = False

    # --- entity reading ---
    def _val(self, key: str, default: float = 0.0) -> float:
        ent = self.cfg.get(key)
        if not ent:
            return default
        st = self.hass.states.get(ent)
        if st is None or st.state in (None, "", "unknown", "unavailable"):
            return default
        try:
            return float(st.state)
        except (ValueError, TypeError):
            return default

    def _grid(self) -> tuple[float, float, float, float]:
        """Return signed (total, l1, l2, l3) grid power in W (negative = export)."""
        l1 = self._val(CONF_POWER_L1)
        l2 = self._val(CONF_POWER_L2)
        l3 = self._val(CONF_POWER_L3)
        if self.cfg.get(CONF_POWER_TOTAL):
            total = self._val(CONF_POWER_TOTAL)
        else:
            total = l1 + l2 + l3
        s = -1.0 if self.cfg.get(CONF_SIGN_INVERT) else 1.0
        return total * s, l1 * s, l2 * s, l3 * s

    # --- datagram ---
    def build_datagram(self) -> bytes:
        total, l1, l2, l3 = self._grid()
        self.last_total = total

        def cs(x: float) -> tuple[float, float]:
            return max(x, 0.0), max(-x, 0.0)

        consume, supply = cs(total)
        l1c, l1s = cs(l1)
        l2c, l2s = cs(l2)
        l3c, l3s = cs(l3)
        v1 = self._val(CONF_VOLT_L1)
        v2 = self._val(CONF_VOLT_L2)
        v3 = self._val(CONF_VOLT_L3)

        b = b""
        # totals (active power in 0.1 W units; energy counters left at 0)
        b += _obis(0, 1, 4, 0) + _u32(consume * 10)
        b += _obis(0, 1, 8, 0) + _u64(0)
        b += _obis(0, 2, 4, 0) + _u32(supply * 10)
        b += _obis(0, 2, 8, 0) + _u64(0)
        # per-phase consume/supply
        b += _obis(0, 21, 4, 0) + _u32(l1c * 10)
        b += _obis(0, 22, 4, 0) + _u32(l1s * 10)
        b += _obis(0, 41, 4, 0) + _u32(l2c * 10)
        b += _obis(0, 42, 4, 0) + _u32(l2s * 10)
        b += _obis(0, 61, 4, 0) + _u32(l3c * 10)
        b += _obis(0, 62, 4, 0) + _u32(l3s * 10)
        # voltages (mV)
        if v1:
            b += _obis(0, 32, 4, 0) + _u32(v1 * 1000)
        if v2:
            b += _obis(0, 52, 4, 0) + _u32(v2 * 1000)
        if v3:
            b += _obis(0, 72, 4, 0) + _u32(v3 * 1000)
        # software version marker
        b += _obis(144, 0, 0, 0) + bytes([2, 0, 52, 0])

        ticker = int(time.time() * 1000) & 0xFFFFFFFF
        data2 = (
            struct.pack(">H", 0x6069)
            + struct.pack(">H", DEFAULT_SUSYID)
            + _u32(self.serial)
            + struct.pack(">I", ticker)
            + b
        )
        pkt = b"SMA\x00"
        pkt += struct.pack(">H", 4) + struct.pack(">H", 0x02A0) + struct.pack(">I", 1)
        pkt += struct.pack(">H", len(data2)) + struct.pack(">H", 0x0010) + data2
        pkt += struct.pack(">H", 0) + struct.pack(">H", 0)
        return pkt

    # --- lifecycle ---
    async def async_start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 8)
        iface = self.cfg.get(CONF_MCAST_IF)
        if iface:
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(iface))
            except OSError:
                _LOGGER.warning("Invalid multicast interface %s, using default", iface)
        self._sock = sock
        self.running = True
        self._task = self.hass.loop.create_task(self._run())
        _LOGGER.info("SMA emitter started (serial=%s) -> %s:%s", self.serial, SMA_MCAST_GRP, SMA_MCAST_PORT)

    async def _run(self) -> None:
        while self.running:
            try:
                self._sock.sendto(self.build_datagram(), (SMA_MCAST_GRP, SMA_MCAST_PORT))
            except Exception:  # noqa: BLE001
                _LOGGER.exception("SMA multicast send failed")
            await asyncio.sleep(SMA_INTERVAL)

    async def async_stop(self) -> None:
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        if self._sock:
            self._sock.close()
            self._sock = None
        _LOGGER.info("SMA emitter stopped")

# Salia Bridge

[![HACS: Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Home Assistant custom integration that lets **Hardy Barth Salia** wallboxes do
**PV-surplus charging** using grid data from *any* inverter/meter you already
have in Home Assistant (GoodWe, Solax, Fronius, a shelly meter, …).

It does two things:

1. **Emulates an SMA Energy Meter** inside Home Assistant. It reads the grid
   connection-point power from the HA entities you choose and broadcasts it on
   the network as SMA Speedwire multicast. The Salia (set to **Mains type = SMA
   Energymeter**) receives it and uses it for surplus/eco charging.
2. **Reads 1–2 Salia chargers** over their local `/api/` and exposes sensors
   (offered power, current limit, state).

This solves the common problem that the Salia can only read a fixed list of
inverters/meters directly — now **HA is the meter**.

## Why?

The Salia's "GoodWe / Sungrow / …" mains drivers need a live Modbus/UDP link to
that specific device, which often isn't reachable (single-client Modbus, WiFi
only, wrong unit id …). The Salia **does** natively accept an *SMA Energy Meter*
over multicast — so we present HA's data as one.

## Requirements

- Home Assistant that already has entities for the grid power (total in W, or
  per-phase L1/L2/L3). Negative = export/feed-in is the expected convention
  (there's a *sign invert* switch if your meter is the other way round).
- HA and the Salia on the **same LAN / L2 segment** (multicast must reach it).
  This works out of the box on Home Assistant OS (host networking).

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/Helioncz/HA-to-salia-bridge`, category **Integration**.
2. Install **Salia Bridge**, then **restart Home Assistant**.
3. **Settings → Devices & Services → Add Integration → Salia Bridge**.

### Manual install

Copy `custom_components/salia_bridge` into your `<config>/custom_components/`
and restart Home Assistant.

## Configure

In the setup dialog:

| Field | Meaning |
|---|---|
| **SMA serial number** | Any number, e.g. `1900000000`. Enter the **same** number in the Salia. |
| **Sign invert** | Turn on if the Salia shows import when you actually export. |
| **Grid power – total** | Entity with the grid power in W (`−` = export). Optional if you use L1/L2/L3. |
| **Grid power – L1/L2/L3** | Per-phase grid power in W. If total is empty, the sum is used. |
| **Voltage L1/L2/L3** | Optional, sent to the meter. |
| **SOC** | Optional battery state of charge. |
| **Multicast interface** | Optional; HA's LAN IP if it has several NICs. |
| **Salia 1/2 – IP** | IP of each charger to read (optional). |

### On each Salia charger

Open the charger web UI → **Configuration → Mains options**:

- **Mains type:** `SMA Energymeter`
- **Serial:** the same number you entered above (e.g. `1900000000`)
- **Save → Reboot**

> In a master/slave setup, configure the **master** only; the slaves get their
> allocation from the master.

## Entities

For each configured charger:

- `sensor.<name>_offered_power` – offered/allocated charging power (W)
- `sensor.<name>_current_limit` – current limit (A)
- `sensor.<name>_state` – Control-Pilot state (Volno / Připojeno / Nabíjí …)

## Notes

- The SMA emulator broadcasts once per second.
- No polling of the inverter is added — it just reuses entities you already have.
- Tested against Hardy Barth Salia PLCC (firmware 2.2.x).

## License

MIT

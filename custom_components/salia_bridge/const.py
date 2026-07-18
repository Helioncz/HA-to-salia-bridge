"""Constants for the Salia Bridge integration."""

DOMAIN = "salia_bridge"
PLATFORMS = ["sensor", "number", "switch"]

# --- Config keys: SMA energy-meter emulator ---
CONF_SMA_SERIAL = "sma_serial"
CONF_SIGN_INVERT = "sign_invert"
CONF_POWER_TOTAL = "power_total"
CONF_POWER_L1 = "power_l1"
CONF_POWER_L2 = "power_l2"
CONF_POWER_L3 = "power_l3"
CONF_SOC = "soc"
CONF_VOLT_L1 = "voltage_l1"
CONF_VOLT_L2 = "voltage_l2"
CONF_VOLT_L3 = "voltage_l3"
CONF_MCAST_IF = "multicast_interface"

# --- Config keys: Hardy Barth Salia chargers ---
CONF_SALIA_HOST_1 = "salia_host_1"
CONF_SALIA_HOST_2 = "salia_host_2"
CONF_SALIA_NAME_1 = "salia_name_1"
CONF_SALIA_NAME_2 = "salia_name_2"

# --- Defaults ---
DEFAULT_SERIAL = 1900000000
DEFAULT_SUSYID = 349            # SMA Energy Meter SusyID
DEFAULT_NAME = "Salia Bridge"
DEFAULT_NAME_1 = "Nabíječka levá"
DEFAULT_NAME_2 = "Nabíječka pravá"

# --- SMA Speedwire multicast ---
SMA_MCAST_GRP = "239.12.255.254"
SMA_MCAST_PORT = 9522
SMA_INTERVAL = 1.0             # seconds between multicast datagrams

# --- Salia REST ---
SALIA_SCAN_INTERVAL = 20       # seconds

CP_STATE_MAP = {
    "A": "Volno",
    "B": "Připojeno",
    "C": "Nabíjí",
    "D": "Nabíjí (ventilace)",
    "E": "Bez proudu",
    "F": "Chyba",
}

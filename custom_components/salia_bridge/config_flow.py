"""Config flow for Salia Bridge."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_MCAST_IF,
    CONF_POWER_L1,
    CONF_POWER_L2,
    CONF_POWER_L3,
    CONF_POWER_TOTAL,
    CONF_SALIA_HOST_1,
    CONF_SALIA_HOST_2,
    CONF_SALIA_NAME_1,
    CONF_SALIA_NAME_2,
    CONF_SIGN_INVERT,
    CONF_SMA_SERIAL,
    CONF_SOC,
    CONF_VOLT_L1,
    CONF_VOLT_L2,
    CONF_VOLT_L3,
    DEFAULT_NAME,
    DEFAULT_NAME_1,
    DEFAULT_NAME_2,
    DEFAULT_SERIAL,
    DOMAIN,
)

_SENSOR = EntitySelector(EntitySelectorConfig(domain="sensor"))
_SENSOR_OPT = EntitySelector(EntitySelectorConfig(domain="sensor"))


def _schema(d: dict[str, Any]) -> vol.Schema:
    """Build the form schema, pre-filled from d."""
    def opt(key, selector):
        # optional entity/text field
        if d.get(key):
            return vol.Optional(key, default=d[key])
        return vol.Optional(key)

    return vol.Schema(
        {
            vol.Required(
                CONF_SMA_SERIAL, default=d.get(CONF_SMA_SERIAL, DEFAULT_SERIAL)
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=4294967295, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_SIGN_INVERT, default=d.get(CONF_SIGN_INVERT, False)): bool,
            opt(CONF_POWER_TOTAL, _SENSOR): _SENSOR_OPT,
            opt(CONF_POWER_L1, _SENSOR): _SENSOR_OPT,
            opt(CONF_POWER_L2, _SENSOR): _SENSOR_OPT,
            opt(CONF_POWER_L3, _SENSOR): _SENSOR_OPT,
            opt(CONF_SOC, _SENSOR): _SENSOR_OPT,
            opt(CONF_VOLT_L1, _SENSOR): _SENSOR_OPT,
            opt(CONF_VOLT_L2, _SENSOR): _SENSOR_OPT,
            opt(CONF_VOLT_L3, _SENSOR): _SENSOR_OPT,
            opt(CONF_MCAST_IF, None): TextSelector(),
            opt(CONF_SALIA_HOST_1, None): TextSelector(),
            vol.Optional(
                CONF_SALIA_NAME_1, default=d.get(CONF_SALIA_NAME_1, DEFAULT_NAME_1)
            ): TextSelector(),
            opt(CONF_SALIA_HOST_2, None): TextSelector(),
            vol.Optional(
                CONF_SALIA_NAME_2, default=d.get(CONF_SALIA_NAME_2, DEFAULT_NAME_2)
            ): TextSelector(),
        }
    )


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    """Coerce serial to int, drop empty strings."""
    out = {k: v for k, v in user_input.items() if v not in (None, "")}
    if CONF_SMA_SERIAL in out:
        out[CONF_SMA_SERIAL] = int(out[CONF_SMA_SERIAL])
    return out


class SaliaBridgeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_NAME, data=_clean(user_input))
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SaliaBridgeOptionsFlow(config_entry)


class SaliaBridgeOptionsFlow(OptionsFlow):
    """Allow reconfiguring entities/serial/hosts after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            # store on the entry.data by replacing options; __init__ merges data+options
            return self.async_create_entry(title="", data=_clean(user_input))
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))

"""Config flow for Kamstrup 403."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import callback

from .const import DEFAULT_BAUDRATE, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, DOMAIN
from .kamstrup import Kamstrup


class KamstrupConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kamstrup 403."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            port = user_input[CONF_PORT]
            client = Kamstrup(port, DEFAULT_BAUDRATE, DEFAULT_TIMEOUT)
            try:
                await client.connect()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(port)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=port, data=user_input)
            finally:
                await client.disconnect()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PORT): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return KamstrupOptionsFlow()


class KamstrupOptionsFlow(OptionsFlow):
    """Handle options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                    vol.Required(
                        CONF_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_TIMEOUT, DEFAULT_TIMEOUT
                        ),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=5.0)),
                }
            ),
        )

"""Config flow for the KALO Thermostat integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult

from .api import BeyonnexApiClient, BeyonnexAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KaloThermostatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KALO Thermostat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = BeyonnexApiClient(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )
            try:
                await api.authenticate()
                room_groups = await api.get_room_groups()
            except BeyonnexAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "cannot_connect"
            else:
                # Use first room group name as title
                title = "KALO"
                if room_groups:
                    title = room_groups[0].get("displayName", "KALO").title()

                # Prevent duplicate entries for the same email
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_REFRESH_TOKEN: api.refresh_token,
                    },
                )
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration (e.g. after password change or device remount)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = BeyonnexApiClient(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )
            try:
                await api.authenticate()
                await api.get_room_groups()
            except BeyonnexAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during reconfiguration")
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_REFRESH_TOKEN: api.refresh_token,
                    },
                )
            finally:
                await api.close()

        entry = self._get_reconfigure_entry()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=entry.data.get(CONF_EMAIL)): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

"""The KALO Thermostat integration."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import BeyonnexApiClient
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_REFRESH_TOKEN, DOMAIN, PLATFORMS
from .coordinator import KaloCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KALO Thermostat from a config entry."""
    session = aiohttp.ClientSession()
    api = BeyonnexApiClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    # Restore refresh token if available
    if CONF_REFRESH_TOKEN in entry.data:
        api.refresh_token = entry.data[CONF_REFRESH_TOKEN]

    # Authenticate and store updated refresh token
    auth_result = await api.authenticate()
    if api.refresh_token:
        new_data = {**entry.data, CONF_REFRESH_TOKEN: api.refresh_token}
        hass.config_entries.async_update_entry(entry, data=new_data)

    coordinator = KaloCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        await entry_data["api"].close()
        await entry_data["session"].close()

    return unload_ok

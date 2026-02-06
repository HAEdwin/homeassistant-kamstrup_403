"""Kamstrup 403 integration for Home Assistant."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DEFAULT_BAUDRATE, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT
from .coordinator import KamstrupCoordinator
from .kamstrup import Kamstrup
from .sensor import ALL_REGISTERS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kamstrup 403 from a config entry."""
    port = entry.data[CONF_PORT]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    timeout = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    client = Kamstrup(port, DEFAULT_BAUDRATE, timeout)
    try:
        await client.connect()
    except Exception as err:
        raise ConfigEntryNotReady(f"Cannot connect to {port}") from err

    coordinator = KamstrupCoordinator(
        hass, client, ALL_REGISTERS, timedelta(seconds=scan_interval)
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await client.disconnect()
        raise

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: KamstrupCoordinator = entry.runtime_data
        await coordinator.client.disconnect()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

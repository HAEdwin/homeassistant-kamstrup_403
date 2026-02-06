"""Diagnostics for Kamstrup 403."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import KamstrupCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator: KamstrupCoordinator = entry.runtime_data
    return {
        "config_entry": entry.as_dict(),
        "data": coordinator.data,
        "registers": coordinator.registers,
    }

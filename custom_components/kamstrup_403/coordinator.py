"""DataUpdateCoordinator for Kamstrup 403."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from serial import SerialException

from .const import DOMAIN, MULTIPLE_REGISTERS_MAX
from .kamstrup import Kamstrup

_LOGGER = logging.getLogger(__name__)


class KamstrupCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Coordinator to manage Kamstrup data fetching with dynamic registration."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: Kamstrup,
        scan_interval: timedelta,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        self.client = client
        self._commands: list[int] = []

    def register_command(self, command: int) -> None:
        """Add a command/register to be polled."""
        if command not in self._commands:
            _LOGGER.debug("Register command %s", command)
            self._commands.append(command)

    def unregister_command(self, command: int) -> None:
        """Remove a command/register from polling."""
        if command in self._commands:
            _LOGGER.debug("Unregister command %s", command)
            self._commands.remove(command)

    @property
    def commands(self) -> list[int]:
        """List of registered commands."""
        return self._commands

    async def _async_update_data(self) -> dict[int, Any]:
        """Fetch data from Kamstrup meter."""
        if not self._commands:
            _LOGGER.debug("No commands registered, skipping update")
            return {}

        _LOGGER.debug("Start update for %d registers", len(self._commands))
        data = {}
        failed_counter = 0

        # Process in chunks (protocol limit)
        chunks: list[list[int]] = [
            self._commands[i : i + MULTIPLE_REGISTERS_MAX]
            for i in range(0, len(self._commands), MULTIPLE_REGISTERS_MAX)
        ]

        for chunk in chunks:
            _LOGGER.debug("Get values for %s", chunk)
            try:
                values = await self.client.read_registers(chunk)
            except SerialException as err:
                _LOGGER.warning("Device disconnected or multiple access on port?")
                raise UpdateFailed("Serial connection error") from err
            except Exception as err:
                _LOGGER.warning("Error reading registers %s: %s", chunk, err)
                raise UpdateFailed(f"Error reading registers: {err}") from err

            if values is None:
                _LOGGER.debug("No values returned for chunk %s", chunk)
                failed_counter += len(chunk)
                continue

            for reg in chunk:
                if reg in values:
                    value, unit = values[reg]
                    data[reg] = {"value": value, "unit": unit}
                    _LOGGER.debug("New value for register %s: %s %s", reg, value, unit)
                else:
                    _LOGGER.debug("No value for register %s", reg)
                    data[reg] = {"value": None, "unit": None}
                    failed_counter += 1

        if failed_counter == len(self._commands):
            _LOGGER.error("No readings from meter - check IR connection")
            persistent_notification.async_create(
                self.hass,
                "No readings from the Kamstrup meter. Please check the IR connection.",
                title="Kamstrup 403 - Connection Failed",
                notification_id=f"{DOMAIN}_ir_connection_failed",
            )
        else:
            _LOGGER.debug(
                "Finished update, %s out of %s readings failed",
                failed_counter,
                len(self._commands),
            )

        return data

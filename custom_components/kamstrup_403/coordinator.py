"""DataUpdateCoordinator for Kamstrup 403."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .kamstrup import Kamstrup

_LOGGER = logging.getLogger(__name__)


class KamstrupCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Coordinator to manage Kamstrup data fetching."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Kamstrup,
        registers: list[int],
        scan_interval: timedelta,
    ) -> None:
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=scan_interval)
        self.client = client
        self.registers = registers

    async def _async_update_data(self) -> dict[int, Any]:
        """Fetch data from Kamstrup meter."""
        data = {}
        # Process in chunks of 8 (protocol limit)
        for i in range(0, len(self.registers), 8):
            chunk = self.registers[i : i + 8]
            try:
                values = await self.client.read_registers(chunk)
            except Exception as err:
                raise UpdateFailed(f"Error reading registers: {err}") from err

            for reg in chunk:
                if reg in values:
                    value, unit = values[reg]
                    data[reg] = {"value": value, "unit": unit}
                else:
                    data[reg] = {"value": None, "unit": None}

        failed = sum(1 for d in data.values() if d["value"] is None)
        if failed == len(self.registers):
            _LOGGER.error("No readings from meter - check IR connection")
        elif failed > 0:
            _LOGGER.debug("Update complete: %d/%d failed", failed, len(self.registers))

        return data

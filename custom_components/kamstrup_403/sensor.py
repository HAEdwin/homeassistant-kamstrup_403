"""Sensor platform for Kamstrup 403."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import KamstrupCoordinator


@dataclass(frozen=True, kw_only=True)
class KamstrupSensorDescription(SensorEntityDescription):
    """Describes a Kamstrup sensor."""

    register: int
    is_date: bool = False


SENSORS: tuple[KamstrupSensorDescription, ...] = (
    # Main sensors
    KamstrupSensorDescription(
        key="heat_energy", register=60, name="Heat Energy (E1)",
        icon="mdi:radiator", device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    KamstrupSensorDescription(
        key="cooling_energy", register=63, name="Cooling Energy (E3)",
        icon="mdi:snowflake", device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="power", register=80, name="Power",
        icon="mdi:flash", device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="temp1", register=86, name="Temp1",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="temp2", register=87, name="Temp2",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="tempdiff", register=89, name="Tempdiff",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="flow", register=74, name="Flow",
        icon="mdi:water", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="volume", register=68, name="Volume",
        icon="mdi:water", state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Monthly min/max
    KamstrupSensorDescription(
        key="minflow_m", register=141, name="MinFlow_M",
        icon="mdi:water", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="maxflow_m", register=139, name="MaxFlow_M",
        icon="mdi:water", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="minpower_m", register=145, name="MinPower_M",
        icon="mdi:flash", device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="maxpower_m", register=143, name="MaxPower_M",
        icon="mdi:flash", device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="avgtemp1_m", register=149, name="AvgTemp1_M",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="avgtemp2_m", register=150, name="AvgTemp2_M",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    # Yearly min/max
    KamstrupSensorDescription(
        key="minflow_y", register=126, name="MinFlow_Y",
        icon="mdi:water", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="maxflow_y", register=124, name="MaxFlow_Y",
        icon="mdi:water", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="minpower_y", register=130, name="MinPower_Y",
        icon="mdi:flash", device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="maxpower_y", register=128, name="MaxPower_Y",
        icon="mdi:flash", device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="avgtemp1_y", register=146, name="AvgTemp1_Y",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="avgtemp2_y", register=147, name="AvgTemp2_Y",
        icon="mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False,
    ),
    # Other
    KamstrupSensorDescription(
        key="temp1xm3", register=97, name="Temp1xm3",
        icon="mdi:thermometer", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="temp2xm3", register=110, name="Temp2xm3",
        icon="mdi:thermometer", state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    KamstrupSensorDescription(
        key="infoevent", register=99, name="Infoevent",
        icon="mdi:eye", state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    KamstrupSensorDescription(
        key="infoevent_counter", register=113, name="Infoevent counter",
        icon="mdi:eye", state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    KamstrupSensorDescription(
        key="serial_number", register=1001, name="Serial number",
        icon="mdi:barcode", state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    KamstrupSensorDescription(
        key="hour_counter", register=1004, name="HourCounter",
        icon="mdi:timer-sand", state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    # Date sensors (monthly)
    KamstrupSensorDescription(
        key="minflowdate_m", register=140, name="MinFlowDate_M",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="maxflowdate_m", register=138, name="MaxFlowDate_M",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="minpowerdate_m", register=144, name="MinPowerDate_M",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="maxpowerdate_m", register=142, name="MaxPowerDate_M",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    # Date sensors (yearly)
    KamstrupSensorDescription(
        key="minflowdate_y", register=125, name="MinFlowDate_Y",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="maxflowdate_y", register=123, name="MaxFlowDate_Y",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="minpowerdate_y", register=129, name="MinPowerDate_Y",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
    KamstrupSensorDescription(
        key="maxpowerdate_y", register=127, name="MaxPowerDate_Y",
        icon="mdi:calendar", device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False, is_date=True,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kamstrup sensors."""
    coordinator: KamstrupCoordinator = entry.runtime_data
    port = entry.data[CONF_PORT]

    entities: list[SensorEntity] = [
        KamstrupSensor(coordinator, entry.entry_id, port, desc)
        for desc in SENSORS
    ]
    # Add gas conversion sensor (depends on register 60)
    entities.append(KamstrupGasSensor(coordinator, entry.entry_id, port))

    async_add_entities(entities)


class KamstrupSensor(CoordinatorEntity[KamstrupCoordinator], SensorEntity):
    """Kamstrup sensor entity."""

    entity_description: KamstrupSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KamstrupCoordinator,
        entry_id: str,
        port: str,
        description: KamstrupSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.register}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, port)},
            manufacturer=MANUFACTURER,
            name="Kamstrup 403",
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Register this sensor's command when added to hass."""
        await super().async_added_to_hass()
        self.coordinator.register_command(self.entity_description.register)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister this sensor's command when removed from hass."""
        self.coordinator.unregister_command(self.entity_description.register)
        await super().async_will_remove_from_hass()

    @property
    def _register_data(self) -> dict[str, Any] | None:
        """Get data for this sensor's register."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.register)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        data = self._register_data
        return data is not None and data.get("value") is not None

    @property
    def native_value(self) -> float | datetime | None:
        """Return sensor value."""
        data = self._register_data
        if not data:
            return None
        value = data.get("value")
        if value is None:
            return None
        if self.entity_description.is_date:
            # Convert yymmdd float to datetime
            try:
                return datetime.strptime(str(int(value)), "%y%m%d").replace(
                    tzinfo=dt_util.get_default_time_zone()
                )
            except ValueError:
                return None
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit from meter (dynamic)."""
        if self.entity_description.is_date:
            return None
        data = self._register_data
        return data.get("unit") if data else None


# Register ID for Heat Energy (used by gas sensor)
HEAT_ENERGY_REGISTER = 60


class KamstrupGasSensor(CoordinatorEntity[KamstrupCoordinator], SensorEntity):
    """Kamstrup gas conversion sensor (heat energy to gas m3)."""

    _attr_has_entity_name = True
    _attr_name = "Heat Energy to Gas"
    _attr_icon = "mdi:gas-burner"
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: KamstrupCoordinator, entry_id: str, port: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_gas"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, port)},
            manufacturer=MANUFACTURER,
            name="Kamstrup 403",
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Register the heat energy command when added to hass."""
        await super().async_added_to_hass()
        self.coordinator.register_command(HEAT_ENERGY_REGISTER)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the heat energy command when removed from hass."""
        self.coordinator.unregister_command(HEAT_ENERGY_REGISTER)
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self.coordinator.data:
            data = self.coordinator.data.get(HEAT_ENERGY_REGISTER)
            return data is not None and data.get("value") is not None
        return False

    @property
    def native_value(self) -> float | None:
        """Return gas equivalent of heat energy."""
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get(HEAT_ENERGY_REGISTER)
        if not data:
            return None
        return data.get("value")

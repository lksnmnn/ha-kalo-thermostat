"""Sensor platform for the KALO Thermostat integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KaloCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KALO sensor entities from a config entry."""
    coordinator: KaloCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = []
    for serial, device in coordinator.data.devices.items():
        entities.append(KaloTemperatureSensor(coordinator, serial))
        entities.append(KaloHumiditySensor(coordinator, serial))

    async_add_entities(entities)


class KaloTemperatureSensor(CoordinatorEntity[KaloCoordinator], SensorEntity):
    """Temperature sensor for a KALO thermostat device."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: KaloCoordinator, serial: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"kalo_{serial}_temperature"
        self._attr_name = f"KALO {serial} Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        device = self.coordinator.data.devices.get(self._serial)
        if device is None:
            return None
        return device.get("temperature")

    @property
    def available(self) -> bool:
        """Return True if the device is in the latest data."""
        return (
            super().available
            and self._serial in self.coordinator.data.devices
        )


class KaloHumiditySensor(CoordinatorEntity[KaloCoordinator], SensorEntity):
    """Humidity sensor for a KALO thermostat device."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: KaloCoordinator, serial: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"kalo_{serial}_humidity"
        self._attr_name = f"KALO {serial} Humidity"

    @property
    def native_value(self) -> float | None:
        """Return the humidity."""
        device = self.coordinator.data.devices.get(self._serial)
        if device is None:
            return None
        return device.get("humidity")

    @property
    def available(self) -> bool:
        """Return True if the device is in the latest data."""
        return (
            super().available
            and self._serial in self.coordinator.data.devices
        )

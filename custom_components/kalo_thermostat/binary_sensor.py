"""Binary sensor platform for the KALO Thermostat integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up KALO binary sensor entities from a config entry."""
    coordinator: KaloCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = []
    for room_id in coordinator.data.rooms:
        entities.append(KaloWindowOpenSensor(coordinator, room_id))

    async_add_entities(entities)


class KaloWindowOpenSensor(CoordinatorEntity[KaloCoordinator], BinarySensorEntity):
    """Binary sensor indicating if a window is detected open in a KALO room."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.WINDOW

    def __init__(self, coordinator: KaloCoordinator, room_id: str) -> None:
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_unique_id = f"kalo_{room_id}_window_open"

        room = coordinator.data.rooms[room_id]
        display_name = room.get("displayName", "")
        self._attr_name = f"{display_name} Window" if display_name else "Window"

    @property
    def _room_data(self) -> dict[str, Any]:
        """Get current room data from coordinator."""
        return self.coordinator.data.rooms.get(self._room_id, {})

    @property
    def is_on(self) -> bool | None:
        """Return True if window is detected open."""
        return self._room_data.get("isWindowOpen")



"""Climate platform for the KALO Thermostat integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAX_TEMPERATURE, MIN_TEMPERATURE
from .coordinator import KaloCoordinator, KaloData

_LOGGER = logging.getLogger(__name__)

# Room usage type to fallback name mapping (used when no custom name is set)
ROOM_TYPE_NAMES = {
    "BEDROOM": "Bedroom",
    "LIVING_ROOM": "Living Room",
    "KITCHEN": "Kitchen",
    "BATHROOM": "Bathroom",
    "HALLWAY": "Hallway",
    "CORRIDOR": "Corridor",
    "OFFICE": "Office",
    "DINING_ROOM": "Dining Room",
    "CHILDRENS_ROOM": "Children's Room",
    "GUEST_ROOM": "Guest Room",
    "STORAGE": "Storage",
    "LAUNDRY": "Laundry",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KALO climate entities from a config entry."""
    coordinator: KaloCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        KaloClimateEntity(coordinator, room_id)
        for room_id in coordinator.data.rooms
    ]
    async_add_entities(entities)


class KaloClimateEntity(CoordinatorEntity[KaloCoordinator], ClimateEntity):
    """Representation of a KALO thermostat room."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_min_temp = MIN_TEMPERATURE
    _attr_max_temp = MAX_TEMPERATURE
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: KaloCoordinator, room_id: str) -> None:
        super().__init__(coordinator)
        self._room_id = room_id
        room = coordinator.data.rooms[room_id]
        self._attr_unique_id = f"kalo_{room_id}"

        # Build a friendly name from room type and display name
        usage_type = room.get("usageType", "")
        display_name = room.get("displayName", "")
        friendly_type = ROOM_TYPE_NAMES.get(usage_type, usage_type.replace("_", " ").title())
        if display_name:
            self._attr_name = display_name
        else:
            self._attr_name = friendly_type

    @property
    def _room_data(self) -> dict[str, Any]:
        """Get current room data from coordinator."""
        return self.coordinator.data.rooms.get(self._room_id, {})

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._room_data.get("averageTemperature")

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        return self._room_data.get("averageHumidity")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._room_data.get("maximumTargetTemperature")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        target = self.target_temperature
        if target is not None and target <= MIN_TEMPERATURE:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        status = self._room_data.get("radiatorStatus", "")
        if status in ("WARM", "LEW"):
            return HVACAction.HEATING
        if self.hvac_mode == HVACMode.OFF or status == "OFF":
            return HVACAction.OFF
        return HVACAction.IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.coordinator.api.set_room_temperature(self._room_id, temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.set_room_temperature(
                self._room_id, MIN_TEMPERATURE
            )
        elif hvac_mode == HVACMode.HEAT:
            # When turning on from off, set to a reasonable default
            await self.coordinator.api.set_room_temperature(self._room_id, 20.0)
        await self.coordinator.async_request_refresh()

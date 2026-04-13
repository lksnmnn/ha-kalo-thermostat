"""Switch platform for the KALO Thermostat integration."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KaloCoordinator

_LOGGER = logging.getLogger(__name__)

PROFILE_AWAY = "PROFILE_APP_AWAY"
PROFILE_SCHEDULE = "PROFILE_APP_SCHEDULE"


def _extract_eui(thing_id: str) -> str | None:
    """Extract the device EUI from a thingId like 'io.beyonnex...srt:eui001bc507317dfe2b'."""
    match = re.search(r":eui([0-9a-f]+)$", thing_id)
    return match.group(1) if match else None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KALO switch entities from a config entry."""
    coordinator: KaloCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SwitchEntity] = []

    for room_id in coordinator.data.rooms:
        entities.append(KaloOpenWindowDetectionSwitch(coordinator, room_id))
        entities.append(KaloScheduleSwitch(coordinator, room_id))

    for serial, device in coordinator.data.devices.items():
        eui = _extract_eui(device.get("thingId", ""))
        if eui:
            entities.append(KaloChildLockSwitch(coordinator, serial, eui))

    # One away-mode switch per room group
    for group in coordinator.data.room_groups:
        entities.append(KaloAwayModeSwitch(coordinator, group["id"]))

    async_add_entities(entities)


class KaloOpenWindowDetectionSwitch(
    CoordinatorEntity[KaloCoordinator], SwitchEntity
):
    """Switch to enable/disable open window detection for a KALO room."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:window-open-variant"

    def __init__(self, coordinator: KaloCoordinator, room_id: str) -> None:
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_unique_id = f"kalo_{room_id}_open_window_detection"

        room = coordinator.data.rooms[room_id]
        display_name = room.get("displayName", "")
        self._attr_name = (
            f"{display_name} Open Window Detection"
            if display_name
            else "Open Window Detection"
        )

    @property
    def _room_data(self) -> dict[str, Any]:
        return self.coordinator.data.rooms.get(self._room_id, {})

    @property
    def is_on(self) -> bool | None:
        return self._room_data.get("isWindowOpenDetectionEnabled")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_open_window_detection(self._room_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_open_window_detection(self._room_id, False)
        await self.coordinator.async_request_refresh()


class KaloScheduleSwitch(CoordinatorEntity[KaloCoordinator], SwitchEntity):
    """Switch to enable/disable the heating schedule for a KALO room."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: KaloCoordinator, room_id: str) -> None:
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_unique_id = f"kalo_{room_id}_schedule"

        room = coordinator.data.rooms[room_id]
        display_name = room.get("displayName", "")
        self._attr_name = (
            f"{display_name} Schedule" if display_name else "Schedule"
        )

    @property
    def _room_data(self) -> dict[str, Any]:
        return self.coordinator.data.rooms.get(self._room_id, {})

    @property
    def is_on(self) -> bool | None:
        return self._room_data.get("isScheduleActive")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_schedule_state(self._room_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_schedule_state(self._room_id, False)
        await self.coordinator.async_request_refresh()


class KaloChildLockSwitch(CoordinatorEntity[KaloCoordinator], SwitchEntity):
    """Switch to enable/disable child lock on a KALO thermostat device."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:lock"

    def __init__(
        self, coordinator: KaloCoordinator, serial: str, device_eui: str
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._device_eui = device_eui
        self._attr_unique_id = f"kalo_{serial}_child_lock"
        self._attr_name = f"KALO {serial} Child Lock"

    @property
    def is_on(self) -> bool | None:
        device = self.coordinator.data.devices.get(self._serial)
        if device is None:
            return None
        return device.get("childLock")

    @property
    def available(self) -> bool:
        return (
            super().available and self._serial in self.coordinator.data.devices
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_child_lock(self._device_eui, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_child_lock(self._device_eui, False)
        await self.coordinator.async_request_refresh()


class KaloAwayModeSwitch(CoordinatorEntity[KaloCoordinator], SwitchEntity):
    """Switch to toggle away mode for a KALO room group."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:home-export-outline"

    def __init__(self, coordinator: KaloCoordinator, group_id: str) -> None:
        super().__init__(coordinator)
        self._group_id = group_id
        self._attr_unique_id = f"kalo_{group_id}_away_mode"

        group = next(
            (g for g in coordinator.data.room_groups if g["id"] == group_id),
            {},
        )
        display_name = group.get("displayName", "")
        self._attr_name = (
            f"{display_name} Away Mode" if display_name else "Away Mode"
        )

    @property
    def _group_data(self) -> dict[str, Any]:
        return next(
            (g for g in self.coordinator.data.room_groups if g["id"] == self._group_id),
            {},
        )

    @property
    def is_on(self) -> bool | None:
        profile = self._group_data.get("profile", {})
        return profile.get("name") == PROFILE_AWAY

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_room_group_profile(
            self._group_id, PROFILE_AWAY
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_room_group_profile(
            self._group_id, PROFILE_SCHEDULE
        )
        await self.coordinator.async_request_refresh()

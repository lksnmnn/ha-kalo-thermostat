"""DataUpdateCoordinator for the KALO Thermostat integration."""

from __future__ import annotations

import logging
import random
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BeyonnexApiClient, BeyonnexApiError
from .const import DEFAULT_POLL_INTERVAL, DOMAIN, POLL_JITTER

_LOGGER = logging.getLogger(__name__)


class KaloData:
    """Container for KALO API data."""

    def __init__(
        self,
        rooms: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        room_names: dict[str, str] | None = None,
        room_groups: list[dict[str, Any]] | None = None,
    ) -> None:
        self.devices = {device["serial"]: device for device in devices}
        self.room_groups = room_groups or []

        # Only include rooms that have at least one device assigned
        rooms_with_devices = {d["roomId"] for d in devices if "roomId" in d}
        self.rooms = {
            room["id"]: room
            for room in rooms
            if room["id"] in rooms_with_devices
        }

        # Merge room names from the room-names endpoint into room data
        if room_names:
            for room_id, name in room_names.items():
                if room_id in self.rooms:
                    self.rooms[room_id]["displayName"] = name


class KaloCoordinator(DataUpdateCoordinator[KaloData]):
    """Coordinator that fetches rooms and devices from the Beyonnex API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: BeyonnexApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.api = api

    def _jittered_interval(self) -> timedelta:
        """Return a poll interval with random jitter."""
        jitter = random.uniform(-POLL_JITTER, POLL_JITTER)
        return timedelta(seconds=DEFAULT_POLL_INTERVAL + jitter)

    async def _async_update_data(self) -> KaloData:
        """Fetch data from the API."""
        # Apply jitter for next poll
        self.update_interval = self._jittered_interval()

        try:
            rooms = await self.api.get_rooms()
            devices = await self.api.get_devices()
            room_groups = await self.api.get_room_groups()

            # Fetch room names for each room group
            room_names: dict[str, str] = {}
            for group in room_groups:
                group_id = group.get("id")
                if group_id:
                    try:
                        names = await self.api.get_room_names(group_id)
                        if names:
                            room_names.update(names)
                    except Exception:
                        _LOGGER.debug(
                            "Failed to fetch room names for group %s", group_id
                        )
        except BeyonnexApiError as err:
            raise UpdateFailed(f"Error fetching KALO data: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        return KaloData(
            rooms=rooms,
            devices=devices,
            room_names=room_names,
            room_groups=room_groups,
        )

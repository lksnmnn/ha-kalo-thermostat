"""API client for the KALO / Beyonnex Homer API."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp
from pycognito.aws_srp import AWSSRP

from .const import (
    API_BASE_URL,
    API_DEVICE_CHILD_LOCK_ENDPOINT,
    API_DEVICES_ENDPOINT,
    API_ROOM_GROUP_PROFILE_ENDPOINT,
    API_ROOM_GROUPS_ENDPOINT,
    API_ROOM_NAMES_ENDPOINT,
    API_ROOM_OPEN_WINDOW_ENDPOINT,
    API_ROOM_TEMPERATURE_ENDPOINT,
    API_ROOMS_ENDPOINT,
    API_SCHEDULER_STATE_ENDPOINT,
    COGNITO_CLIENT_ID,
    COGNITO_REGION,
    COGNITO_USER_POOL_ID,
)

_LOGGER = logging.getLogger(__name__)

# Refresh tokens 30 seconds before expiry to avoid race conditions
TOKEN_REFRESH_BUFFER = 30


class BeyonnexApiError(Exception):
    """Base exception for Beyonnex API errors."""


class BeyonnexAuthError(BeyonnexApiError):
    """Authentication failed."""


class BeyonnexApiClient:
    """Client for the Beyonnex Homer API with AWS Cognito authentication."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expiry: float = 0

    @property
    def refresh_token(self) -> str | None:
        """Return the current refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        """Set the refresh token (e.g. from stored config)."""
        self._refresh_token = value

    async def authenticate(self) -> dict[str, str]:
        """Perform full SRP authentication and return tokens."""
        try:
            def _do_auth():
                import boto3

                client = boto3.client(
                    "cognito-idp",
                    region_name=COGNITO_REGION,
                    aws_access_key_id="",
                    aws_secret_access_key="",
                )
                aws_srp = AWSSRP(
                    username=self._email,
                    password=self._password,
                    pool_id=COGNITO_USER_POOL_ID,
                    client_id=COGNITO_CLIENT_ID,
                    client=client,
                )
                return aws_srp.authenticate_user()

            tokens = await asyncio.get_event_loop().run_in_executor(
                None, _do_auth
            )
        except Exception as err:
            raise BeyonnexAuthError(f"Authentication failed: {err}") from err

        auth_result = tokens.get("AuthenticationResult", {})
        self._access_token = auth_result.get("AccessToken")
        self._refresh_token = auth_result.get("RefreshToken", self._refresh_token)
        expires_in = auth_result.get("ExpiresIn", 300)
        self._token_expiry = time.time() + expires_in - TOKEN_REFRESH_BUFFER

        return auth_result

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            await self.authenticate()
            return

        try:
            def _do_refresh():
                import boto3

                client = boto3.client(
                    "cognito-idp",
                    region_name=COGNITO_REGION,
                    aws_access_key_id="",
                    aws_secret_access_key="",
                )
                return client.initiate_auth(
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    ClientId=COGNITO_CLIENT_ID,
                    AuthParameters={
                        "REFRESH_TOKEN": self._refresh_token,
                    },
                )

            response = await asyncio.get_event_loop().run_in_executor(
                None, _do_refresh
            )
            auth_result = response.get("AuthenticationResult", {})
            self._access_token = auth_result.get("AccessToken")
            expires_in = auth_result.get("ExpiresIn", 300)
            self._token_expiry = time.time() + expires_in - TOKEN_REFRESH_BUFFER
        except Exception:
            _LOGGER.debug("Token refresh failed, performing full authentication")
            await self.authenticate()

    async def _ensure_token(self) -> None:
        """Ensure we have a valid access token."""
        if not self._access_token or time.time() >= self._token_expiry:
            if self._refresh_token:
                await self._refresh_access_token()
            else:
                await self.authenticate()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Any = None,
        raw_data: Any = None,
    ) -> Any:
        """Make an authenticated API request."""
        await self._ensure_token()

        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        kwargs: dict[str, Any] = {"headers": headers}
        if json_data is not None:
            kwargs["json"] = json_data
        elif raw_data is not None:
            kwargs["data"] = str(raw_data)

        async with self._session.request(method, url, **kwargs) as resp:
            if resp.status == 401:
                # Token might have expired server-side, retry once
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self._access_token}"
                async with self._session.request(method, url, **kwargs) as retry_resp:
                    retry_resp.raise_for_status()
                    if retry_resp.content_length and retry_resp.content_length > 0:
                        return await retry_resp.json()
                    return None

            if resp.status == 204:
                return None

            resp.raise_for_status()
            text = await resp.text()
            if not text or text.strip() == "":
                return None
            # Some endpoints return bare values (e.g. "1")
            try:
                return await resp.json()
            except aiohttp.ContentTypeError:
                return text.strip()

    async def get_room_groups(self) -> list[dict[str, Any]]:
        """Get all room groups (apartments/homes)."""
        return await self._request("GET", API_ROOM_GROUPS_ENDPOINT)

    async def get_rooms(self) -> list[dict[str, Any]]:
        """Get all rooms with current state and schedules."""
        return await self._request("GET", API_ROOMS_ENDPOINT)

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get all thermostat devices with current readings."""
        return await self._request("GET", API_DEVICES_ENDPOINT)

    async def set_room_temperature(self, room_id: str, temperature: float) -> Any:
        """Set the target temperature for a room."""
        endpoint = API_ROOM_TEMPERATURE_ENDPOINT.format(room_id=room_id)
        return await self._request("PUT", endpoint, raw_data=temperature)

    async def set_open_window_detection(
        self, room_id: str, enabled: bool
    ) -> None:
        """Enable or disable open window detection for a room."""
        endpoint = API_ROOM_OPEN_WINDOW_ENDPOINT.format(room_id=room_id)
        await self._request("PUT", endpoint, raw_data=str(enabled).lower())

    async def get_room_names(self, group_id: str) -> dict[str, str]:
        """Get room name mapping for a room group."""
        endpoint = API_ROOM_NAMES_ENDPOINT.format(group_id=group_id)
        return await self._request("GET", endpoint)

    async def set_schedule_state(self, room_id: str, enabled: bool) -> None:
        """Enable or disable the schedule for a room."""
        endpoint = API_SCHEDULER_STATE_ENDPOINT.format(room_id=room_id)
        await self._request("POST", endpoint, raw_data=str(enabled).lower())

    async def set_child_lock(self, device_eui: str, enabled: bool) -> None:
        """Enable or disable child lock on a device."""
        endpoint = API_DEVICE_CHILD_LOCK_ENDPOINT.format(device_eui=device_eui)
        await self._request("PUT", endpoint, raw_data=str(enabled).lower())

    async def set_room_group_profile(self, group_id: str, profile: str) -> None:
        """Set the profile for a room group (e.g. PROFILE_APP_AWAY, PROFILE_APP_SCHEDULE)."""
        endpoint = API_ROOM_GROUP_PROFILE_ENDPOINT.format(group_id=group_id)
        await self._request("PUT", endpoint, json_data={"name": profile})

    async def close(self) -> None:
        """Close the API session."""
        if self._session and not self._session.closed:
            await self._session.close()

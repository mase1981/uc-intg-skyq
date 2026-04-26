"""
SkyQ device implementation using PollingDevice.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import (
    SKYQ_CONNECT_RETRIES,
    SKYQ_CONNECT_RETRY_DELAY,
    SKYQ_POLL_INTERVAL,
)

_LOG = logging.getLogger(__name__)


class SkyQDevice(PollingDevice):
    """SkyQ satellite box managed via HTTP polling."""

    def __init__(self, device_config: SkyQDeviceConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=SKYQ_POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: SkyQClient | None = None

        self._state: str = "UNAVAILABLE"
        self._media_title: str = ""
        self._media_image_url: str = ""

        self._model: str = "SkyQ"
        self._device_name: str = device_config.name
        self._ip_address: str = device_config.host
        self._current_channel: str = ""
        self._connection_type: str = "not connected"

    # -- PollingDevice interface -----------------------------------------------

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address})"

    async def establish_connection(self) -> SkyQClient:
        last_err: Exception | None = None

        for attempt in range(SKYQ_CONNECT_RETRIES):
            self._client = SkyQClient(
                self._device_config.host,
                self._device_config.rest_port,
                self._device_config.remote_port,
            )

            if await self._client.test_connection():
                break

            self._client = None
            last_err = ConnectionError(f"Cannot reach SkyQ device at {self._device_config.host}")

            if attempt < SKYQ_CONNECT_RETRIES - 1:
                _LOG.info(
                    "[%s] Connection attempt %d/%d failed, retrying in %ds",
                    self.log_id, attempt + 1, SKYQ_CONNECT_RETRIES, SKYQ_CONNECT_RETRY_DELAY,
                )
                await asyncio.sleep(SKYQ_CONNECT_RETRY_DELAY)
        else:
            raise last_err  # type: ignore[misc]

        self._connection_type = self._client.connection_type

        await self._fetch_device_info()
        try:
            await self._update_player_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial state query failed, continuing with defaults", self.log_id)

        self._state = "ON"
        _LOG.info("[%s] Connected via %s", self.log_id, self._connection_type)
        return self._client

    async def poll_device(self) -> None:
        if not self._client:
            return
        try:
            await self._update_player_state()
            self.push_update()
        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None
        self._state = "UNAVAILABLE"
        await super().disconnect()

    # -- State properties ------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    @property
    def media_title(self) -> str:
        return self._media_title

    @property
    def media_image_url(self) -> str:
        return self._media_image_url

    @property
    def model(self) -> str:
        return self._model

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def current_channel(self) -> str:
        return self._current_channel

    @property
    def connection_type(self) -> str:
        return self._connection_type

    # -- Commands --------------------------------------------------------------

    async def cmd_power_on(self) -> bool:
        if not self._client:
            return False
        is_standby = await self._client.get_power_status()
        if is_standby is True:
            result = await self._client.send_remote_command("power")
            if result:
                self._state = "ON"
                await asyncio.sleep(6)
                await self._update_player_state()
                self.push_update()
            return result
        if is_standby is False:
            self._state = "ON"
            self.push_update()
            return True
        return await self._client.send_remote_command("power")

    async def cmd_power_off(self) -> bool:
        if not self._client:
            return False
        is_standby = await self._client.get_power_status()
        if is_standby is False:
            result = await self._client.send_remote_command("power")
            if result:
                self._state = "OFF"
                self._media_title = ""
                self._media_image_url = ""
                self.push_update()
            return result
        if is_standby is True:
            self._state = "OFF"
            self.push_update()
            return True
        return await self._client.send_remote_command("power")

    async def cmd_power_toggle(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("power")

    async def cmd_play_pause(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("play")

    async def cmd_stop(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("stop")

    async def cmd_next(self) -> bool:
        if not self._client:
            return False
        result = await self._client.send_remote_command("channelup")
        if result:
            await asyncio.sleep(2)
            await self._update_player_state()
            self.push_update()
        return result

    async def cmd_previous(self) -> bool:
        if not self._client:
            return False
        result = await self._client.send_remote_command("channeldown")
        if result:
            await asyncio.sleep(2)
            await self._update_player_state()
            self.push_update()
        return result

    async def cmd_fast_forward(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("fastforward")

    async def cmd_rewind(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("rewind")

    async def cmd_volume_up(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("volumeup")

    async def cmd_volume_down(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("volumedown")

    async def cmd_mute_toggle(self) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command("mute")

    async def cmd_send(self, command: str) -> bool:
        if not self._client:
            return False
        return await self._client.send_remote_command(command)

    async def cmd_send_sequence(self, sequence: list[str], delay: float = 0.1) -> bool:
        if not self._client:
            return False
        return await self._client.send_key_sequence(sequence, delay)

    async def cmd_play_recording(self, pvrid: str) -> bool:
        if not self._client:
            return False
        return await self._client.play_recording(pvrid)

    async def cmd_change_channel(self, channel: str) -> bool:
        if not self._client:
            return False
        result = await self._client.change_channel(channel)
        if result:
            await asyncio.sleep(2)
            await self._update_player_state()
            self.push_update()
        return result

    # -- Browsable content -----------------------------------------------------

    async def get_channel_list(self) -> list:
        if not self._client:
            return []
        return await self._client.get_channel_list()

    async def get_favourite_list(self) -> list:
        if not self._client:
            return []
        return await self._client.get_favourite_list()

    async def get_recordings(self) -> list:
        if not self._client:
            return []
        return await self._client.get_recordings()

    # -- Internal methods ------------------------------------------------------

    async def _fetch_device_info(self) -> None:
        if not self._client:
            return
        info = await self._client.get_system_information()
        if not info:
            return
        if isinstance(info, dict):
            model = info.get("modelName") or info.get("hardwareModel", "SkyQ")
            device_name = info.get("deviceName", "")
            self._ip_address = self._device_config.host
        else:
            model = getattr(info, "modelName", None) or getattr(info, "hardwareModel", "SkyQ")
            device_name = getattr(info, "deviceName", "")
        self._model = model or "SkyQ"
        if device_name and device_name.strip():
            self._device_name = device_name.strip()

    async def _update_player_state(self) -> None:
        if not self._client:
            raise ConnectionError("No client")

        is_standby = await self._client.get_power_status()
        if is_standby is None:
            raise ConnectionError("Cannot reach device")

        if is_standby:
            self._state = "OFF"
            self._media_title = ""
            self._media_image_url = ""
            self._current_channel = ""
            return

        self._state = "PLAYING"

        program = await self._client.get_current_program()
        if program:
            self._media_title = program.get("title", "Live TV") or "Live TV"
            self._media_image_url = program.get("image_url", "") or ""
            self._current_channel = program.get("channel", "") or ""
        else:
            self._media_title = "Live TV"
            self._media_image_url = ""

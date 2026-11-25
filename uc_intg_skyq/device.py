"""
SkyQ device implementation using PollingDevice.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import time
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import (
    DeviceState,
    SKYQ_CONNECT_RETRIES,
    SKYQ_CONNECT_RETRY_DELAY,
    SKYQ_FAVOURITES_REFRESH,
    SKYQ_FAVOURITES_RETRY,
    SKYQ_POLL_FAILURE_THRESHOLD,
    SKYQ_POLL_INTERVAL,
    SKYQ_RECONNECT_POLL_INTERVAL,
)

_LOG = logging.getLogger(__name__)


def _format_uptime(seconds: object) -> str:
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return ""
    if total <= 0:
        return ""
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


class SkyQDevice(PollingDevice):
    """SkyQ satellite box managed via HTTP polling."""

    def __init__(self, device_config: SkyQDeviceConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=SKYQ_POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: SkyQClient | None = None

        self._state: DeviceState = DeviceState.UNAVAILABLE
        self._media_title: str = ""
        self._media_image_url: str = ""

        self._model: str = "SkyQ"
        self._device_name: str = device_config.name
        self._ip_address: str = device_config.host
        self._current_channel: str = ""
        self._connection_type: str = "not connected"
        self._serial_number: str = ""
        self._software_version: str = ""
        self._hdr_capable: str = ""
        self._uhd_capable: str = ""
        self._system_uptime: str = ""
        self._media_kind: str = ""
        self._favourites: list[tuple[str, str]] = []
        self._favourites_loaded_at: float = 0.0
        self._favourites_next_try: float = 0.0
        self._favourites_task: asyncio.Task | None = None
        self._background_tasks: set[asyncio.Task] = set()

        self._connect_lock = asyncio.Lock()
        self._client_lock = asyncio.Lock()
        self._running = False
        self._poll_failures = 0

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

    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def establish_connection(self) -> SkyQClient | None:
        """Never raises: a failed first connect is retried from poll_device()."""
        self._running = True
        self._poll_failures = 0
        self._poll_interval = SKYQ_POLL_INTERVAL

        for attempt in range(SKYQ_CONNECT_RETRIES):
            if await self._reconnect(quiet=True):
                return self._client
            if attempt < SKYQ_CONNECT_RETRIES - 1:
                await asyncio.sleep(SKYQ_CONNECT_RETRY_DELAY)

        _LOG.warning(
            "[%s] Cannot reach SkyQ device, will keep retrying in the background", self.log_id
        )
        self._poll_interval = SKYQ_RECONNECT_POLL_INTERVAL
        self.push_update()
        return None

    async def poll_device(self) -> None:
        if not self._running:
            return

        if self._client is None or self._state == DeviceState.UNAVAILABLE:
            if await self._reconnect(quiet=True):
                self.push_update()
            return

        try:
            await self._update_player_state()
        except Exception as err:
            self._poll_failures += 1
            _LOG.debug(
                "[%s] Poll error (%d/%d): %s",
                self.log_id, self._poll_failures, SKYQ_POLL_FAILURE_THRESHOLD, err,
            )
            if self._poll_failures >= SKYQ_POLL_FAILURE_THRESHOLD:
                self._mark_unavailable()
            return

        self._poll_failures = 0
        self.push_update()
        self._maybe_refresh_favourites()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            self._running = False
            for task in list(self._background_tasks):
                task.cancel()
            self._background_tasks.clear()
            if self._favourites_task:
                self._favourites_task.cancel()
                self._favourites_task = None
            async with self._client_lock:
                if self._client:
                    await self._client.disconnect()
                    self._client = None
            self._state = DeviceState.UNAVAILABLE
            await super().disconnect()

    # -- Connection recovery ---------------------------------------------------

    async def _reconnect(self, quiet: bool = False) -> SkyQClient | None:
        """Single reachability attempt; reuses the one client for the device lifetime."""
        async with self._client_lock:
            if not self._running:
                return None
            if self._client is not None and self._state != DeviceState.UNAVAILABLE:
                return self._client
            if self._client is None:
                self._client = SkyQClient(
                    self._device_config.host,
                    self._device_config.rest_port,
                    self._device_config.remote_port,
                )

            if not await self._client.test_connection(quiet=quiet):
                return None

            if await self._client.get_power_status() is None:
                _LOG.debug("[%s] Power status query failed after connect", self.log_id)
                return None

            was_unavailable = self._state == DeviceState.UNAVAILABLE
            self._connection_type = self._client.connection_type
            await self._fetch_device_info()
            try:
                await self._update_player_state()
            except ConnectionError:
                _LOG.debug("[%s] State query failed after connect", self.log_id)
                self._state = DeviceState.UNAVAILABLE
                return None
            self._poll_failures = 0
            self._poll_interval = SKYQ_POLL_INTERVAL
            self._favourites_loaded_at = 0.0
            self._favourites_next_try = 0.0
            if was_unavailable:
                _LOG.info("[%s] Connected via %s", self.log_id, self._connection_type)
            return self._client

    def _mark_unavailable(self) -> None:
        if self._state == DeviceState.UNAVAILABLE:
            return
        _LOG.warning("[%s] Connection lost, retrying", self.log_id)
        self._state = DeviceState.UNAVAILABLE
        self._poll_interval = SKYQ_RECONNECT_POLL_INTERVAL
        self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _get_client(self) -> SkyQClient | None:
        """Client for a command; one quick reconnect when the link is down."""
        if self._client is not None and self._state != DeviceState.UNAVAILABLE:
            return self._client
        client = await self._reconnect()
        if client is not None:
            self.push_update()
        return client

    # -- State properties ------------------------------------------------------

    @property
    def state(self) -> DeviceState:
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

    @property
    def serial_number(self) -> str:
        return self._serial_number

    @property
    def software_version(self) -> str:
        return self._software_version

    @property
    def hdr_capable(self) -> str:
        return self._hdr_capable

    @property
    def uhd_capable(self) -> str:
        return self._uhd_capable

    @property
    def system_uptime(self) -> str:
        return self._system_uptime

    @property
    def media_kind(self) -> str:
        return self._media_kind

    @property
    def favourites(self) -> list[tuple[str, str]]:
        return list(self._favourites)

    # -- Commands --------------------------------------------------------------

    async def cmd_power_on(self) -> bool:
        client = await self._get_client()
        if not client:
            return False
        is_standby = await client.get_power_status()
        if is_standby is True:
            result = await client.send_remote_command("power")
            if result:
                self._state = DeviceState.ON
                await asyncio.sleep(6)
                await self._update_player_state()
                self.push_update()
            return result
        if is_standby is False:
            self._state = DeviceState.ON
            self.push_update()
            return True
        return await client.send_remote_command("power")

    async def cmd_power_off(self) -> bool:
        client = await self._get_client()
        if not client:
            return False
        is_standby = await client.get_power_status()
        if is_standby is False:
            result = await client.send_remote_command("power")
            if result:
                self._state = DeviceState.OFF
                self._media_title = ""
                self._media_image_url = ""
                self.push_update()
            return result
        if is_standby is True:
            self._state = DeviceState.OFF
            self.push_update()
            return True
        return await client.send_remote_command("power")

    async def cmd_power_toggle(self) -> bool:
        return await self.cmd_send("power")

    async def cmd_play_pause(self) -> bool:
        return await self.cmd_send("play")

    async def cmd_stop(self) -> bool:
        return await self.cmd_send("stop")

    async def cmd_next(self) -> bool:
        result = await self.cmd_send("channelup")
        if result:
            self._schedule_state_refresh(2)
        return result

    async def cmd_previous(self) -> bool:
        result = await self.cmd_send("channeldown")
        if result:
            self._schedule_state_refresh(2)
        return result

    async def cmd_fast_forward(self) -> bool:
        return await self.cmd_send("fastforward")

    async def cmd_rewind(self) -> bool:
        return await self.cmd_send("rewind")

    async def cmd_volume_up(self) -> bool:
        return await self.cmd_send("volumeup")

    async def cmd_volume_down(self) -> bool:
        return await self.cmd_send("volumedown")

    async def cmd_mute_toggle(self) -> bool:
        return await self.cmd_send("mute")

    async def cmd_send(self, command: str) -> bool:
        client = await self._get_client()
        if not client:
            return False
        return await client.send_remote_command(command)

    async def cmd_send_sequence(self, sequence: list[str], delay: float = 0.1) -> bool:
        client = await self._get_client()
        if not client:
            return False
        return await client.send_key_sequence(sequence, delay)

    async def cmd_play_recording(self, pvrid: str) -> bool:
        client = await self._get_client()
        if not client:
            return False
        return await client.play_recording(pvrid)

    async def cmd_change_channel(self, channel: str) -> bool:
        client = await self._get_client()
        if not client:
            return False
        result = await client.change_channel(channel)
        if result:
            self._schedule_state_refresh(2)
        return result

    def _schedule_state_refresh(self, delay: float) -> None:
        task = asyncio.create_task(self._refresh_state_after(delay))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _refresh_state_after(self, delay: float) -> None:
        await asyncio.sleep(delay)
        try:
            await self._update_player_state()
            self.push_update()
        except Exception as err:
            _LOG.debug("[%s] Post-change state refresh failed: %s", self.log_id, err)

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

    # -- Favourites cache ------------------------------------------------------

    def _maybe_refresh_favourites(self) -> None:
        now = time.monotonic()
        if self._favourites_task and not self._favourites_task.done():
            return
        if now < self._favourites_next_try:
            return
        if self._favourites_loaded_at and now - self._favourites_loaded_at < SKYQ_FAVOURITES_REFRESH:
            return
        self._favourites_task = asyncio.create_task(self._refresh_favourites())

    async def _refresh_favourites(self) -> None:
        try:
            raw = await self.get_favourite_list()
        except Exception as err:
            _LOG.debug("[%s] Favourites refresh failed: %s", self.log_id, err)
            raw = []

        favourites: list[tuple[str, str]] = []
        seen: set[str] = set()
        for fav in raw:
            number = str(getattr(fav, "channelno", "") or getattr(fav, "lcn", "") or "")
            name = str(getattr(fav, "channelname", "") or "")
            if not number.isdigit() or number in seen:
                continue
            seen.add(number)
            favourites.append((number, name or f"Channel {number}"))

        now = time.monotonic()
        if not favourites:
            self._favourites_next_try = now + SKYQ_FAVOURITES_RETRY
            return
        self._favourites_loaded_at = now
        if favourites != self._favourites:
            self._favourites = favourites
            self.push_update()

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
            self._serial_number = str(info.get("serialNumber", "") or "")
            self._software_version = str(info.get("ASVersion", "") or "")
            self._hdr_capable = str(info.get("hdrCapable", "") or "")
            self._uhd_capable = str(info.get("uhdCapable", "") or "")
            self._system_uptime = _format_uptime(info.get("systemUptime"))
        else:
            model = getattr(info, "modelName", None) or getattr(info, "hardwareModel", "SkyQ")
            device_name = getattr(info, "deviceName", "")
            self._serial_number = str(getattr(info, "serialNumber", "") or "")
            self._software_version = str(getattr(info, "ASVersion", "") or "")
            self._hdr_capable = str(getattr(info, "hdrCapable", "") or "")
            self._uhd_capable = str(getattr(info, "uhdCapable", "") or "")
            self._system_uptime = _format_uptime(getattr(info, "systemUptime", None))
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
            self._state = DeviceState.OFF
            self._media_title = ""
            self._media_image_url = ""
            self._current_channel = ""
            self._media_kind = ""
            return

        self._state = DeviceState.PLAYING

        program = await self._client.get_current_program()
        if program:
            self._media_title = program.get("title", "Live TV") or "Live TV"
            self._media_image_url = program.get("image_url", "") or ""
            self._current_channel = program.get("channel", "") or ""
            self._media_kind = program.get("media_kind", "") or ""
        else:
            self._media_title = "Live TV"
            self._media_image_url = ""
            self._media_kind = ""

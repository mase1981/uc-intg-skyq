"""
SkyQ HTTP and TCP client for API communication.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
from typing import Any

import aiohttp

from uc_intg_skyq.const import SKYQ_API_TIMEOUT, SKYQ_DIGIT_DELAY

_LOG = logging.getLogger(__name__)


class SkyQClient:
    """HTTP + pyskyqremote client for SkyQ devices."""

    def __init__(self, host: str, rest_port: int = 9006, remote_port: int = 49160) -> None:
        self._host = host
        self._rest_port = rest_port
        self._remote_port = remote_port
        self._skyq_remote: Any = None
        self._http_fallback = False

    @property
    def host(self) -> str:
        return self._host

    @property
    def rest_port(self) -> int:
        return self._rest_port

    @property
    def remote_port(self) -> int:
        return self._remote_port

    @property
    def connection_type(self) -> str:
        if self._skyq_remote and self._skyq_remote.device_setup:
            return "pyskyqremote"
        if self._http_fallback:
            return "HTTP fallback"
        return "not connected"

    async def connect(self) -> bool:
        if self._skyq_remote or self._http_fallback:
            return True
        try:
            from pyskyqremote.skyq_remote import SkyQRemote
            self._skyq_remote = await asyncio.get_event_loop().run_in_executor(
                None, SkyQRemote, self._host
            )
            if self._skyq_remote and self._skyq_remote.device_setup:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._skyq_remote.get_device_information
                    )
                    _LOG.info("pyskyqremote connection established")
                    return True
                except Exception as err:
                    _LOG.warning("pyskyqremote verification failed: %s", err)
                    self._skyq_remote = None
                    self._http_fallback = True
                    return True
            else:
                self._skyq_remote = None
                self._http_fallback = True
                return True
        except Exception as err:
            _LOG.info("pyskyqremote unavailable, using HTTP fallback: %s", err)
            self._skyq_remote = None
            self._http_fallback = True
            return True

    async def disconnect(self) -> None:
        self._skyq_remote = None

    async def test_connection(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._rest_port}/as/services"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=SKYQ_API_TIMEOUT)) as resp:
                    if resp.status == 200:
                        await self.connect()
                        return True
                    _LOG.error("HTTP connection failed: %d", resp.status)
                    return False
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOG.error("Connection test failed: %s", err)
            return False

    async def get_system_information(self) -> dict[str, Any] | None:
        if self._skyq_remote and self._skyq_remote.device_setup:
            try:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.get_device_information
                )
            except Exception as err:
                _LOG.warning("pyskyqremote system info failed: %s", err)

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._rest_port}/as/system/information"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=SKYQ_API_TIMEOUT)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as err:
            _LOG.warning("HTTP system info failed: %s", err)

        return {
            "deviceName": f"SkyQ Device ({self._host})",
            "modelName": "SkyQ",
            "serialNumber": f"SIM-{self._host.replace('.', '')}",
            "hardwareModel": "SkyQ",
        }

    async def get_power_status(self) -> bool | None:
        """Return True if device is in standby (OFF), False if active, None if unknown."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._rest_port}/as/system/information"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=SKYQ_API_TIMEOUT)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("activeStandby")
        except Exception as err:
            _LOG.debug("Power status query failed: %s", err)
        return None

    async def get_current_program(self) -> dict[str, Any] | None:
        """Get current EPG program info via pyskyqremote."""
        if not self._skyq_remote or not self._skyq_remote.device_setup:
            return None

        try:
            app = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_active_application
            )
            if not app:
                return None

            app_id = getattr(app, "appId", None)
            app_title = getattr(app, "title", None)

            from uc_intg_skyq.const import APP_EPG
            if app_id != APP_EPG:
                return {"title": app_title or "App", "image_url": None, "channel": None}

            current_media = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_current_media
            )
            if not current_media:
                return {"title": "Live TV", "image_url": None, "channel": None}

            is_live = getattr(current_media, "live", False)
            sid = getattr(current_media, "sid", None)

            if not is_live or not sid:
                return {"title": "Live TV", "image_url": None, "channel": None}

            programme = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_current_live_tv_programme, sid
            )
            if not programme:
                return {"title": "Live TV", "image_url": None, "channel": None}

            channel = getattr(programme, "channelname", None)
            title = getattr(programme, "title", None)
            image_url = getattr(programme, "image_url", None)

            display_title = "Live TV"
            if channel and title:
                display_title = f"{channel}: {title}"
            elif channel:
                display_title = channel
            elif title:
                display_title = title

            return {"title": display_title, "image_url": image_url, "channel": channel}

        except Exception as err:
            _LOG.debug("EPG query failed: %s", err)
            return None

    async def send_remote_command(self, command: str) -> bool:
        if self._skyq_remote and self._skyq_remote.device_setup:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.press, command
                )
                return result if result is not None else True
            except Exception as err:
                _LOG.error("pyskyqremote command '%s' failed: %s", command, err)
                return False

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._remote_port), timeout=5.0
            )
            writer.write(f"{command}\n".encode("utf-8"))
            await writer.drain()
            response = await asyncio.wait_for(reader.read(100), timeout=3.0)
            writer.close()
            await writer.wait_closed()
            return len(response) > 0
        except Exception as err:
            _LOG.error("TCP command '%s' failed: %s", command, err)
            return False

    async def send_key_sequence(self, commands: list[str], delay: float = SKYQ_DIGIT_DELAY) -> bool:
        for command in commands:
            if not await self.send_remote_command(command):
                return False
            if delay > 0:
                await asyncio.sleep(delay)
        return True

    async def change_channel(self, channel_number: str) -> bool:
        digits = list(channel_number)
        if not await self.send_key_sequence(digits, delay=SKYQ_DIGIT_DELAY):
            return False
        await asyncio.sleep(0.3)
        return await self.send_remote_command("select")

    # -- Browsable content -----------------------------------------------------

    async def get_channel_list(self) -> list:
        if not self._skyq_remote or not self._skyq_remote.device_setup:
            return await self._get_channels_http()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_channel_list
            )
            if result and hasattr(result, "channels"):
                return sorted(result.channels, key=lambda c: int(getattr(c, "channelno", 0) or 0))
            return []
        except Exception as err:
            _LOG.debug("get_channel_list failed: %s", err)
            return []

    async def get_favourite_list(self) -> list:
        if not self._skyq_remote or not self._skyq_remote.device_setup:
            return []
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_favourite_list
            )
            if result and hasattr(result, "favourites"):
                return sorted(result.favourites, key=lambda f: int(getattr(f, "channelno", 0) or 0))
            return []
        except Exception as err:
            _LOG.debug("get_favourite_list failed: %s", err)
            return []

    async def get_recordings(self) -> list:
        if not self._skyq_remote or not self._skyq_remote.device_setup:
            return []
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._skyq_remote.get_recordings
            )
            if result and hasattr(result, "recordings"):
                return list(result.recordings)
            return []
        except Exception as err:
            _LOG.debug("get_recordings failed: %s", err)
            return []

    async def _get_channels_http(self) -> list:
        """Fallback: get channels via HTTP /as/services endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._host}:{self._rest_port}/as/services"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=SKYQ_API_TIMEOUT)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        services = data.get("services", [])
                        return [_HttpChannel(s) for s in services if s.get("t") == "1"]
        except Exception as err:
            _LOG.debug("HTTP channel list failed: %s", err)
        return []


class _HttpChannel:
    """Lightweight channel object from HTTP /as/services fallback."""

    def __init__(self, data: dict) -> None:
        self.channelno = data.get("c", "")
        self.channelname = data.get("t", "") or data.get("title", "")
        self.channelimageurl = None
        self.channeltype = ""
        self.sid = data.get("sid", "")

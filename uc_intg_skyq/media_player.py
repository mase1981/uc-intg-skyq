"""
SkyQ Media Player entity.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import media_player, StatusCodes
from ucapi.media_player import BrowseOptions, BrowseResults, SearchOptions, SearchResults
from ucapi_framework import MediaPlayerEntity, MediaPlayerAttributes

from uc_intg_skyq import browser
from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.TOGGLE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.STOP,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.FAST_FORWARD,
    media_player.Features.REWIND,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MUTE,
    media_player.Features.UNMUTE,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.PLAY_MEDIA,
    media_player.Features.BROWSE_MEDIA,
    media_player.Features.SEARCH_MEDIA,
]


class SkyQMediaPlayer(MediaPlayerEntity):
    """Media player entity for SkyQ devices."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"media_player.skyq_{device_config.identifier}"

        super().__init__(
            entity_id,
            device_config.name,
            features=FEATURES,
            attributes={
                media_player.Attributes.STATE: media_player.States.UNAVAILABLE,
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "VIDEO",
            },
            device_class=media_player.DeviceClasses.SET_TOP_BOX,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self.map_entity_states(self._device.state)
        attrs = MediaPlayerAttributes(
            STATE=state,
            MEDIA_TITLE=self._device.media_title,
            MEDIA_IMAGE_URL=self._device.media_image_url,
            MEDIA_TYPE="VIDEO",
        )
        self.update(attrs)

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        return await browser.browse(self._device, options)

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        return await browser.search(self._device, options)

    async def _handle_command(
        self, entity: media_player.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s params=%s", self.id, cmd_id, params)
        try:
            result = await self._dispatch_command(cmd_id, params)
            return StatusCodes.OK if result else StatusCodes.SERVER_ERROR
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch_command(self, cmd_id: str, params: dict[str, Any] | None) -> bool:
        if cmd_id == media_player.Commands.ON:
            return await self._device.cmd_power_on()
        if cmd_id == media_player.Commands.OFF:
            return await self._device.cmd_power_off()
        if cmd_id == media_player.Commands.TOGGLE:
            return await self._device.cmd_power_toggle()
        if cmd_id == media_player.Commands.PLAY_PAUSE:
            return await self._device.cmd_play_pause()
        if cmd_id == media_player.Commands.STOP:
            return await self._device.cmd_stop()
        if cmd_id == media_player.Commands.NEXT:
            return await self._device.cmd_next()
        if cmd_id == media_player.Commands.PREVIOUS:
            return await self._device.cmd_previous()
        if cmd_id == media_player.Commands.FAST_FORWARD:
            return await self._device.cmd_fast_forward()
        if cmd_id == media_player.Commands.REWIND:
            return await self._device.cmd_rewind()
        if cmd_id == media_player.Commands.VOLUME_UP:
            return await self._device.cmd_volume_up()
        if cmd_id == media_player.Commands.VOLUME_DOWN:
            return await self._device.cmd_volume_down()
        if cmd_id == media_player.Commands.MUTE_TOGGLE:
            return await self._device.cmd_mute_toggle()
        if cmd_id == media_player.Commands.MUTE:
            return await self._device.cmd_mute_toggle()
        if cmd_id == media_player.Commands.UNMUTE:
            return await self._device.cmd_mute_toggle()
        if cmd_id == media_player.Commands.PLAY_MEDIA:
            return await self._handle_play_media(params)

        _LOG.warning("[%s] Unhandled command: %s", self.id, cmd_id)
        return False

    async def _handle_play_media(self, params: dict[str, Any] | None) -> bool:
        if not params:
            return False
        media_id = params.get("media_id", "")
        if not media_id:
            return False

        if media_id.startswith("channel_"):
            channel_no = media_id[8:]
            if channel_no.isdigit():
                return await self._device.cmd_change_channel(channel_no)
            return False

        if media_id.startswith("recording_"):
            pvrid = media_id[10:]
            _LOG.info("[%s] Play recording: %s", self.id, pvrid)
            return await self._device.cmd_play_recording(pvrid)

        _LOG.warning("[%s] Unknown media_id: %s", self.id, media_id)
        return False

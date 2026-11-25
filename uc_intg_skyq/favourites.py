"""
SkyQ Favourites select entity.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, select
from ucapi_framework import SelectEntity

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import DeviceState
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQFavouritesSelect(SelectEntity):
    """Select entity that tunes the box to one of its favourite channels."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"select.skyq_{device_config.identifier}.favourites"

        super().__init__(
            entity_id,
            f"{device_config.name} Favourites",
            attributes={
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    def _channels(self) -> dict[str, str]:
        """Map each unique option label to its channel number."""
        return {f"{number} {name}": number for number, name in self._device.favourites}

    def _current_option(self, options: list[str]) -> str:
        channel = self._device.current_channel
        if not channel:
            return ""
        for option in options:
            if option.split(" ", 1)[1] == channel:
                return option
        return ""

    async def sync_state(self) -> None:
        if self._device.state == DeviceState.UNAVAILABLE:
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return
        options = list(self._channels())
        self.update({
            select.Attributes.STATE: select.States.ON,
            select.Attributes.OPTIONS: options,
            select.Attributes.CURRENT_OPTION: self._current_option(options),
        })

    async def _handle_command(
        self, entity: select.Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        channels = self._channels()
        options = list(channels)
        if not options:
            return StatusCodes.NOT_FOUND

        current = self._current_option(options)
        index = options.index(current) if current in options else -1

        if cmd_id == select.Commands.SELECT_OPTION:
            option = (params or {}).get("option", "")
            if option not in channels:
                return StatusCodes.BAD_REQUEST
        elif cmd_id == select.Commands.SELECT_FIRST:
            option = options[0]
        elif cmd_id == select.Commands.SELECT_LAST:
            option = options[-1]
        elif cmd_id == select.Commands.SELECT_NEXT:
            option = options[(index + 1) % len(options)]
        elif cmd_id == select.Commands.SELECT_PREVIOUS:
            option = options[(index - 1) % len(options)]
        else:
            return StatusCodes.NOT_IMPLEMENTED

        _LOG.info("[%s] Tuning favourite: %s", self.id, option)
        if not await self._device.cmd_change_channel(channels[option]):
            return StatusCodes.SERVER_ERROR
        return StatusCodes.OK

"""
SkyQ Remote entity with custom UI pages.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import remote, StatusCodes
from ucapi.ui import (
    Buttons,
    UiPage,
    Size,
    create_btn_mapping,
    create_ui_icon,
    create_ui_text,
)
from ucapi_framework import RemoteEntity

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import SIMPLE_COMMANDS
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)

DIGIT_COMMANDS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}


class SkyQRemote(RemoteEntity):
    """Remote entity for SkyQ devices with custom UI pages."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"remote.skyq_{device_config.identifier}"

        ui_pages = self._build_ui_pages()
        button_mapping = self._build_button_mapping()

        super().__init__(
            entity_id,
            f"{device_config.name} Remote",
            features=[remote.Features.ON_OFF, remote.Features.TOGGLE, remote.Features.SEND_CMD],
            attributes={remote.Attributes.STATE: remote.States.UNKNOWN},
            simple_commands=list(SIMPLE_COMMANDS),
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({remote.Attributes.STATE: remote.States.UNAVAILABLE})
            return
        if self._device.state == "OFF":
            self.update({remote.Attributes.STATE: remote.States.OFF})
            return
        self.update({remote.Attributes.STATE: remote.States.ON})

    async def _handle_command(
        self, entity: remote.Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.debug("[%s] Command: %s params=%s", self.id, cmd_id, params)

        try:
            if cmd_id == remote.Commands.ON:
                result = await self._device.cmd_power_on()
                return StatusCodes.OK if result else StatusCodes.SERVER_ERROR

            if cmd_id == remote.Commands.OFF:
                result = await self._device.cmd_power_off()
                return StatusCodes.OK if result else StatusCodes.SERVER_ERROR

            if cmd_id == remote.Commands.TOGGLE:
                result = await self._device.cmd_power_toggle()
                return StatusCodes.OK if result else StatusCodes.SERVER_ERROR

            if cmd_id == remote.Commands.SEND_CMD:
                command = params.get("command", "") if params else ""
                if not command:
                    return StatusCodes.BAD_REQUEST
                return await self._handle_send_cmd(command)

            if cmd_id == remote.Commands.SEND_CMD_SEQUENCE:
                sequence = params.get("sequence", []) if params else []
                delay_ms = params.get("delay", 100) if params else 100
                repeat = params.get("repeat", 1) if params else 1
                if not sequence:
                    return StatusCodes.BAD_REQUEST
                for _ in range(repeat):
                    if not await self._device.cmd_send_sequence(sequence, delay_ms / 1000.0):
                        return StatusCodes.SERVER_ERROR
                return StatusCodes.OK

            if cmd_id in SIMPLE_COMMANDS:
                return await self._handle_send_cmd(cmd_id)

            _LOG.warning("[%s] Unknown command: %s", self.id, cmd_id)
            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _handle_send_cmd(self, command: str) -> StatusCodes:
        if command in DIGIT_COMMANDS:
            await self._device.cmd_send(command)
            return StatusCodes.OK

        if command.startswith("channel_select:"):
            channel = command.split(":", 1)[1].strip()
            if not channel.isdigit():
                return StatusCodes.BAD_REQUEST
            result = await self._device.cmd_change_channel(channel)
            return StatusCodes.OK if result else StatusCodes.SERVER_ERROR

        result = await self._device.cmd_send(command)
        return StatusCodes.OK if result else StatusCodes.SERVER_ERROR

    # -- UI Pages --------------------------------------------------------------

    @staticmethod
    def _build_ui_pages() -> list[UiPage]:
        pages = []

        # Page 1: Main Control
        main = UiPage("main", "Main Control", grid=Size(4, 6))
        main.add(create_ui_text("POWER", 0, 0, cmd="power"))
        main.add(create_ui_text("Guide", 1, 0, cmd="guide"))
        main.add(create_ui_text("Menu", 2, 0, cmd="services"))
        main.add(create_ui_text("Help", 3, 0, cmd="help"))
        main.add(create_ui_icon("uc:up", 1, 1, cmd="up"))
        main.add(create_ui_icon("uc:left", 0, 2, cmd="left"))
        main.add(create_ui_text("OK", 1, 2, cmd="select"))
        main.add(create_ui_icon("uc:right", 2, 2, cmd="right"))
        main.add(create_ui_text("Back", 3, 2, cmd="back"))
        main.add(create_ui_icon("uc:down", 1, 3, cmd="down"))
        main.add(create_ui_icon("uc:play", 0, 4, cmd="play"))
        main.add(create_ui_text("Pause", 1, 4, cmd="pause"))
        main.add(create_ui_icon("uc:stop", 2, 4, cmd="stop"))
        main.add(create_ui_icon("uc:record", 3, 4, cmd="record"))
        main.add(create_ui_text("CH+", 0, 5, cmd="channelup"))
        main.add(create_ui_text("CH-", 1, 5, cmd="channeldown"))
        main.add(create_ui_text("Home", 2, 5, cmd="home"))
        main.add(create_ui_text("Sky", 3, 5, cmd="sky"))
        pages.append(main)

        # Page 2: Numbers
        nums = UiPage("numbers", "Numbers", grid=Size(4, 6))
        for num, x, y in [
            ("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
            ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
            ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
            ("0", 1, 3),
        ]:
            nums.add(create_ui_text(num, x, y, cmd=num))
        nums.add(create_ui_text("Clear", 3, 0, cmd="back"))
        nums.add(create_ui_text("Enter", 3, 3, cmd="select"))
        nums.add(create_ui_icon("uc:fast-forward", 0, 4, cmd="fastforward"))
        nums.add(create_ui_icon("uc:rewind", 1, 4, cmd="rewind"))
        nums.add(create_ui_text("TV Guide", 2, 4, cmd="tvguide"))
        nums.add(create_ui_text("Vol+", 3, 4, cmd="volumeup"))
        nums.add(create_ui_text("Search", 0, 5, cmd="search"))
        nums.add(create_ui_text("Info", 1, 5, cmd="i"))
        nums.add(create_ui_text("Last", 2, 5, cmd="last"))
        nums.add(create_ui_text("Vol-", 3, 5, cmd="volumedown"))
        pages.append(nums)

        # Page 3: Color Buttons
        colors = UiPage("colors", "Color Buttons", grid=Size(4, 6))
        colors.add(create_ui_text("Home", 0, 0, cmd="home"))
        colors.add(create_ui_text("Search", 2, 0, cmd="search"))
        colors.add(create_ui_text("RED", 0, 1, Size(2, 1), cmd="red"))
        colors.add(create_ui_text("GREEN", 2, 1, Size(2, 1), cmd="green"))
        colors.add(create_ui_text("YELLOW", 0, 3, Size(2, 1), cmd="yellow"))
        colors.add(create_ui_text("BLUE", 2, 3, Size(2, 1), cmd="blue"))
        colors.add(create_ui_text("Services", 0, 5, cmd="services"))
        colors.add(create_ui_text("Text", 2, 5, cmd="text"))
        pages.append(colors)

        # Page 4: Special Functions
        special = UiPage("special", "Special Functions", grid=Size(4, 6))
        special.add(create_ui_text("POWER", 0, 0, cmd="power"))
        special.add(create_ui_text("SKY", 1, 0, cmd="sky"))
        special.add(create_ui_text("ON", 2, 0, cmd="on"))
        special.add(create_ui_text("STANDBY", 3, 0, cmd="standby"))
        special.add(create_ui_text("TV", 0, 1, cmd="tv"))
        special.add(create_ui_text("RADIO", 1, 1, cmd="radio"))
        special.add(create_ui_text("BOX OFFICE", 2, 1, Size(2, 1), cmd="boxoffice"))
        special.add(create_ui_text("MY SKY", 0, 2, cmd="mysky"))
        special.add(create_ui_text("PLANNER", 1, 2, cmd="planner"))
        special.add(create_ui_text("INTERACTIVE", 2, 2, Size(2, 1), cmd="interactive"))
        special.add(create_ui_text("SUBTITLE", 0, 3, cmd="subtitle"))
        special.add(create_ui_text("AUDIO", 1, 3, cmd="audio"))
        special.add(create_ui_text("LIST", 2, 3, cmd="list"))
        special.add(create_ui_text("TOP", 3, 3, cmd="top"))
        special.add(create_ui_text("ANNOUNCE", 0, 4, cmd="announce"))
        special.add(create_ui_text("DISMISS", 1, 4, cmd="dismiss"))
        special.add(create_ui_text("BACKUP", 2, 4, cmd="backup"))
        special.add(create_ui_text("MUTE", 3, 4, cmd="mute"))
        pages.append(special)

        return pages

    @staticmethod
    def _build_button_mapping() -> list:
        return [
            create_btn_mapping(Buttons.POWER, short="power"),
            create_btn_mapping(Buttons.PLAY, short="play"),
            create_btn_mapping(Buttons.PREV, short="channeldown"),
            create_btn_mapping(Buttons.NEXT, short="channelup"),
            create_btn_mapping(Buttons.VOLUME_UP, short="volumeup"),
            create_btn_mapping(Buttons.VOLUME_DOWN, short="volumedown"),
            create_btn_mapping(Buttons.MUTE, short="mute"),
            create_btn_mapping(Buttons.BACK, short="back"),
            create_btn_mapping(Buttons.HOME, short="home"),
            create_btn_mapping(Buttons.CHANNEL_UP, short="channelup"),
            create_btn_mapping(Buttons.CHANNEL_DOWN, short="channeldown"),
            create_btn_mapping(Buttons.DPAD_UP, short="up"),
            create_btn_mapping(Buttons.DPAD_DOWN, short="down"),
            create_btn_mapping(Buttons.DPAD_LEFT, short="left"),
            create_btn_mapping(Buttons.DPAD_RIGHT, short="right"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, short="select"),
        ]

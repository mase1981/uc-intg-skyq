"""
SkyQ Remote entity implementation.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import ucapi.api_definitions as uc
from ucapi.remote import Remote, Attributes, Features, States, Commands
from ucapi.ui import create_btn_mapping, Buttons, create_ui_icon, create_ui_text, UiPage, Size

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQRemote(Remote):
    """Remote Control entity for SkyQ satellite box."""

    def __init__(self, device_config: SkyQDeviceConfig, client: SkyQClient):
        """
        Initialize SkyQ Remote entity.
        
        Args:
            device_config: Device configuration
            client: SkyQ client for API communication
        """
        self.device_config = device_config
        self.client = client

        entity_id = f"skyq_remote_{device_config.device_id}"
        entity_name = f"{device_config.name} Remote"

        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.SEND_CMD
        ]

        attributes = {
            Attributes.STATE: States.UNKNOWN
        }

        simple_commands = [
            "power", "on", "off", "standby",
            "play", "pause", "stop", "record",
            "fast_forward", "rewind",
            "up", "down", "left", "right", "select", "back", "home", "menu",
            "guide", "info",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "red", "green", "yellow", "blue",
            "volume_up", "volume_down", "mute",
            "sky", "search", "text", "help", "services"
        ]

        button_mapping = [
            create_btn_mapping(Buttons.POWER, "power"),
            create_btn_mapping(Buttons.HOME, "home"),
            create_btn_mapping(Buttons.VOLUME_UP, "volume_up"),
            create_btn_mapping(Buttons.VOLUME_DOWN, "volume_down"),
            create_btn_mapping(Buttons.MUTE, "mute"),
            create_btn_mapping(Buttons.DPAD_UP, "up"),
            create_btn_mapping(Buttons.DPAD_DOWN, "down"),
            create_btn_mapping(Buttons.DPAD_LEFT, "left"),
            create_btn_mapping(Buttons.DPAD_RIGHT, "right"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, "select"),
            create_btn_mapping(Buttons.BACK, "back"),
            #create_btn_mapping(Buttons.CHANNEL_UP, "channel_up"),
            create_btn_mapping(Buttons.PLAY, "play"),
            create_btn_mapping(Buttons.NEXT, "fast_forward"),
            create_btn_mapping(Buttons.PREV, "rewind"),
            create_btn_mapping(Buttons.RED, "red"),
            create_btn_mapping(Buttons.GREEN, "green"),
            create_btn_mapping(Buttons.YELLOW, "yellow"),
            create_btn_mapping(Buttons.BLUE, "blue")
        ]

        ui_pages = self._create_ui_pages()

        super().__init__(
            identifier=entity_id,
            name=entity_name,
            features=features,
            attributes=attributes,
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self.command_handler
        )

        self._available = False
        self._connected = False
        self._last_command_time = 0

        self._integration_api = None

        _LOG.debug(f"Initialized SkyQ remote: {entity_id}")

    def _create_ui_pages(self) -> List[UiPage]:
        """Create UI pages for on-screen remote control."""
        pages = []

        main_page = UiPage(
            page_id="main",
            name="Main Control",
            grid=Size(4, 6)
        )

        main_page.add(create_ui_text("POWER", 0, 0, cmd="power"))
        main_page.add(create_ui_text("Guide", 1, 0, cmd="guide"))
        main_page.add(create_ui_text("Menu", 2, 0, cmd="menu"))
        main_page.add(create_ui_text("Info", 3, 0, cmd="info"))

        main_page.add(create_ui_icon("uc:up", 1, 1, cmd="up"))
        main_page.add(create_ui_icon("uc:left", 0, 2, cmd="left"))
        main_page.add(create_ui_text("OK", 1, 2, cmd="select"))
        main_page.add(create_ui_icon("uc:right", 2, 2, cmd="right"))
        main_page.add(create_ui_icon("uc:down", 1, 3, cmd="down"))
        main_page.add(create_ui_text("Back", 3, 2, cmd="back"))

        main_page.add(create_ui_icon("uc:play", 0, 4, cmd="play"))
        main_page.add(create_ui_icon("uc:pause", 1, 4, cmd="pause"))
        main_page.add(create_ui_icon("uc:stop", 2, 4, cmd="stop"))
        main_page.add(create_ui_icon("uc:record", 3, 4, cmd="record"))

        #main_page.add(create_ui_text("CH+", 0, 5, cmd="channel_up"))
        main_page.add(create_ui_text("VOL+", 1, 5, cmd="volume_up"))
        main_page.add(create_ui_text("VOL-", 2, 5, cmd="volume_down"))
        main_page.add(create_ui_text("MUTE", 3, 5, cmd="mute"))

        pages.append(main_page)

        numbers_page = UiPage(
            page_id="numbers",
            name="Numbers",
            grid=Size(4, 6)
        )

        numbers = [
            ("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
            ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
            ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
            ("0", 1, 3)
        ]

        for num, x, y in numbers:
            numbers_page.add(create_ui_text(num, x, y, cmd=num))

        numbers_page.add(create_ui_text("Enter", 3, 3, cmd="select"))
        numbers_page.add(create_ui_text("Clear", 3, 0, cmd="back"))

        numbers_page.add(create_ui_icon("uc:fast-forward", 0, 4, cmd="fast_forward"))
        numbers_page.add(create_ui_icon("uc:rewind", 1, 4, cmd="rewind"))

        pages.append(numbers_page)

        colors_page = UiPage(
            page_id="colors",
            name="Color Buttons",
            grid=Size(4, 6)
        )

        colors_page.add(create_ui_text("RED", 0, 1, Size(2, 1), cmd="red"))
        colors_page.add(create_ui_text("GREEN", 2, 1, Size(2, 1), cmd="green"))
        colors_page.add(create_ui_text("YELLOW", 0, 3, Size(2, 1), cmd="yellow"))
        colors_page.add(create_ui_text("BLUE", 2, 3, Size(2, 1), cmd="blue"))

        colors_page.add(create_ui_text("Home", 0, 0, cmd="home"))
        colors_page.add(create_ui_text("Search", 2, 0, cmd="search"))
        colors_page.add(create_ui_text("Services", 0, 5, cmd="services"))
        colors_page.add(create_ui_text("Text", 2, 5, cmd="text"))

        pages.append(colors_page)

        power_page = UiPage(
            page_id="power",
            name="Power Controls",
            grid=Size(4, 6)
        )

        power_page.add(create_ui_text("POWER\nTOGGLE", 0, 1, Size(2, 2), cmd="power"))
        power_page.add(create_ui_text("POWER\nON", 2, 1, Size(2, 2), cmd="on"))
        power_page.add(create_ui_text("STANDBY", 0, 3, Size(2, 2), cmd="standby"))
        power_page.add(create_ui_text("OFF", 2, 3, Size(2, 2), cmd="off"))

        power_page.add(create_ui_text("Home", 0, 0, cmd="home"))
        power_page.add(create_ui_text("Sky", 2, 0, cmd="sky"))
        power_page.add(create_ui_text("Services", 0, 5, cmd="services"))
        power_page.add(create_ui_text("Help", 2, 5, cmd="help"))

        pages.append(power_page)

        return pages

    async def initialize(self) -> bool:
        """
        Initialize the remote entity.
        
        Returns:
            True if initialization successful
        """
        _LOG.info(f"Initializing SkyQ remote: {self.device_config.name}")

        try:
            if await self.client.test_connection():
                self._available = True
                self._connected = True
                self.attributes[Attributes.STATE] = States.ON

                try:
                    device_info = await self.client.get_system_information()
                    enhanced_name = self._generate_entity_name(device_info)
                    if enhanced_name != self.name:
                        if isinstance(self.name, str):
                            self.name = enhanced_name
                        else:
                            self.name["en"] = enhanced_name
                        _LOG.info(f"Updated remote entity name to: {enhanced_name}")
                except Exception as e:
                    _LOG.warning(f"Could not get device info for remote naming: {e}")

                _LOG.info(f"SkyQ remote initialized successfully: {self.name}")
                return True
            else:
                _LOG.warning(f"Failed to connect to SkyQ device: {self.device_config.name}")
                self._available = False
                self._connected = False
                self.attributes[Attributes.STATE] = States.UNAVAILABLE
                return False

        except Exception as e:
            _LOG.error(f"Failed to initialize SkyQ remote {self.device_config.name}: {e}")
            self._available = False
            self._connected = False
            self.attributes[Attributes.STATE] = States.UNAVAILABLE
            return False

    def _generate_entity_name(self, device_info: Dict[str, Any]) -> str:
        """
        Generate enhanced remote entity name using device information.
        
        Args:
            device_info: Device information from SkyQ API
            
        Returns:
            Enhanced remote entity name
        """
        model = device_info.get("modelName") or device_info.get("hardwareModel", "SkyQ")
        device_name = device_info.get("deviceName", "")
        serial = device_info.get("serialNumber", "")

        base_name = self.device_config.name

        generic_names = ["skyq device", "skyq", "device", f"skyq device ({self.device_config.host})"]
        if base_name.lower() in generic_names or not base_name:
            if device_name and device_name != "SkyQ Device":
                entity_name = f"{device_name} Remote"
            else:
                if serial and not serial.startswith("SIM"):
                    entity_name = f"SkyQ {model} Remote ({serial[-4:]})"
                else:
                    entity_name = f"SkyQ {model} Remote ({self.device_config.host})"
        else:
            if model and model != "SkyQ":
                entity_name = f"{base_name} Remote ({model})"
            else:
                entity_name = f"{base_name} Remote"

        return entity_name

    async def shutdown(self):
        """Shutdown the remote entity."""
        _LOG.info(f"Shutting down SkyQ remote: {self.device_config.name}")

        self._available = False
        self._connected = False
        self.attributes[Attributes.STATE] = States.UNAVAILABLE

        _LOG.debug(f"SkyQ remote shutdown complete: {self.device_config.name}")

    async def update_attributes(self):
        """Update remote attributes - FIXED: Naim pattern."""
        if self._connected and self._available:
            self.attributes[Attributes.STATE] = States.ON
        else:
            self.attributes[Attributes.STATE] = States.UNAVAILABLE

        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.identifier, {Attributes.STATE: self.attributes[Attributes.STATE]}
                )
                _LOG.debug("Updated remote attributes via integration API for %s - State: %s",
                          self.identifier, self.attributes[Attributes.STATE])
            except Exception as e:
                _LOG.debug("Could not update remote via integration API: %s", e)

    async def command_handler(self, entity: Remote, cmd_id: str, params: dict = None) -> uc.StatusCodes:
        """
        Handle commands sent to the remote control.
        
        Args:
            entity: The remote entity
            cmd_id: Command identifier
            params: Command parameters
            
        Returns:
            Status code indicating success/failure
        """
        _LOG.debug(f"SkyQ remote command: {cmd_id} with params: {params}")

        if not self._available:
            _LOG.warning(f"SkyQ device {self.device_config.name} not available for command: {cmd_id}")
            return uc.StatusCodes.SERVICE_UNAVAILABLE

        try:
            import time
            self._last_command_time = time.time()

            if cmd_id == Commands.ON:
                await self.client.power_on()
                self.attributes[Attributes.STATE] = States.ON

            elif cmd_id == Commands.OFF:
                await self.client.power_off()
                self.attributes[Attributes.STATE] = States.OFF

            elif cmd_id == Commands.TOGGLE:
                await self.client.power_toggle()

            elif cmd_id == Commands.SEND_CMD:
                command = params.get("command") if params else None
                if command:
                    await self._send_command(command)
                else:
                    _LOG.warning("SEND_CMD called without command parameter")
                    return uc.StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SEND_CMD_SEQUENCE:
                sequence = params.get("sequence", []) if params else []
                delay = params.get("delay", 0.5) if params else 0.5
                repeat = params.get("repeat", 1) if params else 1

                if sequence:
                    for _ in range(repeat):
                        await self.client.send_key_sequence(sequence, delay)
                else:
                    _LOG.warning("SEND_CMD_SEQUENCE called without sequence parameter")
                    return uc.StatusCodes.BAD_REQUEST

            elif cmd_id in ["power", "on", "off", "standby"]:
                if cmd_id == "on":
                    await self.client.power_on()
                elif cmd_id == "off" or cmd_id == "standby":
                    await self.client.power_off()
                else:
                    await self.client.power_toggle()

            elif cmd_id in ["play", "pause", "stop", "record", "fast_forward", "rewind"]:
                await self._send_command(cmd_id)

            elif cmd_id in ["up", "down", "left", "right", "select", "back", "home"]:
                await self._send_command(cmd_id)

            #elif cmd_id == "channel_up":
                #await self._send_command(cmd_id)

            elif cmd_id in ["volume_up", "volume_down", "mute"]:
                await self._send_command(cmd_id)

            elif cmd_id in ["menu", "guide", "info", "services", "search", "text"]:
                await self._send_command(cmd_id)

            elif cmd_id in ["red", "green", "yellow", "blue"]:
                await self._send_command(cmd_id)

            elif cmd_id in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                await self._send_command(cmd_id)

            else:
                await self._send_command(cmd_id)

            return uc.StatusCodes.OK

        except Exception as e:
            _LOG.error(f"Error executing remote command {cmd_id} on {self.device_config.name}: {e}")
            return uc.StatusCodes.SERVER_ERROR

    async def _send_command(self, command: str):
        """
        Send command to SkyQ device with error handling.
        
        Args:
            command: Command name to send
        """
        success = await self.client.send_remote_command(command)

        if not success:
            _LOG.warning(f"Failed to send remote command: {command}")
            raise Exception(f"Remote command failed: {command}")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information for diagnostics."""
        return {
            "device_id": self.device_config.device_id,
            "name": f"{self.device_config.name} Remote",
            "host": self.device_config.host,
            "available": self._available,
            "connected": self._connected,
            "state": self.attributes.get(Attributes.STATE),
            "last_command_time": self._last_command_time,
            "simple_commands_count": len(self.options.get("simple_commands", [])),
            "ui_pages_count": len(self.options.get("user_interface", {}).get("pages", []))
        }
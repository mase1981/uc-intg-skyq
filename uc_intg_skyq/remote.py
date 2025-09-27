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
from ucapi.ui import create_ui_icon, create_ui_text, UiPage, Size

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQRemote(Remote):

    def __init__(self, device_config: SkyQDeviceConfig, client: SkyQClient):
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
            "power", "standby", "on", "off", "select", "channelup", "channeldown",
            "sky", "help", "services", "search", "home", "up",
            "down", "left", "right", "red", "green", "yellow", "blue", "0", "1",
            "2", "3", "4", "5", "6", "7", "8", "9", "play", "pause", "stop",
            "record", "fastforward", "rewind", "text", "back", "menu",
            "guide", "info", "volumeup", "volumedown", "mute", "tvguide", "i",
            "boxoffice", "dismiss", "backup", "tv", "radio", "interactive",
            "mysky", "planner", "top", "subtitle", "audio", "announce", "last", "list"
        ]

        # No button mapping to avoid invalid constants
        button_mapping = []

        # Create UI pages for remote interface
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
        """Create UI pages for the remote interface."""
        pages = []

        # Main Control Page
        main_page = UiPage(
            page_id="main",
            name="Main Control",
            grid=Size(4, 6)
        )

        # Row 0 - Top controls
        main_page.add(create_ui_text("POWER", 0, 0, cmd="power"))
        main_page.add(create_ui_text("Guide", 1, 0, cmd="guide"))
        main_page.add(create_ui_text("Menu", 2, 0, cmd="services"))
        main_page.add(create_ui_text("Help", 3, 0, cmd="help"))

        # Row 1-3 - Navigation
        main_page.add(create_ui_icon("uc:up", 1, 1, cmd="up"))
        main_page.add(create_ui_icon("uc:left", 0, 2, cmd="left"))
        main_page.add(create_ui_text("OK", 1, 2, cmd="select"))
        main_page.add(create_ui_icon("uc:right", 2, 2, cmd="right"))
        main_page.add(create_ui_icon("uc:down", 1, 3, cmd="down"))
        main_page.add(create_ui_text("Back", 3, 2, cmd="back"))

        # Row 4 - Media controls
        main_page.add(create_ui_icon("uc:play", 0, 4, cmd="play"))
        main_page.add(create_ui_text("Pause", 1, 4, cmd="pause"))
        main_page.add(create_ui_icon("uc:stop", 2, 4, cmd="stop"))
        main_page.add(create_ui_icon("uc:record", 3, 4, cmd="record"))

        # Row 5 - Channel controls
        main_page.add(create_ui_text("CH+", 0, 5, cmd="channelup"))
        main_page.add(create_ui_text("CH-", 1, 5, cmd="channeldown"))
        main_page.add(create_ui_text("Home", 2, 5, cmd="home"))
        main_page.add(create_ui_text("Sky", 3, 5, cmd="sky"))

        pages.append(main_page)

        # Numbers Page
        numbers_page = UiPage(
            page_id="numbers",
            name="Numbers",
            grid=Size(4, 6)
        )

        # Number buttons
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

        # Transport controls
        numbers_page.add(create_ui_icon("uc:fast-forward", 0, 4, cmd="fastforward"))
        numbers_page.add(create_ui_icon("uc:rewind", 1, 4, cmd="rewind"))
        numbers_page.add(create_ui_text("TV Guide", 2, 4, cmd="tvguide"))
        numbers_page.add(create_ui_text("Vol+", 3, 4, cmd="volumeup"))

        numbers_page.add(create_ui_text("Search", 0, 5, cmd="search"))
        numbers_page.add(create_ui_text("Info", 1, 5, cmd="i"))
        numbers_page.add(create_ui_text("Last", 2, 5, cmd="last"))
        numbers_page.add(create_ui_text("Vol-", 3, 5, cmd="volumedown"))

        pages.append(numbers_page)

        # Color Buttons Page
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

        # Special Functions Page
        special_page = UiPage(
            page_id="special",
            name="Special Functions",
            grid=Size(4, 6)
        )

        special_page.add(create_ui_text("POWER", 0, 0, cmd="power"))
        special_page.add(create_ui_text("SKY", 1, 0, cmd="sky"))
        special_page.add(create_ui_text("ON", 2, 0, cmd="on"))
        special_page.add(create_ui_text("STANDBY", 3, 0, cmd="standby"))

        special_page.add(create_ui_text("TV", 0, 1, cmd="tv"))
        special_page.add(create_ui_text("RADIO", 1, 1, cmd="radio"))
        special_page.add(create_ui_text("BOX OFFICE", 2, 1, Size(2, 1), cmd="boxoffice"))

        special_page.add(create_ui_text("MY SKY", 0, 2, cmd="mysky"))
        special_page.add(create_ui_text("PLANNER", 1, 2, cmd="planner"))
        special_page.add(create_ui_text("INTERACTIVE", 2, 2, Size(2, 1), cmd="interactive"))

        special_page.add(create_ui_text("SUBTITLE", 0, 3, cmd="subtitle"))
        special_page.add(create_ui_text("AUDIO", 1, 3, cmd="audio"))
        special_page.add(create_ui_text("LIST", 2, 3, cmd="list"))
        special_page.add(create_ui_text("TOP", 3, 3, cmd="top"))

        special_page.add(create_ui_text("ANNOUNCE", 0, 4, cmd="announce"))
        special_page.add(create_ui_text("DISMISS", 1, 4, cmd="dismiss"))
        special_page.add(create_ui_text("BACKUP", 2, 4, cmd="backup"))
        special_page.add(create_ui_text("MUTE", 3, 4, cmd="mute"))

        pages.append(special_page)

        return pages

    async def initialize(self) -> bool:
        """Initialize the remote entity."""
        _LOG.info(f"Initializing SkyQ remote: {self.device_config.name}")

        try:
            if await self.client.test_connection():
                self._available = True
                self._connected = True
                self.attributes[Attributes.STATE] = States.ON

                try:
                    device_info = await self.client.get_system_information()
                    if device_info:
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
        """Generate enhanced entity name using device information."""
        if isinstance(device_info, dict):
            model = device_info.get("modelName") or device_info.get("hardwareModel", "SkyQ")
            device_name = device_info.get("deviceName", "")
            serial = device_info.get("serialNumber", "")
        else:
            model = getattr(device_info, 'modelName', None) or getattr(device_info, 'hardwareModel', 'SkyQ')
            device_name = getattr(device_info, 'deviceName', '')
            serial = getattr(device_info, 'serialNumber', '')

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

        await self.client.disconnect()
        _LOG.debug(f"SkyQ remote shutdown complete: {self.device_config.name}")

    async def update_attributes(self):
        """Update entity attributes."""
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
        """Handle commands sent to the remote."""
        _LOG.debug(f"SkyQ remote command: {cmd_id} with params: {params}")

        if not self._available:
            _LOG.warning(f"SkyQ device {self.device_config.name} not available for command: {cmd_id}")
            return uc.StatusCodes.SERVICE_UNAVAILABLE

        try:
            import time
            self._last_command_time = time.time()

            if cmd_id == Commands.ON:
                # Note: library's power_status() is inverted. It returns True for STANDBY.
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is True:
                    _LOG.debug("Device is in STANDBY. Sending power toggle to turn ON.")
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.ON
                elif is_in_standby is False:
                    _LOG.debug("Device is already ON. No action taken.")
                    self.attributes[Attributes.STATE] = States.ON
                else:
                    _LOG.warning("Could not determine power state. Sending power toggle as fallback.")
                    await self.client.send_remote_command("power")

            elif cmd_id == Commands.OFF:
                # Note: library's power_status() is inverted. It returns False for ON.
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is False:
                    _LOG.debug("Device is ON. Sending power toggle to go to STANDBY.")
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.OFF
                elif is_in_standby is True:
                    _LOG.debug("Device is already in STANDBY. No action taken.")
                    self.attributes[Attributes.STATE] = States.OFF
                else:
                    _LOG.warning("Could not determine power state. Sending power toggle as fallback.")
                    await self.client.send_remote_command("power")

            elif cmd_id == Commands.TOGGLE:
                success = await self.client.send_remote_command("power")

            elif cmd_id == Commands.SEND_CMD:
                command = params.get("command") if params else None
                if command:
                    success = await self.client.send_remote_command(command)
                    if success:
                        _LOG.info(f"Command '{command}' sent successfully to {self.device_config.name}")
                        return uc.StatusCodes.OK
                    else:
                        _LOG.warning(f"Command '{command}' failed on {self.device_config.name}")
                        return uc.StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning("SEND_CMD called without command parameter")
                    return uc.StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SEND_CMD_SEQUENCE:
                sequence = params.get("sequence", []) if params else []
                delay = params.get("delay", 0.5) if params else 0.5
                repeat = params.get("repeat", 1) if params else 1

                if sequence:
                    for _ in range(repeat):
                        success = await self.client.send_key_sequence(sequence, delay)
                        if not success:
                            return uc.StatusCodes.SERVER_ERROR
                    return uc.StatusCodes.OK
                else:
                    _LOG.warning("SEND_CMD_SEQUENCE called without sequence parameter")
                    return uc.StatusCodes.BAD_REQUEST

            else:
                # Handle any simple command
                if cmd_id in self.options.get("simple_commands", []):
                    success = await self.client.send_remote_command(cmd_id)
                    if success:
                        _LOG.info(f"Simple command '{cmd_id}' sent successfully to {self.device_config.name}")
                        return uc.StatusCodes.OK
                    else:
                        _LOG.warning(f"Simple command '{cmd_id}' failed on {self.device_config.name}")
                        return uc.StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning(f"Unknown command: {cmd_id}")
                    return uc.StatusCodes.NOT_IMPLEMENTED

            return uc.StatusCodes.OK

        except Exception as e:
            _LOG.error(f"Error executing remote command {cmd_id} on {self.device_config.name}: {e}")
            return uc.StatusCodes.SERVER_ERROR

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
            "connection_type": getattr(self.client, 'connection_type', 'unknown'),
            "using_fallback": getattr(self.client, 'is_using_fallback', False),
            "state": self.attributes.get(Attributes.STATE),
            "last_command_time": self._last_command_time,
            "simple_commands_count": len(self.options.get("simple_commands", [])),
            "ui_pages_count": len(self.options.get("user_interface", {}).get("pages", []))
        }
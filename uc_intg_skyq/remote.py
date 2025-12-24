"""SkyQ Remote entity."""
import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Remote, Attributes, Features, Commands, Options, States

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQRemote(Remote):
    """SkyQ Remote entity for comprehensive remote control."""

    def __init__(self, config: SkyQDeviceConfig, device: SkyQDevice):
        """Initialize the remote entity."""
        entity_id = f"remote.{config.identifier}"
        
        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.SEND_CMD
        ]

        # Start with UNAVAILABLE
        attributes = {
            Attributes.STATE: States.UNAVAILABLE
        }

        # Initialize WITHOUT options
        super().__init__(
            identifier=entity_id,
            name=f"{config.name} Remote",
            features=features,
            attributes=attributes,
            cmd_handler=self.handle_command,
        )
        
        self._config = config
        self._device = device

        # Define simple commands
        simple_commands = [
            "power", "standby", "on", "off", "select", "channelup",
            "sky", "help", "services", "search", "home", "up",
            "down", "left", "right", "red", "green", "yellow", "blue", "0", "1",
            "2", "3", "4", "5", "6", "7", "8", "9", "play", "pause", "stop",
            "record", "fastforward", "rewind", "text", "back", "menu",
            "guide", "info", "volumeup", "volumedown", "mute"
        ]

        # Create UI pages
        ui_pages = self._create_ui_pages()
        
        # Set options AFTER initialization
        self.options = {
            Options.SIMPLE_COMMANDS: simple_commands,
            "user_interface": {"pages": ui_pages}
        }
        
        # CRITICAL: Register for device events!
        device.events.on("UPDATE", self._on_device_update)
        
        _LOG.debug("Remote entity created: %s with %d commands and %d pages", 
                   entity_id, len(simple_commands), len(ui_pages))

    async def _on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        """Handle device state updates."""
        # Only process updates for this entity
        if entity_id != self.id:
            return
        
        _LOG.info("[%s] Received update: %s", self.id, update_data)
        
        # Update state
        if "state" in update_data:
            state_str = update_data["state"]
            if state_str == "OFF":
                self.attributes[Attributes.STATE] = States.OFF
            elif state_str == "ON":
                self.attributes[Attributes.STATE] = States.ON
            else:
                self.attributes[Attributes.STATE] = States.UNKNOWN
            
            # CRITICAL: Notify framework of attribute change
            if self.is_configured:
                self.configured_event(self.attributes)
                _LOG.info("[%s] Pushed state update to framework: %s", self.id, state_str)

    def _create_ui_pages(self) -> list[dict]:
        """Create UI pages for the remote interface."""
        pages = []

        # Main Control Page
        main_page = {
            "page_id": "main",
            "name": "Main Control",
            "grid": {"width": 4, "height": 6},
            "items": [
                {"type": "text", "text": "POWER", "command": {"cmd_id": "power"}, "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "Guide", "command": {"cmd_id": "guide"}, "location": {"x": 1, "y": 0}},
                {"type": "text", "text": "Menu", "command": {"cmd_id": "services"}, "location": {"x": 2, "y": 0}},
                {"type": "text", "text": "Help", "command": {"cmd_id": "help"}, "location": {"x": 3, "y": 0}},
                
                {"type": "icon", "icon": "uc:up-arrow", "command": {"cmd_id": "up"}, "location": {"x": 1, "y": 1}},
                {"type": "icon", "icon": "uc:left-arrow", "command": {"cmd_id": "left"}, "location": {"x": 0, "y": 2}},
                {"type": "text", "text": "OK", "command": {"cmd_id": "select"}, "location": {"x": 1, "y": 2}},
                {"type": "icon", "icon": "uc:right-arrow", "command": {"cmd_id": "right"}, "location": {"x": 2, "y": 2}},
                {"type": "icon", "icon": "uc:down-arrow", "command": {"cmd_id": "down"}, "location": {"x": 1, "y": 3}},
                {"type": "text", "text": "Back", "command": {"cmd_id": "back"}, "location": {"x": 3, "y": 2}},
                
                {"type": "icon", "icon": "uc:play", "command": {"cmd_id": "play"}, "location": {"x": 0, "y": 4}},
                {"type": "text", "text": "Pause", "command": {"cmd_id": "pause"}, "location": {"x": 1, "y": 4}},
                {"type": "icon", "icon": "uc:stop", "command": {"cmd_id": "stop"}, "location": {"x": 2, "y": 4}},
                {"type": "icon", "icon": "uc:record", "command": {"cmd_id": "record"}, "location": {"x": 3, "y": 4}},
                
                {"type": "text", "text": "CH+", "command": {"cmd_id": "channelup"}, "location": {"x": 0, "y": 5}},
                {"type": "text", "text": "Home", "command": {"cmd_id": "home"}, "location": {"x": 2, "y": 5}},
                {"type": "text", "text": "Sky", "command": {"cmd_id": "sky"}, "location": {"x": 3, "y": 5}},
            ]
        }
        pages.append(main_page)

        # Numbers Page
        numbers_page = {
            "page_id": "numbers",
            "name": "Numbers",
            "grid": {"width": 4, "height": 6},
            "items": [
                {"type": "text", "text": "1", "command": {"cmd_id": "1"}, "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "2", "command": {"cmd_id": "2"}, "location": {"x": 1, "y": 0}},
                {"type": "text", "text": "3", "command": {"cmd_id": "3"}, "location": {"x": 2, "y": 0}},
                {"type": "text", "text": "4", "command": {"cmd_id": "4"}, "location": {"x": 0, "y": 1}},
                {"type": "text", "text": "5", "command": {"cmd_id": "5"}, "location": {"x": 1, "y": 1}},
                {"type": "text", "text": "6", "command": {"cmd_id": "6"}, "location": {"x": 2, "y": 1}},
                {"type": "text", "text": "7", "command": {"cmd_id": "7"}, "location": {"x": 0, "y": 2}},
                {"type": "text", "text": "8", "command": {"cmd_id": "8"}, "location": {"x": 1, "y": 2}},
                {"type": "text", "text": "9", "command": {"cmd_id": "9"}, "location": {"x": 2, "y": 2}},
                {"type": "text", "text": "0", "command": {"cmd_id": "0"}, "location": {"x": 1, "y": 3}},
                
                {"type": "text", "text": "Enter", "command": {"cmd_id": "select"}, "location": {"x": 3, "y": 3}},
                {"type": "text", "text": "Clear", "command": {"cmd_id": "back"}, "location": {"x": 3, "y": 0}},
                
                {"type": "icon", "icon": "uc:fast-forward", "command": {"cmd_id": "fastforward"}, "location": {"x": 0, "y": 4}},
                {"type": "icon", "icon": "uc:rewind", "command": {"cmd_id": "rewind"}, "location": {"x": 1, "y": 4}},
                {"type": "text", "text": "Info", "command": {"cmd_id": "info"}, "location": {"x": 2, "y": 4}},
                {"type": "text", "text": "Vol+", "command": {"cmd_id": "volumeup"}, "location": {"x": 3, "y": 4}},
                
                {"type": "text", "text": "Search", "command": {"cmd_id": "search"}, "location": {"x": 0, "y": 5}},
                {"type": "text", "text": "Text", "command": {"cmd_id": "text"}, "location": {"x": 1, "y": 5}},
                {"type": "text", "text": "Mute", "command": {"cmd_id": "mute"}, "location": {"x": 2, "y": 5}},
                {"type": "text", "text": "Vol-", "command": {"cmd_id": "volumedown"}, "location": {"x": 3, "y": 5}},
            ]
        }
        pages.append(numbers_page)

        # Colors Page
        colors_page = {
            "page_id": "colors",
            "name": "Color Buttons",
            "grid": {"width": 4, "height": 6},
            "items": [
                {"type": "text", "text": "RED", "command": {"cmd_id": "red"}, "location": {"x": 0, "y": 1}, "size": {"width": 2, "height": 1}},
                {"type": "text", "text": "GREEN", "command": {"cmd_id": "green"}, "location": {"x": 2, "y": 1}, "size": {"width": 2, "height": 1}},
                {"type": "text", "text": "YELLOW", "command": {"cmd_id": "yellow"}, "location": {"x": 0, "y": 3}, "size": {"width": 2, "height": 1}},
                {"type": "text", "text": "BLUE", "command": {"cmd_id": "blue"}, "location": {"x": 2, "y": 3}, "size": {"width": 2, "height": 1}},
                
                {"type": "text", "text": "Home", "command": {"cmd_id": "home"}, "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "Search", "command": {"cmd_id": "search"}, "location": {"x": 2, "y": 0}},
                {"type": "text", "text": "Services", "command": {"cmd_id": "services"}, "location": {"x": 0, "y": 5}},
                {"type": "text", "text": "Text", "command": {"cmd_id": "text"}, "location": {"x": 2, "y": 5}},
            ]
        }
        pages.append(colors_page)

        return pages

    async def handle_command(self, entity: Remote, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle commands sent to the remote."""
        _LOG.debug(f"Remote command: {cmd_id} with params: {params}")

        if not self._device.is_connected:
            _LOG.warning(f"Device not available for command: {cmd_id}")
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                await self._device.client.send_remote_command("on")
                self.attributes[Attributes.STATE] = States.ON
                if self.is_configured:
                    self.configured_event(self.attributes)
                return StatusCodes.OK

            elif cmd_id == Commands.OFF:
                await self._device.client.send_remote_command("standby")
                self.attributes[Attributes.STATE] = States.OFF
                if self.is_configured:
                    self.configured_event(self.attributes)
                return StatusCodes.OK

            elif cmd_id == Commands.TOGGLE:
                await self._device.client.send_remote_command("power")
                return StatusCodes.OK

            elif cmd_id == Commands.SEND_CMD:
                if params and "command" in params:
                    command = params["command"]
                    success = await self._device.client.send_remote_command(command)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            else:
                _LOG.warning(f"Unknown command: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED

        except Exception as e:
            _LOG.error(f"Error executing remote command {cmd_id}: {e}")
            return StatusCodes.SERVER_ERROR
"""SkyQ Media Player entity."""
import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.media_player import MediaPlayer, Attributes, Features, States, Commands, DeviceClasses, Options

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQMediaPlayer(MediaPlayer):
    """Media player entity for SkyQ devices."""

    def __init__(self, config: SkyQDeviceConfig, device: SkyQDevice):
        """Initialize the media player entity."""
        entity_id = f"media_player.{config.identifier}"
        
        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.PLAY_PAUSE,
            Features.STOP,
            Features.NEXT,
            Features.PREVIOUS,
            Features.FAST_FORWARD,
            Features.REWIND,
            Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE,
            Features.MEDIA_TITLE,
            Features.MEDIA_IMAGE_URL,
        ]

        # Start with UNAVAILABLE - device will update when connected
        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_IMAGE_URL: "",
        }

        # Initialize WITHOUT options
        super().__init__(
            identifier=entity_id,
            name=config.name,
            features=features,
            attributes=attributes,
            device_class=DeviceClasses.SET_TOP_BOX,
            cmd_handler=self.handle_command,
        )
        
        self._config = config
        self._device = device
        
        # Set options AFTER initialization
        self.options = {
            Options.SIMPLE_COMMANDS: [
                Commands.ON,
                Commands.OFF,
                Commands.PLAY_PAUSE,
                Commands.STOP,
                Commands.NEXT,
                Commands.PREVIOUS,
                Commands.VOLUME_UP,
                Commands.VOLUME_DOWN,
                Commands.MUTE_TOGGLE,
            ]
        }
        
        # Register for device events - CRITICAL!
        device.events.on("UPDATE", self._on_device_update)
        
        _LOG.debug("Media player entity created: %s", entity_id)

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
            elif state_str == "PLAYING":
                self.attributes[Attributes.STATE] = States.PLAYING
            else:
                self.attributes[Attributes.STATE] = States.UNKNOWN
            
            # CRITICAL: Notify framework of attribute change
            if self.is_configured:
                self.configured_event(self.attributes)
                _LOG.info("[%s] Pushed state update to framework: %s", self.id, state_str)

    async def handle_command(self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle media player commands."""
        _LOG.debug(f"Media player command: {cmd_id} with params: {params}")

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

            elif cmd_id == Commands.PLAY_PAUSE:
                await self._device.client.send_remote_command("play")
                return StatusCodes.OK

            elif cmd_id == Commands.STOP:
                await self._device.client.send_remote_command("stop")
                return StatusCodes.OK

            elif cmd_id == Commands.NEXT:
                await self._device.client.send_remote_command("channelup")
                return StatusCodes.OK

            elif cmd_id == Commands.PREVIOUS:
                await self._device.client.send_remote_command("channeldown")
                return StatusCodes.OK

            elif cmd_id == Commands.FAST_FORWARD:
                await self._device.client.send_remote_command("fastforward")
                return StatusCodes.OK

            elif cmd_id == Commands.REWIND:
                await self._device.client.send_remote_command("rewind")
                return StatusCodes.OK

            elif cmd_id == Commands.VOLUME_UP:
                await self._device.client.send_remote_command("volumeup")
                return StatusCodes.OK

            elif cmd_id == Commands.VOLUME_DOWN:
                await self._device.client.send_remote_command("volumedown")
                return StatusCodes.OK

            elif cmd_id == Commands.MUTE_TOGGLE:
                await self._device.client.send_remote_command("mute")
                return StatusCodes.OK

            else:
                _LOG.warning(f"Unknown command: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED

        except Exception as e:
            _LOG.error(f"Error executing command {cmd_id}: {e}")
            return StatusCodes.SERVER_ERROR
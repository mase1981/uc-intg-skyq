"""SkyQ Voice Assistant entity."""
import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.voice_assistant import VoiceAssistant, Attributes, States, Commands

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQVoiceAssistant(VoiceAssistant):
    """Voice Assistant entity for SkyQ devices."""

    def __init__(self, config: SkyQDeviceConfig, device: SkyQDevice):
        """Initialize the voice assistant entity."""
        # Plain string entity ID - NOT enum!
        entity_id = f"voice_assistant.{config.identifier}"
        
        super().__init__(
            identifier=entity_id,
            name=f"{config.name} Voice",
            features=[],  # No features for now - will add when we know what's supported
            attributes={
                Attributes.STATE: States.UNAVAILABLE,
            },
            cmd_handler=self.handle_command,
        )
        
        self._config = config
        self._device = device
        
        _LOG.debug("Voice assistant entity created: %s", entity_id)

    async def handle_command(self, entity: VoiceAssistant, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle voice assistant commands."""
        _LOG.info("Voice command received: %s with params: %s", cmd_id, params)
        
        if not self._device.is_connected:
            _LOG.warning("Device not connected, cannot process voice command")
            return StatusCodes.SERVICE_UNAVAILABLE
        
        try:
            # For now, any voice command triggers the Sky button
            _LOG.info("Activating voice on SkyQ device")
            await self._device.client.send_remote_command("sky")
            return StatusCodes.OK
                
        except Exception as e:
            _LOG.error("Error handling voice command %s: %s", cmd_id, e)
            return StatusCodes.SERVER_ERROR
"""
SkyQ integration driver.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging

from ucapi import EntityTypes
from ucapi_framework import BaseIntegrationDriver

from uc_intg_skyq.config import SkyQConfigManager, SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice
from uc_intg_skyq.media_player import SkyQMediaPlayer
from uc_intg_skyq.remote import SkyQRemote
from uc_intg_skyq.sensor import SkyQChannelSensor, SkyQProgramSensor
# from uc_intg_skyq.voice_assistant import SkyQVoiceAssistant  # Keep for future

_LOG = logging.getLogger(__name__)


class SkyQDriver(BaseIntegrationDriver[SkyQDevice, SkyQDeviceConfig]):
    """SkyQ integration driver."""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(
            device_class=SkyQDevice,
            entity_classes=[],
            loop=loop,
            driver_id="skyq"
        )
    
    def create_entities(
        self,
        device_config: SkyQDeviceConfig,
        device: SkyQDevice
    ) -> list:
        """Create entities for a SkyQ device."""
        entities = []
        
        # Media player entity (always created)
        media_player = SkyQMediaPlayer(device_config, device)
        entities.append(media_player)
        _LOG.info("Created media player: %s for %s", media_player.id, device_config.name)
        
        # Remote entity (always created)
        remote = SkyQRemote(device_config, device)
        entities.append(remote)
        _LOG.info("Created remote: %s for %s", remote.id, device_config.name)
        
        # Voice assistant entity (DISABLED - placeholder for future)
        # if device_config.enable_voice:
        #     voice = SkyQVoiceAssistant(device_config, device)
        #     entities.append(voice)
        #     _LOG.info("Created voice assistant: %s for %s", voice.id, device_config.name)
        
        # Sensor entities (if enabled)
        if device_config.enable_sensors:
            channel_sensor = SkyQChannelSensor(device_config, device)
            entities.append(channel_sensor)
            _LOG.info("Created channel sensor: %s for %s", channel_sensor.id, device_config.name)
            
            program_sensor = SkyQProgramSensor(device_config, device)
            entities.append(program_sensor)
            _LOG.info("Created program sensor: %s for %s", program_sensor.id, device_config.name)
        
        return entities
    
    def device_from_entity_id(self, entity_id: str) -> str | None:
        """Extract device ID from entity ID."""
        if not entity_id or "." not in entity_id:
            return None
        
        parts = entity_id.split(".")
        
        # Format: type.device_id or type.device_id.sub
        if len(parts) >= 2:
            return parts[1]
        
        return None
    
    def get_entity_ids_for_device(self, device_id: str) -> list[str]:
        """Get all entity IDs for a device."""
        device_config = self.get_device_config(device_id)
        if not device_config:
            return []
        
        entity_ids = [
            f"{EntityTypes.MEDIA_PLAYER}.{device_id}",
            f"{EntityTypes.REMOTE}.{device_id}"
        ]
        
        # Voice disabled
        # if device_config.enable_voice:
        #     entity_ids.append(f"{EntityTypes.VOICE_ASSISTANT}.{device_id}")
        
        if device_config.enable_sensors:
            entity_ids.append(f"{EntityTypes.SENSOR}.{device_id}.channel")
            entity_ids.append(f"{EntityTypes.SENSOR}.{device_id}.program")
        
        return entity_ids
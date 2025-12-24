"""SkyQ Device implementation."""
import logging
from typing import Any

from ucapi_framework import PersistentConnectionDevice, DeviceEvents

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQDevice(PersistentConnectionDevice):
    """SkyQ device with persistent connection and state management."""
    
    def __init__(self, device_config: SkyQDeviceConfig, **kwargs):
        super().__init__(device_config, **kwargs)
        self._device_config = device_config
        self.client: SkyQClient | None = None
        
    @property
    def identifier(self) -> str:
        return self._device_config.identifier
    
    @property
    def name(self) -> str:
        return self._device_config.name
    
    @property
    def address(self) -> str:
        return self._device_config.host
    
    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address}:{self._device_config.rest_port})"
    
    async def establish_connection(self) -> Any:
        """Establish connection to SkyQ device."""
        _LOG.info("[%s] Establishing connection", self.log_id)
        
        self.client = SkyQClient(
            self._device_config.host,
            self._device_config.rest_port,
            49160
        )
        
        # Test connection
        if not await self.client.test_connection():
            raise ConnectionError(f"Failed to connect to {self.address}")
        
        _LOG.info("[%s] Connection established", self.log_id)
        
        # Get initial state and emit to entities
        await self._update_entity_states()
        
        return self.client
    
    async def close_connection(self) -> None:
        """Close connection to SkyQ device."""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def maintain_connection(self) -> None:
        """Maintain connection and poll for state changes."""
        _LOG.debug("[%s] Starting polling loop", self.log_id)
        
        while self.is_connected:
            try:
                # Poll every 30 seconds
                await asyncio.sleep(30)
                
                if not self.is_connected:
                    break
                
                # Update entity states
                await self._update_entity_states()
                
            except Exception as err:
                _LOG.error("[%s] Error in polling loop: %s", self.log_id, err)
                break
        
        _LOG.debug("[%s] Polling loop ended", self.log_id)
    
    async def _update_entity_states(self) -> None:
        """Query device state and emit updates to entities."""
        if not self.client:
            return
        
        try:
            # Get power status
            is_standby = await self.client.get_power_status()
            
            # Determine state
            if is_standby is True:
                new_state = "OFF"
            elif is_standby is False:
                new_state = "ON"
            else:
                new_state = "UNKNOWN"
            
            # Emit to media player
            media_player_id = f"media_player.{self.identifier}"
            self.events.emit(DeviceEvents.UPDATE, media_player_id, {
                "state": new_state
            })
            
            # Emit to remote
            remote_id = f"remote.{self.identifier}"
            self.events.emit(DeviceEvents.UPDATE, remote_id, {
                "state": new_state
            })
            
            _LOG.debug("[%s] Emitted state update: %s", self.log_id, new_state)
            
        except Exception as err:
            _LOG.error("[%s] Error updating entity states: %s", self.log_id, err)


import asyncio
"""
SkyQ Media Player entity implementation.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import ucapi.api_definitions as uc
from ucapi.media_player import MediaPlayer, Attributes, Features, States, Commands

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQMediaPlayer(MediaPlayer):

    def __init__(self, device_config: SkyQDeviceConfig, client: SkyQClient):
        self.device_config = device_config
        self.client = client

        entity_id = f"skyq_media_{device_config.device_id}"
        entity_name = f"{device_config.name}"

        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.PLAY_PAUSE,
            Features.STOP,
            Features.NEXT,
            Features.PREVIOUS,
            Features.FAST_FORWARD,
            Features.REWIND,
            Features.VOLUME,
            Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE,
            Features.UNMUTE,
            Features.MUTE,
            Features.MEDIA_TITLE,
            Features.MEDIA_IMAGE_URL,
            Features.MEDIA_TYPE,
            Features.MEDIA_DURATION,
            Features.MEDIA_POSITION,
            Features.SEEK
        ]

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.MEDIA_TYPE: "channel",
            Attributes.MEDIA_DURATION: 0,
            Attributes.MEDIA_POSITION: 0
        }

        super().__init__(
            identifier=entity_id,
            name=entity_name,
            features=features,
            attributes=attributes,
            cmd_handler=self.command_handler
        )

        self._available = False
        self._connected = False
        self._current_channel = None
        self._current_program = None
        self._last_update = 0
        self._integration_api = None

        _LOG.debug(f"Initialized SkyQ media player: {entity_id}")

    async def initialize(self) -> bool:
        """Initialize the media player entity."""
        _LOG.info(f"Initializing SkyQ media player: {self.device_config.name}")

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
                            _LOG.info(f"Updated media player entity name to: {enhanced_name}")
                except Exception as e:
                    _LOG.warning(f"Could not get device info for media player naming: {e}")

                self._last_update = 0
                await self._update_status()

                _LOG.info(f"SkyQ media player initialized successfully: {self.name}")
                return True
            else:
                _LOG.warning(f"Failed to connect to SkyQ device: {self.device_config.name}")
                self._available = False
                self._connected = False
                self.attributes[Attributes.STATE] = States.UNAVAILABLE
                return False

        except Exception as e:
            _LOG.error(f"Failed to initialize SkyQ media player {self.device_config.name}: {e}")
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
                entity_name = device_name
            else:
                if serial and not serial.startswith("SIM"):
                    entity_name = f"SkyQ {model} ({serial[-4:]})"
                else:
                    entity_name = f"SkyQ {model} ({self.device_config.host})"
        else:
            entity_name = base_name

        return entity_name

    async def shutdown(self):
        """Shutdown the media player entity."""
        _LOG.info(f"Shutting down SkyQ media player: {self.device_config.name}")
        self._available = False
        self._connected = False
        self.attributes[Attributes.STATE] = States.UNAVAILABLE
        await self.client.disconnect()
        _LOG.debug(f"SkyQ media player shutdown complete: {self.device_config.name}")

    async def _update_status(self):
        """Update media player status using Home Assistant pattern - FIXED v1.0.36."""
        try:
            if not self._connected:
                _LOG.debug("Not connected, skipping status update")
                return

            import time
            current_time = time.time()

            if self._last_update > 0 and (current_time - self._last_update < 5):
                _LOG.debug(f"Rate limited - last update {current_time - self._last_update:.1f}s ago")
                return

            self._last_update = current_time
            _LOG.info(f"=== STATUS UPDATE v1.0.36 - HOME ASSISTANT METHOD ===")

            # Get power state
            is_standby = False
            try:
                is_standby = await self.client.get_power_status()
                _LOG.info(f"Power status: is_standby={is_standby}")
                
                if is_standby:
                    self.attributes[Attributes.STATE] = States.OFF
                    self.attributes[Attributes.MEDIA_TITLE] = ""
                    self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                    _LOG.info("Device in standby, returning")
                    return
                else:
                    self.attributes[Attributes.STATE] = States.PLAYING
                    _LOG.info("Device is ON")
            except Exception as e:
                _LOG.warning(f"Could not get power status: {e}")

            # HOME ASSISTANT METHOD: get_current_media() -> getCurrentLiveTVProgramme(sid)
            try:
                if self.client._skyq_remote and self.client._skyq_remote.device_setup:
                    _LOG.info("=== STEP 1: Getting current media (for channel SID) ===")
                    
                    current_media = await asyncio.get_event_loop().run_in_executor(
                        None, self.client._skyq_remote.get_current_media
                    )
                    
                    _LOG.info(f"get_current_media() returned: {current_media}")
                    _LOG.info(f"  Type: {type(current_media)}")
                    
                    if current_media:
                        # Try to get attributes from the media object
                        _LOG.info(f"  Attributes: {[attr for attr in dir(current_media) if not attr.startswith('_')]}")
                        
                        # Extract channel SID (multiple ways to try)
                        channel_sid = None
                        
                        if hasattr(current_media, 'sid'):
                            channel_sid = getattr(current_media, 'sid', None)
                            _LOG.info(f"  Found sid attribute: {channel_sid}")
                        
                        if not channel_sid and hasattr(current_media, 'channelId'):
                            channel_sid = getattr(current_media, 'channelId', None)
                            _LOG.info(f"  Found channelId attribute: {channel_sid}")
                        
                        if not channel_sid and hasattr(current_media, 'channel'):
                            channel_obj = getattr(current_media, 'channel', None)
                            if channel_obj and hasattr(channel_obj, 'sid'):
                                channel_sid = getattr(channel_obj, 'sid', None)
                                _LOG.info(f"  Found channel.sid: {channel_sid}")
                        
                        if not channel_sid and isinstance(current_media, dict):
                            channel_sid = current_media.get('sid') or current_media.get('channelId')
                            _LOG.info(f"  Found in dict: {channel_sid}")
                        
                        _LOG.info(f"  Final extracted channel SID: {channel_sid}")
                        
                        if channel_sid:
                            # STEP 2: Get programme info (HOME ASSISTANT WAY)
                            _LOG.info(f"=== STEP 2: Calling getCurrentLiveTVProgramme({channel_sid}) ===")
                            
                            programme = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.client._skyq_remote.getCurrentLiveTVProgramme,
                                str(channel_sid)
                            )
                            
                            _LOG.info(f"getCurrentLiveTVProgramme returned: {programme}")
                            _LOG.info(f"  Type: {type(programme)}")
                            
                            if programme:
                                _LOG.info(f"  Attributes: {[attr for attr in dir(programme) if not attr.startswith('_')]}")
                                
                                # Extract programme data
                                channel = getattr(programme, 'channel', None)
                                title = getattr(programme, 'title', None)
                                image_url = getattr(programme, 'imageUrl', None) or getattr(programme, 'image_url', None)
                                
                                _LOG.info(f"  Programme data - channel={channel}, title={title}, image={bool(image_url)}")
                                
                                # Build media title
                                if title and channel:
                                    self.attributes[Attributes.MEDIA_TITLE] = f"{channel}: {title}"
                                    _LOG.info(f"SUCCESS: Set title to '{self.attributes[Attributes.MEDIA_TITLE]}'")
                                elif channel:
                                    self.attributes[Attributes.MEDIA_TITLE] = channel
                                    _LOG.info(f"SUCCESS: Set title to channel '{channel}'")
                                elif title:
                                    self.attributes[Attributes.MEDIA_TITLE] = title
                                    _LOG.info(f"SUCCESS: Set title to '{title}'")
                                else:
                                    _LOG.warning("Programme object has no channel or title")
                                    raise ValueError("No media info in programme")
                                
                                # Set image URL
                                if image_url:
                                    self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url
                                    _LOG.info(f"Set image URL: {image_url[:50]}...")
                                
                                _LOG.info("=== STATUS UPDATE SUCCESSFUL ===")
                                return  # Success!
                            else:
                                _LOG.warning("getCurrentLiveTVProgramme returned None")
                        else:
                            _LOG.warning("Could not extract channel SID from current_media")
                    else:
                        _LOG.warning("get_current_media() returned None")
                else:
                    _LOG.warning("pyskyqremote not available")
                    
            except Exception as e:
                _LOG.error(f"Error in HOME ASSISTANT method: {e}", exc_info=True)
            
            # Fallback to get_active_application
            _LOG.info("=== FALLBACK: get_active_application() ===")
            try:
                if self.client._skyq_remote and self.client._skyq_remote.device_setup:
                    app = await asyncio.get_event_loop().run_in_executor(
                        None, self.client._skyq_remote.get_active_application
                    )
                    
                    _LOG.info(f"get_active_application() returned: {app}")
                    
                    if app and hasattr(app, 'title'):
                        app_title = getattr(app, 'title', '')
                        if app_title:
                            self.attributes[Attributes.MEDIA_TITLE] = app_title
                            _LOG.info(f"Media info from app: {app_title}")
                            return
            except Exception as app_e:
                _LOG.error(f"Fallback failed: {app_e}")
            
            # Final fallback
            self.attributes[Attributes.MEDIA_TITLE] = "Live TV"
            _LOG.info(f"Final fallback: Live TV")
                    
        except Exception as e:
            _LOG.error(f"FATAL ERROR in _update_status: {e}", exc_info=True)

    async def update_attributes(self):
        """Update entity attributes."""
        await self._update_status()

        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.identifier,
                    self.attributes
                )
                _LOG.debug("Updated media player attributes via integration API")
            except Exception as e:
                _LOG.debug(f"Could not update via integration API: {e}")

    async def command_handler(self, entity: MediaPlayer, cmd_id: str, params: dict = None) -> uc.StatusCodes:
        """Handle commands sent to the media player."""
        _LOG.debug(f"Media player command: {cmd_id} with params: {params}")

        if not self._available:
            _LOG.warning(f"Device not available for command: {cmd_id}")
            return uc.StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is True:
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.ON
                        await self._update_status()

            elif cmd_id == Commands.OFF:
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is False:
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.OFF

            elif cmd_id == Commands.TOGGLE:
                await self.client.send_remote_command("power")

            elif cmd_id == Commands.PLAY_PAUSE:
                await self.client.send_remote_command("play")

            elif cmd_id == Commands.STOP:
                await self.client.send_remote_command("stop")

            elif cmd_id == Commands.NEXT:
                await self.client.send_remote_command("channelup")

            elif cmd_id == Commands.PREVIOUS:
                await self.client.send_remote_command("channeldown")

            elif cmd_id == Commands.FAST_FORWARD:
                await self.client.send_remote_command("fastforward")

            elif cmd_id == Commands.REWIND:
                await self.client.send_remote_command("rewind")

            elif cmd_id == Commands.VOLUME_UP:
                await self.client.send_remote_command("volumeup")

            elif cmd_id == Commands.VOLUME_DOWN:
                await self.client.send_remote_command("volumedown")

            elif cmd_id == Commands.MUTE_TOGGLE:
                await self.client.send_remote_command("mute")

            elif cmd_id == Commands.MUTE:
                await self.client.send_remote_command("mute")
                self.attributes[Attributes.MUTED] = True

            elif cmd_id == Commands.UNMUTE:
                await self.client.send_remote_command("mute")
                self.attributes[Attributes.MUTED] = False

            elif cmd_id == Commands.SEEK:
                _LOG.warning("Direct seek not supported by SkyQ")
                return uc.StatusCodes.NOT_IMPLEMENTED

            else:
                _LOG.warning(f"Unknown command: {cmd_id}")
                return uc.StatusCodes.NOT_IMPLEMENTED

            await self._update_status()
            return uc.StatusCodes.OK

        except Exception as e:
            _LOG.error(f"Error executing command {cmd_id}: {e}")
            return uc.StatusCodes.SERVER_ERROR

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information for diagnostics."""
        return {
            "device_id": self.device_config.device_id,
            "name": self.device_config.name,
            "host": self.device_config.host,
            "available": self._available,
            "connected": self._connected,
            "state": self.attributes.get(Attributes.STATE),
            "media_title": self.attributes.get(Attributes.MEDIA_TITLE),
            "last_update": self._last_update
        }
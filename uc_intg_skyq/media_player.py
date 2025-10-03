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

# Constants from Home Assistant
APP_EPG = "com.bskyb.epgui"


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
        
        # Add polling mechanism (like Home Assistant)
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_polling = False

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

                # Initial update
                self._last_update = 0
                await self._update_status()
                
                # Start polling (like Home Assistant does with should_poll=True)
                self._start_polling()

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
    
    def _start_polling(self):
        """Start background polling task (Home Assistant pattern)."""
        if self._polling_task is None or self._polling_task.done():
            self._stop_polling = False
            self._polling_task = asyncio.create_task(self._polling_loop())
            _LOG.info(f"Started polling for {self.device_config.name}")
    
    async def _polling_loop(self):
        """Background polling loop - updates every 10 seconds like Home Assistant."""
        try:
            while not self._stop_polling and self._connected:
                await asyncio.sleep(10)  # Poll every 10 seconds (HA default)
                
                if not self._stop_polling and self._connected:
                    _LOG.debug(f"Polling update for {self.device_config.name}")
                    # FIX 2: Bypass rate limit for polling by resetting last_update
                    self._last_update = 0
                    await self.update_attributes()
                    
        except asyncio.CancelledError:
            _LOG.debug(f"Polling cancelled for {self.device_config.name}")
        except Exception as e:
            _LOG.error(f"Error in polling loop: {e}", exc_info=True)

    async def shutdown(self):
        """Shutdown the media player entity."""
        _LOG.info(f"Shutting down SkyQ media player: {self.device_config.name}")
        
        # Stop polling
        self._stop_polling = True
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        self._available = False
        self._connected = False
        self.attributes[Attributes.STATE] = States.UNAVAILABLE
        await self.client.disconnect()
        _LOG.debug(f"SkyQ media player shutdown complete: {self.device_config.name}")

    async def _update_status(self):
        """Update media player status using EXACT Home Assistant pattern."""
        try:
            if not self._connected:
                _LOG.debug("Not connected, skipping status update")
                return

            import time
            current_time = time.time()

            # Reduce rate limit from 5s to 2s
            if self._last_update > 0 and (current_time - self._last_update < 2):
                _LOG.debug(f"Rate limited - last update {current_time - self._last_update:.1f}s ago")
                return

            self._last_update = current_time
            _LOG.info(f"=== STATUS UPDATE v1.0.40 - POLLING ENABLED ===")

            # STEP 1: Check power status
            is_standby = False
            try:
                is_standby = await self.client.get_power_status()
                _LOG.info(f"Power status: is_standby={is_standby}")
                
                if is_standby:
                    self.attributes[Attributes.STATE] = States.OFF
                    self.attributes[Attributes.MEDIA_TITLE] = ""
                    self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                    _LOG.info("Device in standby")
                    return
                else:
                    self.attributes[Attributes.STATE] = States.PLAYING
                    _LOG.info("Device is ON")
            except Exception as e:
                _LOG.warning(f"Could not get power status: {e}")

            # STEP 2: Get active application
            if not self.client._skyq_remote or not self.client._skyq_remote.device_setup:
                _LOG.warning("pyskyqremote not available")
                self.attributes[Attributes.MEDIA_TITLE] = "Live TV"
                return

            try:
                _LOG.info("=== STEP 2: Getting active application ===")
                app = await asyncio.get_event_loop().run_in_executor(
                    None, self.client._skyq_remote.get_active_application
                )
                
                _LOG.info(f"Active app: {app}")
                
                if app:
                    app_id = getattr(app, 'appId', None)
                    app_title = getattr(app, 'title', None)
                    _LOG.info(f"  appId: {app_id}, title: {app_title}")
                    
                    #  Check if in EPG
                    if app_id == APP_EPG:
                        _LOG.info("=== In EPG - Getting live media ===")
                        
                        # STEP 3: Get current media
                        current_media = await asyncio.get_event_loop().run_in_executor(
                            None, self.client._skyq_remote.get_current_media
                        )
                        
                        _LOG.info(f"current_media: {current_media}")
                        
                        if current_media:
                            is_live = getattr(current_media, 'live', False)
                            sid = getattr(current_media, 'sid', None)
                            
                            _LOG.info(f"  live: {is_live}, sid: {sid}")
                            
                            #  Check live AND sid
                            if is_live and sid:
                                _LOG.info(f"=== STEP 4: Getting programme for SID {sid} ===")
                                
                                #  STEP 4: Get programme
                                current_programme = await asyncio.get_event_loop().run_in_executor(
                                    None,
                                    self.client._skyq_remote.get_current_live_tv_programme,
                                    sid
                                )
                                
                                _LOG.info(f"current_programme: {current_programme}")
                                
                                if current_programme:
                                    channel = getattr(current_programme, 'channelname', None)
                                    title = getattr(current_programme, 'title', None)
                                    image_url = getattr(current_programme, 'image_url', None)
                                    
                                    _LOG.info(f"  channelname: {channel}")
                                    _LOG.info(f"  title: {title}")
                                    _LOG.info(f"  image_url: {image_url}")
                                    
                                    # Set media info
                                    if channel and title:
                                        self.attributes[Attributes.MEDIA_TITLE] = f"{channel}: {title}"
                                    elif channel:
                                        self.attributes[Attributes.MEDIA_TITLE] = channel
                                    elif title:
                                        self.attributes[Attributes.MEDIA_TITLE] = title
                                    else:
                                        self.attributes[Attributes.MEDIA_TITLE] = "Live TV"
                                    
                                    if image_url:
                                        self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url
                                    else:
                                        self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                                    
                                    _LOG.info(f"SUCCESS: Title='{self.attributes[Attributes.MEDIA_TITLE]}', Image={bool(image_url)}")
                                    return
                                else:
                                    _LOG.warning("get_current_live_tv_programme returned None")
                            else:
                                _LOG.warning(f"Not live content or no SID - live={is_live}, sid={sid}")
                        else:
                            _LOG.warning("get_current_media returned None")
                    else:
                        # Not in EPG - in an app
                        _LOG.info(f"In app: {app_title}")
                        self.attributes[Attributes.MEDIA_TITLE] = app_title if app_title else "App"
                        self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                        return
                else:
                    _LOG.warning("get_active_application returned None")
                    
            except Exception as e:
                _LOG.error(f"Error in Home Assistant pattern: {e}", exc_info=True)
            
            # Final fallback
            self.attributes[Attributes.MEDIA_TITLE] = "Live TV"
            self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
            _LOG.info("Using fallback: Live TV")
                    
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
            # FIX 2: Track if this is a channel-changing command
            is_channel_command = cmd_id in [Commands.NEXT, Commands.PREVIOUS]
            
            if cmd_id == Commands.ON:
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is True:
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.ON
                        # FIX 2: Force immediate update after power on
                        self._last_update = 0
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

            if is_channel_command:
                _LOG.info("Channel command detected - forcing immediate update")
                await asyncio.sleep(1.5)  # Wait for SkyQ to change channel
                self._last_update = 0  # Bypass rate limit
                await self._update_status()
            else:
                # Normal update for other commands
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
            "last_update": self._last_update,
            "polling_active": self._polling_task is not None and not self._polling_task.done()
        }
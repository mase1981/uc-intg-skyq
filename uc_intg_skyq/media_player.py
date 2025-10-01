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

        # Features WITHOUT SELECT_SOURCE
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

                # Update initial status - FORCE first update
                self._last_update = 0  # Reset to allow first update
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
        """Update media player status using pyskyqremote methods (HA pattern)."""
        try:
            if not self._connected:
                _LOG.debug("Not connected, skipping status update")
                return

            import time
            current_time = time.time()

            # Rate limit updates to every 5 seconds (but allow first update)
            if self._last_update > 0 and (current_time - self._last_update < 5):
                _LOG.debug(f"Rate limited - last update {current_time - self._last_update:.1f}s ago")
                return

            self._last_update = current_time
            _LOG.debug(f"Updating media player status for {self.device_config.name}")

            # Get power state first (from HA pattern)
            power_state_checked = False
            is_standby = False
            try:
                is_standby = await self.client.get_power_status()
                power_state_checked = True
                
                if is_standby:
                    self.attributes[Attributes.STATE] = States.OFF
                    _LOG.debug(f"Device {self.device_config.name} is in standby")
                else:
                    self.attributes[Attributes.STATE] = States.PLAYING
                    _LOG.debug(f"Device {self.device_config.name} is on")
            except Exception as e:
                _LOG.debug(f"Could not get power status: {e}")

            try:
                if self.client._skyq_remote and self.client._skyq_remote.device_setup:
                    _LOG.debug("Attempting to get current programme from pyskyqremote")
                    
                    # Try multiple possible method names from pyskyqremote
                    programme = None
                    
                    # Method 1: Try get_current_live_tv_programme (snake_case)
                    if hasattr(self.client._skyq_remote, 'get_current_live_tv_programme'):
                        _LOG.debug("Using get_current_live_tv_programme() method")
                        programme = await asyncio.get_event_loop().run_in_executor(
                            None, self.client._skyq_remote.get_current_live_tv_programme
                        )
                    # Method 2: Try current_programme property
                    elif hasattr(self.client._skyq_remote, 'current_programme'):
                        _LOG.debug("Using current_programme property")
                        programme = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: self.client._skyq_remote.current_programme
                        )
                    # Method 3: Try getCurrentProgram (alternative naming)
                    elif hasattr(self.client._skyq_remote, 'getCurrentProgram'):
                        _LOG.debug("Using getCurrentProgram() method")
                        programme = await asyncio.get_event_loop().run_in_executor(
                            None, self.client._skyq_remote.getCurrentProgram
                        )
                    else:
                        # List all available methods for debugging
                        available_methods = [m for m in dir(self.client._skyq_remote) if not m.startswith('_')]
                        _LOG.warning(f"Could not find programme method. Available methods: {available_methods[:20]}")
                    
                    if programme:
                        _LOG.debug(f"Got programme object: {type(programme)}")
                        _LOG.debug(f"Programme object attributes: {dir(programme)}")
                        
                        # Extract info using HA's attribute access pattern
                        # Try different possible attribute names
                        channel_name = (getattr(programme, 'channel', '') or 
                                      getattr(programme, 'channelname', '') or
                                      getattr(programme, 'channel_name', ''))
                        
                        title = (getattr(programme, 'title', '') or
                                getattr(programme, 'programme_title', '') or
                                getattr(programme, 'programmename', ''))
                        
                        image_url = (getattr(programme, 'imageUrl', '') or
                                   getattr(programme, 'image_url', '') or
                                   getattr(programme, 'imageurl', ''))
                        
                        _LOG.debug(f"Programme details - Channel: {channel_name}, Title: {title}, Image: {bool(image_url)}")
                        
                        # Build media title
                        if title and channel_name:
                            self.attributes[Attributes.MEDIA_TITLE] = f"{channel_name}: {title}"
                        elif channel_name:
                            self.attributes[Attributes.MEDIA_TITLE] = channel_name
                        elif title:
                            self.attributes[Attributes.MEDIA_TITLE] = title
                        else:
                            # Only set to "Live TV" if we have no info AND device is ON
                            if power_state_checked and not is_standby:
                                self.attributes[Attributes.MEDIA_TITLE] = "Live TV"
                            else:
                                self.attributes[Attributes.MEDIA_TITLE] = ""
                        
                        # Set image URL
                        if image_url:
                            self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url
                        else:
                            self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                        
                        if self.attributes[Attributes.MEDIA_TITLE]:
                            _LOG.info(f"Updated media info - Title: {self.attributes[Attributes.MEDIA_TITLE]}")
                        else:
                            _LOG.debug("No media title available (device may be off or no program playing)")
                    else:
                        _LOG.debug("Programme method returned None - device may be off or not on live TV")
                        # Clear media info when None
                        if power_state_checked and is_standby:
                            self.attributes[Attributes.MEDIA_TITLE] = ""
                            self.attributes[Attributes.MEDIA_IMAGE_URL] = ""
                else:
                    _LOG.debug("pyskyqremote not available")
                    
            except Exception as e:
                _LOG.warning(f"Could not get current programme info: {e}", exc_info=True)

        except Exception as e:
            _LOG.error(f"Failed to update media player status: {e}", exc_info=True)

    async def update_attributes(self):
        """Update entity attributes."""
        await self._update_status()

        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.identifier,
                    self.attributes
                )
                _LOG.debug("Updated media player attributes via integration API for %s",
                          self.identifier)
            except Exception as e:
                _LOG.debug("Could not update media player via integration API: %s", e)

    async def command_handler(self, entity: MediaPlayer, cmd_id: str, params: dict = None) -> uc.StatusCodes:
        """Handle commands sent to the media player."""
        _LOG.debug(f"SkyQ media player command: {cmd_id} with params: {params}")

        if not self._available:
            _LOG.warning(f"SkyQ device {self.device_config.name} not available for command: {cmd_id}")
            return uc.StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                is_in_standby = await self.client.get_power_status()
                if is_in_standby is True:
                    _LOG.debug("Device is in STANDBY. Sending power toggle to turn ON.")
                    success = await self.client.send_remote_command("power")
                    if success:
                        self.attributes[Attributes.STATE] = States.ON
                        await self._update_status()
                elif is_in_standby is False:
                    _LOG.debug("Device is already ON. No action taken.")
                    self.attributes[Attributes.STATE] = States.ON
                else:
                    _LOG.warning("Could not determine power state. Sending power toggle as fallback.")
                    await self.client.send_remote_command("power")

            elif cmd_id == Commands.OFF:
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
                if success:
                    # Toggle state
                    current_state = self.attributes.get(Attributes.STATE)
                    if current_state == States.ON or current_state == States.PLAYING:
                        self.attributes[Attributes.STATE] = States.OFF
                    else:
                        self.attributes[Attributes.STATE] = States.ON

            elif cmd_id == Commands.PLAY_PAUSE:
                success = await self.client.send_remote_command("play")
                if success:
                    current_state = self.attributes.get(Attributes.STATE)
                    if current_state == States.PLAYING:
                        self.attributes[Attributes.STATE] = States.PAUSED
                    else:
                        self.attributes[Attributes.STATE] = States.PLAYING

            elif cmd_id == Commands.STOP:
                success = await self.client.send_remote_command("stop")
                if success:
                    self.attributes[Attributes.STATE] = States.ON

            elif cmd_id == Commands.NEXT:
                success = await self.client.send_remote_command("channelup")

            elif cmd_id == Commands.PREVIOUS:
                success = await self.client.send_remote_command("channeldown")

            elif cmd_id == Commands.FAST_FORWARD:
                success = await self.client.send_remote_command("fastforward")

            elif cmd_id == Commands.REWIND:
                success = await self.client.send_remote_command("rewind")

            elif cmd_id == Commands.VOLUME_UP:
                success = await self.client.send_remote_command("volumeup")

            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self.client.send_remote_command("volumedown")

            elif cmd_id == Commands.MUTE_TOGGLE:
                success = await self.client.send_remote_command("mute")
                if success:
                    current_muted = self.attributes.get(Attributes.MUTED, False)
                    self.attributes[Attributes.MUTED] = not current_muted

            elif cmd_id == Commands.MUTE:
                success = await self.client.send_remote_command("mute")
                if success:
                    self.attributes[Attributes.MUTED] = True

            elif cmd_id == Commands.UNMUTE:
                success = await self.client.send_remote_command("mute")
                if success:
                    self.attributes[Attributes.MUTED] = False

            elif cmd_id == Commands.SEEK:
                position = params.get("media_position") if params else None
                if position is not None:
                    _LOG.warning("Direct seek not supported by SkyQ")
                    return uc.StatusCodes.NOT_IMPLEMENTED

            else:
                _LOG.warning(f"Unknown command: {cmd_id}")
                return uc.StatusCodes.NOT_IMPLEMENTED

            # Update status after command
            await self._update_status()
            return uc.StatusCodes.OK

        except Exception as e:
            _LOG.error(f"Error executing media player command {cmd_id} on {self.device_config.name}: {e}")
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
            "connection_type": getattr(self.client, 'connection_type', 'unknown'),
            "using_fallback": getattr(self.client, 'is_using_fallback', False),
            "state": self.attributes.get(Attributes.STATE),
            "current_channel": self._current_channel,
            "media_title": self.attributes.get(Attributes.MEDIA_TITLE),
            "last_update": self._last_update
        }
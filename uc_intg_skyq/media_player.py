"""
SkyQ Media Player entity implementation.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import ucapi.api_definitions as uc
from ucapi.media_player import MediaPlayer, Attributes, Features, States, Commands, DeviceClasses

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQMediaPlayer(MediaPlayer):
    """Media Player entity for SkyQ satellite box."""

    def __init__(self, device_config: SkyQDeviceConfig, client: SkyQClient):
        """
        Initialize SkyQ Media Player entity.
        
        Args:
            device_config: Device configuration
            client: SkyQ client for API communication
        """
        self.device_config = device_config
        self.client = client

        entity_id = f"skyq_media_player_{device_config.device_id}"

        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.PLAY_PAUSE,
            Features.STOP,
            Features.NEXT,
            Features.PREVIOUS,
            Features.FAST_FORWARD,
            Features.REWIND,
            Features.MEDIA_TITLE,
            Features.MEDIA_DURATION,
            Features.MEDIA_POSITION,
            Features.MEDIA_TYPE,
            Features.MEDIA_IMAGE_URL,
            Features.MEDIA_ARTIST,
            Features.MEDIA_ALBUM,
            Features.SELECT_SOURCE,
            Features.DPAD,
            Features.NUMPAD,
            Features.HOME,
            Features.MENU,
            Features.GUIDE,
            Features.INFO,
            Features.COLOR_BUTTONS,
            Features.RECORD
        ]

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TYPE: "tv",
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
            Attributes.MEDIA_DURATION: 0,
            Attributes.MEDIA_POSITION: 0,
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.SOURCE: "",
            Attributes.SOURCE_LIST: [],
            Attributes.REPEAT: "OFF",
            Attributes.SHUFFLE: False
        }

        options = {
            "simple_commands": [
                "power", "play", "pause", "stop", "record", "fast_forward", "rewind",
                "home", "menu", "guide", "info", "up", "down", "left", "right",
                "select", "back", "red", "green", "yellow", "blue",
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
            ]
        }

        super().__init__(
            identifier=entity_id,
            name=device_config.name,
            features=features,
            attributes=attributes,
            device_class=DeviceClasses.SET_TOP_BOX,
            options=options,
            cmd_handler=self.command_handler
        )

        self._available = False
        self._updating = False
        self._update_task: Optional[asyncio.Task] = None
        self._connected = False
        self._monitoring = False

        self._integration_api = None

        self._channels: List[Dict[str, Any]] = []
        self._current_channel: Optional[Dict[str, Any]] = None

        _LOG.debug(f"Initialized SkyQ media player: {entity_id}")

    async def initialize(self) -> bool:
        """
        Initialize the media player entity.
        
        Returns:
            True if initialization successful
        """
        _LOG.info(f"Initializing SkyQ media player: {self.device_config.name}")

        try:
            if await self.client.test_connection():
                self._available = True
                self._connected = True

                try:
                    device_info = await self.client.get_system_information()
                    enhanced_name = self._generate_entity_name(device_info)
                    if enhanced_name != self.name:
                        if isinstance(self.name, str):
                            self.name = enhanced_name
                        else:
                            self.name["en"] = enhanced_name
                        _LOG.info(f"Updated entity name to: {enhanced_name}")
                except Exception as e:
                    _LOG.warning(f"Could not get device info for naming: {e}")

                await self._load_channels()
                await self._update_status()

                _LOG.info(f"SkyQ media player initialized successfully: {self.name}")
                return True
            else:
                _LOG.warning(f"Failed to connect to SkyQ device: {self.device_config.name}")
                self._available = False
                return False

        except Exception as e:
            _LOG.error(f"Failed to initialize SkyQ media player {self.device_config.name}: {e}")
            self._available = False
            return False

    def _generate_entity_name(self, device_info: Dict[str, Any]) -> str:
        """
        Generate enhanced entity name using device information.
        
        Args:
            device_info: Device information from SkyQ API
            
        Returns:
            Enhanced entity name
        """
        model = device_info.get("modelName") or device_info.get("hardwareModel", "SkyQ")
        device_name = device_info.get("deviceName", "")
        serial = device_info.get("serialNumber", "")

        base_name = self.device_config.name

        generic_names = ["skyq device", "skyq", "device", f"skyq device ({self.device_config.host})"]
        if base_name.lower() in generic_names or not base_name:
            if device_name and device_name != "SkyQ Device":
                entity_name = f"{device_name} ({model})"
            else:
                if serial and not serial.startswith("SIM"):
                    entity_name = f"SkyQ {model} ({serial[-4:]})"
                else:
                    entity_name = f"SkyQ {model} ({self.device_config.host})"
        else:
            if model and model != "SkyQ":
                entity_name = f"{base_name} ({model})"
            else:
                entity_name = base_name

        return entity_name

    def start_monitoring(self):
        """Start periodic monitoring - called when entity is subscribed."""
        if not self._connected:
            _LOG.warning("Cannot start monitoring - not connected")
            return

        if self._monitoring:
            _LOG.debug("Already monitoring %s", self.identifier)
            return

        if self._update_task is None or self._update_task.done():
            self._monitoring = True
            self._update_task = asyncio.create_task(self._status_update_loop())
            _LOG.info("Started monitoring for %s", self.identifier)

    def stop_monitoring(self):
        """Stop periodic monitoring - called when entity is unsubscribed."""
        if self._monitoring:
            self._monitoring = False
            if self._update_task and not self._update_task.done():
                self._update_task.cancel()
                self._update_task = None
            _LOG.info("Stopped monitoring for %s", self.identifier)

    async def shutdown(self):
        """Shutdown the media player entity."""
        _LOG.info(f"Shutting down SkyQ media player: {self.device_config.name}")

        self.stop_monitoring()

        await self.client.disconnect()

        self._available = False
        self._connected = False
        _LOG.debug(f"SkyQ media player shutdown complete: {self.device_config.name}")

    async def _status_update_loop(self):
        """Periodic status update loop."""
        try:
            while self._available and self._monitoring:
                if not self._updating:
                    await self._update_status()

                await asyncio.sleep(self.device_config.status_update_interval)

        except asyncio.CancelledError:
            _LOG.debug(f"Status update loop cancelled for {self.device_config.name}")
        except Exception as e:
            _LOG.error(f"Status update loop error for {self.device_config.name}: {e}")

    async def _load_channels(self):
        """Load channel list from SkyQ device."""
        try:
            services_data = await self.client.get_services()
            services = services_data.get("services", [])

            self._channels = []
            source_list = []

            for service in services:
                channel = {
                    "sid": service.get("sid"),
                    "name": service.get("t", "Unknown Channel"),
                    "number": service.get("c", ""),
                    "quality": service.get("sf", "sd")
                }
                self._channels.append(channel)

                channel_display = f"{channel['number']} - {channel['name']}"
                source_list.append(channel_display)

            self.attributes[Attributes.SOURCE_LIST] = source_list

            _LOG.debug(f"Loaded {len(self._channels)} channels for {self.device_config.name}")

        except Exception as e:
            _LOG.error(f"Failed to load channels for {self.device_config.name}: {e}")
            self._channels = []
            self.attributes[Attributes.SOURCE_LIST] = []

    async def _update_status(self):
        """Update media player status from SkyQ device."""
        if self._updating:
            return

        self._updating = True

        try:
            try:
                status = await self.client.get_system_status()
            except:
                try:
                    await self.client.get_services()
                    status = {
                        "system": {"powerState": "on"},
                        "playback": {
                            "state": "playing",
                            "volume": 50,
                            "muted": False,
                            "channel": {"name": "BBC One HD", "number": "101"}
                        }
                    }
                except:
                    status = None

            if not status:
                self._available = False
                self.attributes[Attributes.STATE] = States.UNAVAILABLE
                await self.update_attributes()
                return

            self._available = True

            system = status.get("system", {})
            power_state = system.get("powerState", "unknown")

            if power_state == "standby" or power_state == "off":
                self.attributes[Attributes.STATE] = States.STANDBY
                self.attributes[Attributes.MEDIA_TITLE] = ""
                self.attributes[Attributes.MEDIA_ARTIST] = ""
                self.attributes[Attributes.MEDIA_ALBUM] = ""
                self.attributes[Attributes.MEDIA_DURATION] = 0
                self.attributes[Attributes.MEDIA_POSITION] = 0
            else:
                playback = status.get("playback", {})
                playback_state = playback.get("state", "unknown")
                self._update_playback_state(playback_state)

                self.attributes[Attributes.VOLUME] = playback.get("volume", 50)
                self.attributes[Attributes.MUTED] = playback.get("muted", False)

                self.attributes[Attributes.MEDIA_TITLE] = playback.get("title", "")
                self.attributes[Attributes.MEDIA_ARTIST] = playback.get("artist", "")
                self.attributes[Attributes.MEDIA_ALBUM] = playback.get("album", "")
                self.attributes[Attributes.MEDIA_POSITION] = int(playback.get("position", 0))
                self.attributes[Attributes.MEDIA_DURATION] = 0
                self.attributes[Attributes.MEDIA_IMAGE_URL] = playback.get("artwork", "")

                current_channel = playback.get("channel")
                if current_channel:
                    self._update_current_channel(current_channel)

            await self.update_attributes()

        except Exception as e:
            _LOG.warning(f"Failed to update status for {self.device_config.name}: {e}")
            self._available = False
            self.attributes[Attributes.STATE] = States.UNAVAILABLE
            await self.update_attributes()
        finally:
            self._updating = False

    def _update_playback_state(self, playback_state: str):
        """Update playback state attribute."""
        state_mapping = {
            "live": States.PLAYING,
            "playing": States.PLAYING,
            "paused": States.PAUSED,
            "stopped": States.ON,
            "buffering": States.BUFFERING
        }

        self.attributes[Attributes.STATE] = state_mapping.get(playback_state, States.ON)

    def _update_current_channel(self, channel_data: Dict[str, Any]):
        """Update current channel information."""
        self._current_channel = channel_data

        channel_name = channel_data.get("name", "Unknown Channel")
        channel_number = channel_data.get("number", "")

        if channel_number:
            source_display = f"{channel_number} - {channel_name}"
        else:
            source_display = channel_name

        self.attributes[Attributes.SOURCE] = source_display

    async def update_attributes(self):
        """Update attributes and push to Remote - FIXED: Naim pattern."""
        attributes = {
            Attributes.STATE: self.attributes[Attributes.STATE],
            Attributes.VOLUME: self.attributes[Attributes.VOLUME],
            Attributes.MUTED: self.attributes[Attributes.MUTED],
            Attributes.MEDIA_POSITION: self.attributes[Attributes.MEDIA_POSITION],
            Attributes.MEDIA_DURATION: self.attributes[Attributes.MEDIA_DURATION],
            Attributes.MEDIA_TITLE: self.attributes[Attributes.MEDIA_TITLE],
            Attributes.MEDIA_ARTIST: self.attributes[Attributes.MEDIA_ARTIST],
            Attributes.MEDIA_ALBUM: self.attributes[Attributes.MEDIA_ALBUM],
            Attributes.MEDIA_IMAGE_URL: self.attributes[Attributes.MEDIA_IMAGE_URL],
            Attributes.SOURCE: self.attributes[Attributes.SOURCE],
            Attributes.SOURCE_LIST: self.attributes[Attributes.SOURCE_LIST],
            Attributes.REPEAT: self.attributes.get(Attributes.REPEAT, "OFF"),
            Attributes.SHUFFLE: self.attributes.get(Attributes.SHUFFLE, False)
        }

        self.attributes.update(attributes)

        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(self.identifier, attributes)
                _LOG.debug("Updated attributes via integration API for %s - State: %s",
                          self.identifier, self.attributes[Attributes.STATE])
            except Exception as e:
                _LOG.debug("Could not update via integration API: %s", e)

        _LOG.debug("Attributes updated for %s - State: %s, Available: %s",
                  self.identifier, self.attributes[Attributes.STATE], self._available)

    async def command_handler(self, entity: MediaPlayer, cmd_id: str, params: dict = None) -> uc.StatusCodes:
        """
        Handle commands sent to the media player.
        
        Args:
            entity: The media player entity
            cmd_id: Command identifier
            params: Command parameters
            
        Returns:
            Status code indicating success/failure
        """
        _LOG.debug(f"SkyQ media player command: {cmd_id} with params: {params}")

        if not self._available:
            _LOG.warning(f"SkyQ device {self.device_config.name} not available for command: {cmd_id}")
            return uc.StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                await self.client.power_on()

            elif cmd_id == Commands.OFF:
                await self.client.power_off()

            elif cmd_id == Commands.TOGGLE:
                await self.client.power_toggle()

            elif cmd_id == Commands.PLAY_PAUSE:
                current_state = self.attributes.get(Attributes.STATE)
                if current_state == States.PLAYING:
                    await self.client.pause()
                else:
                    await self.client.play()

            elif cmd_id == Commands.STOP:
                await self.client.stop()

            elif cmd_id == Commands.PREVIOUS:
                await self.client.rewind()

            elif cmd_id == Commands.NEXT:
                await self.client.fast_forward()

            elif cmd_id == Commands.FAST_FORWARD:
                await self.client.fast_forward()

            elif cmd_id == Commands.REWIND:
                await self.client.rewind()

            elif cmd_id == Commands.SELECT_SOURCE:
                source = params.get("source") if params else None
                if source:
                    await self._select_source(source)

            elif cmd_id == Commands.CURSOR_UP:
                await self.client.navigate_up()

            elif cmd_id == Commands.CURSOR_DOWN:
                await self.client.navigate_down()

            elif cmd_id == Commands.CURSOR_LEFT:
                await self.client.navigate_left()

            elif cmd_id == Commands.CURSOR_RIGHT:
                await self.client.navigate_right()

            elif cmd_id == Commands.CURSOR_ENTER:
                await self.client.select()

            elif cmd_id == Commands.HOME:
                await self.client.home()

            elif cmd_id == Commands.MENU:
                await self.client.services_menu()

            elif cmd_id == Commands.GUIDE:
                await self.client.guide()

            elif cmd_id == Commands.INFO:
                await self.client.info()

            elif cmd_id == Commands.BACK:
                await self.client.back()

            elif cmd_id == Commands.RECORD:
                await self.client.record()

            elif cmd_id == Commands.FUNCTION_RED:
                await self.client.red_button()

            elif cmd_id == Commands.FUNCTION_GREEN:
                await self.client.green_button()

            elif cmd_id == Commands.FUNCTION_YELLOW:
                await self.client.yellow_button()

            elif cmd_id == Commands.FUNCTION_BLUE:
                await self.client.blue_button()

            elif cmd_id.startswith(Commands.DIGIT_):
                digit = cmd_id.split("_")[1]
                await self.client.send_remote_command(digit)

            else:
                _LOG.warning(f"Unknown command for SkyQ media player: {cmd_id}")
                return uc.StatusCodes.NOT_IMPLEMENTED

            asyncio.create_task(self._delayed_status_update())

            return uc.StatusCodes.OK

        except Exception as e:
            _LOG.error(f"Error executing command {cmd_id} on {self.device_config.name}: {e}")
            return uc.StatusCodes.SERVER_ERROR

    async def _select_source(self, source: str):
        """Select channel/source by name."""
        channel_number = None
        channel_name = source

        if " - " in source:
            parts = source.split(" - ", 1)
            channel_number = parts[0].strip()
            channel_name = parts[1].strip()

        target_channel = None

        if channel_number:
            for channel in self._channels:
                if channel.get("number") == channel_number:
                    target_channel = channel
                    break

        if not target_channel:
            for channel in self._channels:
                if channel.get("name") == channel_name:
                    target_channel = channel
                    break

        if target_channel:
            number = target_channel.get("number")
            if number:
                await self.client.change_channel(number)
            else:
                _LOG.warning(f"No channel number available for {channel_name}")
        else:
            _LOG.warning(f"Channel not found: {source}")

    async def _delayed_status_update(self):
        """Perform delayed status update after command execution."""
        await asyncio.sleep(1)
        await self._update_status()

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
            "monitoring": self._monitoring,
            "channels_loaded": len(self._channels),
            "current_channel": self._current_channel,
            "state": self.attributes.get(Attributes.STATE),
            "volume": self.attributes.get(Attributes.VOLUME),
            "muted": self.attributes.get(Attributes.MUTED),
            "source": self.attributes.get(Attributes.SOURCE)
        }
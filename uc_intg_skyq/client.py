"""
SkyQ HTTP and TCP client for API communication.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

_LOG = logging.getLogger(__name__)


class SkyQClient:
    
    def __init__(self, host: str, rest_port: int = 9006, remote_port: int = 49160):
        self.host = host
        self.rest_port = rest_port
        self.remote_port = remote_port
        self._skyq_remote = None
        self._http_fallback = False  # Track if we're using HTTP fallback
        
        self._direct_tcp_commands = {"on", "off", "tvguide", "i", "boxoffice", "dismiss", 
                                   "backup", "tv", "radio", "interactive", "mysky", 
                                   "planner", "top", "subtitle", "audio", "announce", 
                                   "last", "list"}
        
    async def connect(self):
        """Connect to SkyQ device, trying pyskyqremote first, then HTTP fallback."""
        if not self._skyq_remote and not self._http_fallback:
            try:
                from pyskyqremote.skyq_remote import SkyQRemote
                self._skyq_remote = await asyncio.get_event_loop().run_in_executor(
                    None, SkyQRemote, self.host
                )
                if self._skyq_remote and self._skyq_remote.device_setup:
                    _LOG.info("pyskyqremote connection established successfully")
                    return True
                else:
                    _LOG.warning("pyskyqremote failed, switching to HTTP fallback")
                    self._skyq_remote = None
                    self._http_fallback = True
                    return True
            except Exception as e:
                _LOG.info(f"pyskyqremote initialization failed, using HTTP fallback: {e}")
                self._skyq_remote = None
                self._http_fallback = True
                return True
        return True
    
    async def disconnect(self):
        """Disconnect from SkyQ device."""
        self._skyq_remote = None
        # Keep _http_fallback state for reuse
    
    async def test_connection(self) -> bool:
        """Test connection to SkyQ device with consistent fallback logic."""
        try:
            # First test HTTP connectivity
            import aiohttp
            url = f"http://{self.host}:{self.rest_port}/as/services"
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            _LOG.info("HTTP connection successful, initializing pyskyqremote")
                            
                            # Try pyskyqremote initialization
                            try:
                                await self.connect()
                                if self._skyq_remote and self._skyq_remote.device_setup:
                                    _LOG.info("pyskyqremote initialization successful")
                                    return True
                                else:
                                    _LOG.info("pyskyqremote failed, but HTTP works - using fallback mode")
                                    self._http_fallback = True
                                    return True  # HTTP works, that's sufficient
                            except Exception as e:
                                _LOG.info(f"pyskyqremote initialization failed, using HTTP fallback: {e}")
                                self._http_fallback = True
                                return True  # HTTP works, that's sufficient
                        else:
                            _LOG.error(f"HTTP connection failed: {response.status}")
                            return False
                except asyncio.TimeoutError:
                    _LOG.error("HTTP connection timeout")
                    return False
                except Exception as e:
                    _LOG.error(f"HTTP connection error: {e}")
                    return False
                    
        except Exception as e:
            _LOG.error(f"Connection test failed: {e}")
            return False
    
    async def get_system_information(self) -> Optional[Dict[str, Any]]:
        """Get system information from SkyQ device."""
        try:
            # Try pyskyqremote first
            if self._skyq_remote and self._skyq_remote.device_setup:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.get_device_information
                )
            else:
                # HTTP fallback
                import aiohttp
                url = f"http://{self.host}:{self.rest_port}/as/system/information"
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                _LOG.debug(f"HTTP fallback system info: {data}")
                                return data
                            else:
                                # If /as/system/information fails, try fallback data
                                _LOG.warning("System information endpoint failed, using fallback")
                                return {
                                    "deviceName": f"SkyQ Device ({self.host})",
                                    "modelName": "SkyQ",
                                    "serialNumber": f"SIM-{self.host.replace('.', '')}",
                                    "hardwareModel": "SkyQ"
                                }
                    except Exception as e:
                        _LOG.warning(f"HTTP system info failed: {e}, using fallback")
                        return {
                            "deviceName": f"SkyQ Device ({self.host})",
                            "modelName": "SkyQ", 
                            "serialNumber": f"SIM-{self.host.replace('.', '')}",
                            "hardwareModel": "SkyQ"
                        }
        except Exception as e:
            _LOG.error(f"Failed to get system information: {e}")
            return {
                "deviceName": f"SkyQ Device ({self.host})",
                "modelName": "SkyQ",
                "serialNumber": f"SIM-{self.host.replace('.', '')}",
                "hardwareModel": "SkyQ"
            }
    
    async def get_services(self) -> Dict[str, Any]:
        """Get services/channels from SkyQ device."""
        try:
            # Try pyskyqremote first
            if self._skyq_remote and self._skyq_remote.device_setup:
                channels = await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.get_channel_list
                )
                return {"services": channels} if channels else {"services": []}
            else:
                # HTTP fallback
                import aiohttp
                url = f"http://{self.host}:{self.rest_port}/as/services"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            _LOG.debug(f"HTTP fallback services: {len(data.get('services', []))} channels")
                            return data
                        else:
                            return {"services": []}
        except Exception as e:
            _LOG.error(f"Failed to get services: {e}")
            return {"services": []}
    
    async def send_remote_command(self, command: str) -> bool:
        """Send remote control command to SkyQ device."""
        try:
            # FIXED: Check if command needs direct TCP (not supported by pyskyqremote)
            if command in self._direct_tcp_commands:
                _LOG.debug(f"Command '{command}' requires direct TCP, bypassing pyskyqremote")
                return await self._send_direct_tcp_command(command)
            
            # Try pyskyqremote first for supported commands
            if self._skyq_remote and self._skyq_remote.device_setup:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.press, command
                )
                _LOG.debug(f"pyskyqremote command {command}: success={result}")
                return result if result is not None else True
            else:
                # HTTP fallback - direct TCP
                return await self._send_direct_tcp_command(command)
                    
        except Exception as e:
            _LOG.error(f"Failed to send command {command}: {e}")
            return False
    
    async def _send_direct_tcp_command(self, command: str) -> bool:
        """Send command directly via TCP socket."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.remote_port),
                timeout=5.0
            )
            
            command_bytes = f"{command}\n".encode('utf-8')
            writer.write(command_bytes)
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(100), timeout=3.0)
            
            writer.close()
            await writer.wait_closed()
            
            response_text = response.decode('utf-8', errors='ignore').strip()
            success = response_text.startswith("SKY") or len(response_text) > 0
            
            _LOG.debug(f"Direct TCP command {command}: response='{response_text}', success={success}")
            return success
            
        except Exception as tcp_e:
            _LOG.error(f"Direct TCP command failed: {tcp_e}")
            return False
    
    async def send_key_sequence(self, commands: List[str], delay: float = 0.5) -> bool:
        """Send sequence of remote commands."""
        try:
            # Check if any commands need direct TCP
            needs_direct_tcp = any(cmd in self._direct_tcp_commands for cmd in commands)
            
            if needs_direct_tcp:
                # Send all commands via direct TCP for consistency
                for command in commands:
                    if not await self._send_direct_tcp_command(command):
                        return False
                    if delay > 0:
                        await asyncio.sleep(delay)
                return True
            
            # Try pyskyqremote first for supported commands
            if self._skyq_remote and self._skyq_remote.device_setup:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._skyq_remote.press, commands, delay
                )
                return result if result is not None else True
            else:
                # HTTP fallback - send commands individually
                for command in commands:
                    if not await self._send_direct_tcp_command(command):
                        return False
                    if delay > 0:
                        await asyncio.sleep(delay)
                return True
        except Exception as e:
            _LOG.error(f"Failed to send key sequence: {e}")
            return False
    
    def get_supported_commands(self) -> List[str]:
        """Get list of supported remote commands."""
        try:
            from pyskyqremote.const import COMMANDS
            pyskyq_commands = list(COMMANDS.keys())
            
            # FIXED: Combine pyskyqremote commands with direct TCP commands
            all_commands = list(set(pyskyq_commands + list(self._direct_tcp_commands)))
            return all_commands
        except ImportError:
            # Fallback command list including all discovered commands
            return [
                "power", "select", "backup", "dismiss", "channelup", "channeldown",
                "i", "sky", "help", "services", "search", "tvguide", "home", "up",
                "down", "left", "right", "red", "green", "yellow", "blue", "0", "1",
                "2", "3", "4", "5", "6", "7", "8", "9", "play", "pause", "stop",
                "record", "fastforward", "rewind", "boxoffice", "text", "on", "off",
                "tv", "radio", "interactive", "mysky", "planner", "top", "subtitle",
                "audio", "announce", "last", "list", "volumeup", "volumedown", "mute"
            ]
            
    @property
    def is_using_fallback(self) -> bool:
        """Check if client is using HTTP fallback mode."""
        return self._http_fallback
        
    @property
    def connection_type(self) -> str:
        """Get connection type description."""
        if self._skyq_remote and self._skyq_remote.device_setup:
            return "pyskyqremote + direct TCP"
        elif self._http_fallback:
            return "HTTP fallback + direct TCP"
        else:
            return "not connected"
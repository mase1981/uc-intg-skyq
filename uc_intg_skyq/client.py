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
        
        # Force TCP-only mode based on discovery results - this is the key fix
        self._force_tcp_only = True
        
    async def connect(self):
        """Connect to SkyQ device, using TCP-only mode based on discovery results."""
        if self._force_tcp_only:
            _LOG.info("Using TCP-only mode based on discovery results")
            self._http_fallback = True
            return True
            
        # Legacy pyskyqremote path (not used when _force_tcp_only=True)
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
                            _LOG.info("HTTP connection successful")
                            
                            # Test TCP connection as well
                            tcp_test = await self._test_tcp_connection()
                            if tcp_test:
                                _LOG.info("TCP connection test successful")
                                return True
                            else:
                                _LOG.warning("TCP connection test failed")
                                return False
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
    
    async def _test_tcp_connection(self) -> bool:
        """Test TCP remote control connectivity."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.remote_port),
                timeout=5.0
            )
            
            # Test with a simple command
            test_command = "up\n"
            writer.write(test_command.encode('utf-8'))
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(100), timeout=3.0)
            
            writer.close()
            await writer.wait_closed()
            
            response_text = response.decode('utf-8', errors='ignore').strip()
            success = response_text.startswith("SKY") or len(response_text) > 0
            
            _LOG.debug(f"TCP test command result: {success}, response: '{response_text}'")
            return success
            
        except Exception as e:
            _LOG.error(f"TCP connection test failed: {e}")
            return False
    
    async def get_system_information(self) -> Optional[Dict[str, Any]]:
        """Get system information from SkyQ device."""
        try:
            import aiohttp
            url = f"http://{self.host}:{self.rest_port}/as/system/information"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            _LOG.debug(f"HTTP system info retrieved successfully")
                            return data
                        else:
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
            # Use HTTP for services (more reliable)
            import aiohttp
            url = f"http://{self.host}:{self.rest_port}/as/services"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOG.debug(f"HTTP services: {len(data.get('services', []))} channels")
                        return data
                    else:
                        return {"services": []}
        except Exception as e:
            _LOG.error(f"Failed to get services: {e}")
            return {"services": []}
    
    async def send_remote_command(self, command: str) -> bool:
        """Send remote control command to SkyQ device."""
        _LOG.debug(f"Sending command '{command}' via direct TCP (forced mode)")
        return await self._send_direct_tcp_command(command)
    
    async def _send_direct_tcp_command(self, command: str) -> bool:
        """Send command directly via TCP socket with improved error handling."""
        try:
            # Create connection with explicit timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.remote_port),
                timeout=5.0
            )
            
            # Send command with newline (SkyQ protocol requirement)
            command_bytes = f"{command}\n".encode('utf-8')
            writer.write(command_bytes)
            await writer.drain()
            
            # Wait for response with timeout
            response = await asyncio.wait_for(reader.read(100), timeout=3.0)
            
            # Properly close connection
            writer.close()
            await writer.wait_closed()
            
            response_text = response.decode('utf-8', errors='ignore').strip()
            

            success = True
            
            _LOG.debug(f"Direct TCP command '{command}' sent successfully: '{response_text}'")
            return success
            
        except asyncio.TimeoutError:
            _LOG.error(f"TCP command '{command}' timed out")
            return False
        except ConnectionRefusedError:
            _LOG.error(f"TCP connection refused for command '{command}'")
            return False
        except Exception as e:
            _LOG.error(f"TCP command '{command}' failed: {type(e).__name__}: {e}")
            return False
    
    async def send_key_sequence(self, commands: List[str], delay: float = 0.5) -> bool:
        """Send sequence of remote commands via direct TCP."""
        try:
            _LOG.debug(f"Sending key sequence: {commands} with {delay}s delay")
            for i, command in enumerate(commands):
                if not await self._send_direct_tcp_command(command):
                    _LOG.warning(f"Key sequence failed at command {i}: {command}")
                    return False
                if delay > 0 and i < len(commands) - 1:  # Don't delay after last command
                    await asyncio.sleep(delay)
            return True
        except Exception as e:
            _LOG.error(f"Failed to send key sequence: {e}")
            return False
    
    def get_supported_commands(self) -> List[str]:
        """Get list of supported remote commands (all 60 from discovery)."""
        return [
            "power", "standby", "on", "off", "up", "down", "left", "right", 
            "select", "back", "home", "menu", "play", "pause", "stop", 
            "record", "fastforward", "rewind", "channelup", "guide", "info",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "red", "green", "yellow", "blue", "volumeup", "volumedown", "mute",
            "sky", "search", "text", "help", "services", "channeldown", 
            "tvguide", "i", "boxoffice", "dismiss", "backup", "tv", "radio", 
            "interactive", "mysky", "planner", "top", "subtitle", "audio", 
            "announce", "last", "list"
        ]
            
    @property
    def is_using_fallback(self) -> bool:
        """Check if client is using HTTP fallback mode."""
        return self._http_fallback or self._force_tcp_only
        
    @property
    def connection_type(self) -> str:
        """Get connection type description."""
        if self._force_tcp_only:
            return "TCP-only (discovery optimized)"
        elif self._skyq_remote and self._skyq_remote.device_setup:
            return "pyskyqremote + direct TCP"
        elif self._http_fallback:
            return "HTTP fallback + direct TCP"
        else:
            return "not connected"
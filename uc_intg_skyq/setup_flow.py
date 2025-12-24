"""SkyQ setup flow."""
import asyncio
import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig

_LOG = logging.getLogger(__name__)


class SkyQSetupFlow(BaseSetupFlow[SkyQDeviceConfig]):
    """Setup flow for SkyQ devices."""
    
    def get_manual_entry_form(self) -> RequestUserInput:
        """Get manual entry form for device configuration."""
        return RequestUserInput(
            {"en": "SkyQ Device Configuration"},
            [
                {
                    "id": "host",
                    "label": {"en": "Device IP Address"},
                    "description": {"en": "IP address of your SkyQ device (e.g., 192.168.1.100)"},
                    "field": {"text": {"value": "", "placeholder": "192.168.1.100"}},
                },
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "description": {"en": "Friendly name for this device (e.g., Living Room SkyQ)"},
                    "field": {"text": {"value": "", "placeholder": "Living Room SkyQ"}},
                },
                {
                    "id": "rest_port",
                    "label": {"en": "REST API Port (Advanced)"},
                    "description": {"en": "HTTP API port (default: 9006, alternative: 8080)"},
                    "field": {"number": {"value": 9006, "min": 1, "max": 65535}},
                },
            ],
        )
    
    async def query_device(self, input_values: dict[str, Any]) -> SkyQDeviceConfig:
        """Query device and create configuration."""
        _LOG.info("Processing device setup query")
        
        host = input_values.get("host", "").strip()
        name = input_values.get("name", "").strip() or f"SkyQ {host}"
        rest_port = int(input_values.get("rest_port", 9006))
        
        # Create identifier from sanitized host
        identifier = f"skyq_{host.replace('.', '_')}"
        
        _LOG.info("Testing connection to %s:%s", host, rest_port)
        
        # Test connection
        client = SkyQClient(host, rest_port)
        
        try:
            connected = await asyncio.wait_for(client.test_connection(), timeout=10.0)
            
            if not connected:
                # Try alternative port
                _LOG.info("Trying alternative port 8080")
                await client.disconnect()
                
                rest_port = 8080
                client = SkyQClient(host, rest_port)
                
                connected = await asyncio.wait_for(client.test_connection(), timeout=10.0)
                
                if not connected:
                    raise ValueError(f"Failed to connect to {host} on ports 9006 and 8080")
            
            # Get device info
            device_info = await client.get_system_information()
            
            model = "SkyQ"
            serial = ""
            
            if device_info:
                if isinstance(device_info, dict):
                    model = device_info.get("hardwareModel") or device_info.get("modelName", "SkyQ")
                    serial = device_info.get("serialNumber", "")
                else:
                    model = getattr(device_info, "hardwareModel", None) or getattr(device_info, "modelName", "SkyQ")
                    serial = getattr(device_info, "serialNumber", "")
            
            await client.disconnect()
            
            _LOG.info("Device configured successfully: %s (%s)", name, model)
            
            # Calculate remote port based on rest port
            if rest_port == 8080:
                remote_port = 49160
            elif rest_port >= 8080 and rest_port < 8090:
                remote_port = 49160 + (rest_port - 8080)
            else:
                remote_port = 49160
            
            return SkyQDeviceConfig(
                identifier=identifier,
                name=name,
                host=host,
                rest_port=rest_port,
                remote_port=remote_port,
                discovered_model=model,
                discovered_serial=serial,
                enable_voice=False,  # Always disabled
                enable_sensors=False,
            )
            
        except asyncio.TimeoutError:
            _LOG.error("Connection timeout to %s:%s", host, rest_port)
            raise ValueError(f"Connection timeout to {host}:{rest_port}") from None
        except Exception as err:
            _LOG.error("Connection test failed: %s", err)
            raise ValueError(f"Failed to connect: {err}") from err
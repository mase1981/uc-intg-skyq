"""
SkyQ device configuration management.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field

from ucapi_framework import BaseConfigManager


@dataclass
class SkyQDeviceConfig:
    """Configuration for a SkyQ device."""
    
    identifier: str
    name: str
    host: str
    rest_port: int = 9006
    remote_port: int = 49160
    
    # Discovered device information
    discovered_model: str = ""
    discovered_serial: str = ""
    discovered_software_version: str = ""
    discovered_has_voice: bool = False
    discovered_channels: list[dict] = field(default_factory=list)
    
    # Feature flags
    enable_voice: bool = False
    enable_sensors: bool = False


class SkyQConfigManager(BaseConfigManager[SkyQDeviceConfig]):
    """Configuration manager for SkyQ devices with JSON persistence."""
    pass
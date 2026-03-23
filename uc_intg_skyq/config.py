"""
Configuration for SkyQ integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field


@dataclass
class SkyQDeviceConfig:
    """SkyQ device configuration."""

    identifier: str
    name: str
    host: str
    rest_port: int = 9006
    remote_port: int = 49160

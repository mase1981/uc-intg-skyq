"""
SkyQ Integration Driver.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.device import SkyQDevice
from uc_intg_skyq.media_player import SkyQMediaPlayer
from uc_intg_skyq.remote import SkyQRemote
from uc_intg_skyq.sensor import (
    SkyQChannelSensor,
    SkyQConnectionTypeSensor,
    SkyQIPAddressSensor,
    SkyQModelSensor,
)

_LOG = logging.getLogger(__name__)


class SkyQDriver(BaseIntegrationDriver[SkyQDevice, SkyQDeviceConfig]):
    """Integration driver for SkyQ satellite boxes."""

    def __init__(self) -> None:
        super().__init__(
            device_class=SkyQDevice,
            entity_classes=[
                SkyQMediaPlayer,
                SkyQRemote,
                SkyQModelSensor,
                SkyQIPAddressSensor,
                SkyQChannelSensor,
                SkyQConnectionTypeSensor,
            ],
            driver_id="uc_intg_skyq",
            require_connection_before_registry=True,
        )

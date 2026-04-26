"""
SkyQ Sensor entities.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import DeviceState
from uc_intg_skyq.device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQModelSensor(SensorEntity):
    """Sensor showing the SkyQ device model."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"sensor.skyq_{device_config.identifier}.model"

        super().__init__(
            entity_id,
            f"{device_config.name} Model",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == DeviceState.UNAVAILABLE:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.model,
        })


class SkyQIPAddressSensor(SensorEntity):
    """Sensor showing the SkyQ device IP address."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"sensor.skyq_{device_config.identifier}.ip"

        super().__init__(
            entity_id,
            f"{device_config.name} IP Address",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == DeviceState.UNAVAILABLE:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.ip_address,
        })


class SkyQChannelSensor(SensorEntity):
    """Sensor showing the current channel."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"sensor.skyq_{device_config.identifier}.channel"

        super().__init__(
            entity_id,
            f"{device_config.name} Channel",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == DeviceState.UNAVAILABLE:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.current_channel or "Unknown",
        })


class SkyQConnectionTypeSensor(SensorEntity):
    """Sensor showing the connection type (pyskyqremote or HTTP fallback)."""

    def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
        self._device = device
        entity_id = f"sensor.skyq_{device_config.identifier}.connection"

        super().__init__(
            entity_id,
            f"{device_config.name} Connection",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == DeviceState.UNAVAILABLE:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.connection_type,
        })


def _make_simple_sensor(suffix: str, label: str, device_attr: str):
    """Build a SensorEntity subclass that surfaces a single SkyQDevice property."""

    class _SimpleDeviceSensor(SensorEntity):
        def __init__(self, device_config: SkyQDeviceConfig, device: SkyQDevice) -> None:
            self._device = device
            entity_id = f"sensor.skyq_{device_config.identifier}.{suffix}"
            super().__init__(
                entity_id,
                f"{device_config.name} {label}",
                features=[],
                attributes={
                    sensor.Attributes.STATE: sensor.States.ON,
                    sensor.Attributes.VALUE: "",
                },
                device_class=sensor.DeviceClasses.CUSTOM,
                options={sensor.Options.CUSTOM_UNIT: ""},
            )
            self.subscribe_to_device(device)

        async def sync_state(self) -> None:
            if self._device.state == DeviceState.UNAVAILABLE:
                self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
                return
            self.update({
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: getattr(self._device, device_attr, "") or "",
            })

    _SimpleDeviceSensor.__name__ = f"SkyQ{label.replace(' ', '')}Sensor"
    _SimpleDeviceSensor.__qualname__ = _SimpleDeviceSensor.__name__
    return _SimpleDeviceSensor


SkyQSerialSensor = _make_simple_sensor("serial", "Serial", "serial_number")
SkyQSoftwareVersionSensor = _make_simple_sensor("software_version", "Software Version", "software_version")
SkyQHdrCapableSensor = _make_simple_sensor("hdr", "HDR Capable", "hdr_capable")
SkyQUhdCapableSensor = _make_simple_sensor("uhd", "UHD Capable", "uhd_capable")
SkyQUptimeSensor = _make_simple_sensor("uptime", "Uptime", "system_uptime")
SkyQMediaKindSensor = _make_simple_sensor("media_kind", "Media Kind", "media_kind")

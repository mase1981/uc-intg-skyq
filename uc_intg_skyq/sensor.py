"""SkyQ Sensor entities for channel and program information."""
import logging

from ucapi import EntityTypes, sensor
from ucapi_framework import DeviceEvents

from .config import SkyQDeviceConfig
from .device import SkyQDevice

_LOG = logging.getLogger(__name__)


class SkyQChannelSensor(sensor.Sensor):
    """Sensor for current channel."""

    def __init__(self, config: SkyQDeviceConfig, device: SkyQDevice):
        """Initialize channel sensor."""
        self._config = config
        self._device = device
        
        entity_id = f"{EntityTypes.SENSOR}.{config.identifier}.channel"
        
        attributes = {
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: "",
        }
        
        super().__init__(
            identifier=entity_id,
            name=f"{config.name} Channel",
            features=[],
            attributes=attributes,
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        
        # Subscribe to device events
        device.events.on(DeviceEvents.UPDATE, self.on_device_update)
        
        _LOG.debug("Channel sensor initialized: %s", entity_id)

    def on_device_update(self, device_id: str, value: str) -> None:
        """Handle device updates."""
        # Check if this is a channel update
        if device_id == f"{self._config.identifier}.channel":
            self.attributes[sensor.Attributes.VALUE] = value or ""


class SkyQProgramSensor(sensor.Sensor):
    """Sensor for current program."""

    def __init__(self, config: SkyQDeviceConfig, device: SkyQDevice):
        """Initialize program sensor."""
        self._config = config
        self._device = device
        
        entity_id = f"{EntityTypes.SENSOR}.{config.identifier}.program"
        
        attributes = {
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: "",
        }
        
        super().__init__(
            identifier=entity_id,
            name=f"{config.name} Program",
            features=[],
            attributes=attributes,
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        
        # Subscribe to device events
        device.events.on(DeviceEvents.UPDATE, self.on_device_update)
        
        _LOG.debug("Program sensor initialized: %s", entity_id)

    def on_device_update(self, device_id: str, value: str) -> None:
        """Handle device updates."""
        # Check if this is a program update
        if device_id == f"{self._config.identifier}.program":
            self.attributes[sensor.Attributes.VALUE] = value or ""
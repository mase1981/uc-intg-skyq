"""
Configuration management for SkyQ integration.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path

_LOG = logging.getLogger(__name__)


@dataclass
class SkyQDeviceConfig:
    """Configuration for a single SkyQ device."""

    device_id: str
    name: str
    host: str
    rest_port: int = 9006
    remote_port: int = 49160
    enabled: bool = True

    create_media_player: bool = True
    create_remote: bool = True

    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 5

    status_update_interval: int = 5
    channel_update_interval: int = 30
    recording_update_interval: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkyQDeviceConfig':
        """Create from dictionary."""
        return cls(**data)

    def validate(self) -> List[str]:
        """
        Validate device configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.device_id:
            errors.append("Device ID is required")

        if not self.name:
            errors.append("Device name is required")

        if not self.host:
            errors.append("Host/IP address is required")

        if not (1 <= self.rest_port <= 65535):
            errors.append(f"Invalid REST port: {self.rest_port}")

        if not (1 <= self.remote_port <= 65535):
            errors.append(f"Invalid remote port: {self.remote_port}")

        if self.timeout < 1:
            errors.append("Timeout must be at least 1 second")

        if self.retry_attempts < 0:
            errors.append("Retry attempts cannot be negative")

        if self.status_update_interval < 1:
            errors.append("Status update interval must be at least 1 second")

        return errors


@dataclass
class SkyQIntegrationConfig:
    """Main integration configuration."""

    devices: List[SkyQDeviceConfig]

    integration_name: str = "SkyQ Integration"
    log_level: str = "INFO"

    enable_websocket_monitoring: bool = True
    websocket_reconnect_delay: int = 10
    max_concurrent_requests: int = 10

    entity_name_format: str = "{device_name}"
    remote_entity_suffix: str = " Remote"

    enable_pvr_management: bool = True
    enable_channel_switching: bool = True
    enable_power_control: bool = True
    enable_recording_scheduling: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['devices'] = [device.to_dict() for device in self.devices]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkyQIntegrationConfig':
        """Create from dictionary."""
        devices_data = data.pop('devices', [])
        devices = [SkyQDeviceConfig.from_dict(dev) for dev in devices_data]
        return cls(devices=devices, **data)

    def validate(self) -> List[str]:
        """
        Validate integration configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.devices:
            errors.append("At least one device must be configured")

        device_ids = set()
        device_names = set()

        for i, device in enumerate(self.devices):
            device_errors = device.validate()
            for error in device_errors:
                errors.append(f"Device {i+1}: {error}")

            if device.device_id in device_ids:
                errors.append(f"Duplicate device ID: {device.device_id}")
            device_ids.add(device.device_id)

            if device.name in device_names:
                errors.append(f"Duplicate device name: {device.name}")
            device_names.add(device.name)

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")

        return errors

    def get_device_by_id(self, device_id: str) -> Optional[SkyQDeviceConfig]:
        """Get device configuration by ID."""
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    def get_device_by_name(self, name: str) -> Optional[SkyQDeviceConfig]:
        """Get device configuration by name."""
        for device in self.devices:
            if device.name == name:
                return device
        return None

    def add_device(self, device: SkyQDeviceConfig) -> bool:
        """
        Add device to configuration.
        
        Returns:
            True if added successfully, False if ID/name already exists
        """
        if self.get_device_by_id(device.device_id):
            return False
        if self.get_device_by_name(device.name):
            return False

        self.devices.append(device)
        return True

    def remove_device(self, device_id: str) -> bool:
        """
        Remove device from configuration.
        
        Returns:
            True if removed, False if not found
        """
        for i, device in enumerate(self.devices):
            if device.device_id == device_id:
                del self.devices[i]
                return True
        return False

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update device configuration.
        
        Returns:
            True if updated and saved successfully
        """
        device = self.get_device_by_id(device_id)
        if not device:
            return False

        for key, value in updates.items():
            if hasattr(device, key):
                setattr(device, key, value)

        return True


class SkyQConfigManager:
    """Manages SkyQ integration configuration file operations."""

    CONFIG_FILE_NAME = "config.json"

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store config file
        """
        if config_dir is None:
            config_dir = os.getenv("UC_CONFIG_HOME", ".")
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, self.CONFIG_FILE_NAME)
        self._config: Optional[SkyQIntegrationConfig] = None

        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        _LOG.debug(f"Config manager initialized with file: {self.config_file}")

    @property
    def config(self) -> SkyQIntegrationConfig:
        """Get current configuration (loads if not cached)."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> SkyQIntegrationConfig:
        """
        Load configuration from config file.
        
        Returns:
            Loaded configuration or default if file doesn't exist
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                config = SkyQIntegrationConfig.from_dict(data)

                errors = config.validate()
                if errors:
                    _LOG.warning(f"Configuration validation errors: {errors}")

                _LOG.info(f"Loaded configuration for {len(config.devices)} devices from {self.config_file}")
                return config
            else:
                _LOG.info(f"No configuration file found at {self.config_file}, creating default")
                return self._create_default_config()
        except Exception as e:
            _LOG.error(f"Failed to load configuration from {self.config_file}: {e}")
            return self._create_default_config()

    def save_config(self, config: Optional[SkyQIntegrationConfig] = None) -> bool:
        """
        Save configuration to config file.
        
        Args:
            config: Configuration to save (uses current if None)
            
        Returns:
            True if saved successfully
        """
        if config is None:
            config = self.config

        try:
            errors = config.validate()
            if errors:
                _LOG.error(f"Cannot save invalid configuration: {errors}")
                return False

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, default=str)

            self._config = config

            _LOG.info(f"Saved configuration for {len(config.devices)} devices to {self.config_file}")
            return True

        except Exception as e:
            _LOG.error(f"Failed to save configuration to {self.config_file}: {e}")
            return False

    def _create_default_config(self) -> SkyQIntegrationConfig:
        """Create default configuration."""
        return SkyQIntegrationConfig(
            devices=[],
            integration_name="SkyQ Integration",
            log_level="INFO"
        )

    def backup_config(self) -> bool:
        """
        Create backup of current configuration.
        
        Returns:
            True if backup created successfully
        """
        if not os.path.exists(self.config_file):
            return False

        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.config_dir, f"config_backup_{timestamp}.json")

            shutil.copy2(self.config_file, backup_file)
            _LOG.info(f"Configuration backed up to: {backup_file}")
            return True

        except Exception as e:
            _LOG.error(f"Failed to backup configuration: {e}")
            return False

    def restore_config(self, backup_file: str) -> bool:
        """
        Restore configuration from backup file.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if restored successfully
        """
        try:
            if not os.path.exists(backup_file):
                _LOG.error(f"Backup file not found: {backup_file}")
                return False

            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = SkyQIntegrationConfig.from_dict(data)
            errors = config.validate()
            if errors:
                _LOG.error(f"Invalid backup configuration: {errors}")
                return False

            return self.save_config(config)

        except Exception as e:
            _LOG.error(f"Failed to restore configuration: {e}")
            return False

    def add_device_config(self, device_config: SkyQDeviceConfig) -> bool:
        """
        Add device to configuration and save.
        
        Returns:
            True if added and saved successfully
        """
        if self.config.add_device(device_config):
            return self.save_config()
        return False

    def remove_device_config(self, device_id: str) -> bool:
        """
        Remove device from configuration and save.
        
        Returns:
            True if removed and saved successfully
        """
        if self.config.remove_device(device_id):
            return self.save_config()
        return False

    def update_device_config(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update device configuration and save.
        
        Returns:
            True if updated and saved successfully
        """
        if self.config.update_device(device_id, updates):
            return self.save_config()
        return False

    def get_device_configs(self) -> List[SkyQDeviceConfig]:
        """Get list of all device configurations."""
        return self.config.devices.copy()

    def get_enabled_device_configs(self) -> List[SkyQDeviceConfig]:
        """Get list of enabled device configurations."""
        return [device for device in self.config.devices if device.enabled]

    def reset_config(self) -> bool:
        """
        Reset configuration to defaults and save.
        
        Returns:
            True if reset successfully
        """
        default_config = self._create_default_config()
        return self.save_config(default_config)

    def delete_config(self) -> bool:
        """
        Delete the configuration file.
        
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                _LOG.info(f"Deleted configuration file: {self.config_file}")
                self._config = None
                return True
            else:
                _LOG.info("No configuration file to delete")
                return True
        except Exception as e:
            _LOG.error(f"Failed to delete configuration file: {e}")
            return False

    def export_config(self, export_file: str) -> bool:
        """
        Export configuration to specified file.
        
        Args:
            export_file: Path to export file
            
        Returns:
            True if exported successfully
        """
        try:
            export_path = os.path.dirname(export_file)
            if export_path:
                os.makedirs(export_path, exist_ok=True)

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, default=str)

            _LOG.info(f"Configuration exported to: {export_file}")
            return True

        except Exception as e:
            _LOG.error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, import_file: str) -> bool:
        """
        Import configuration from specified file.
        
        Args:
            import_file: Path to import file
            
        Returns:
            True if imported successfully
        """
        try:
            if not os.path.exists(import_file):
                _LOG.error(f"Import file not found: {import_file}")
                return False

            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = SkyQIntegrationConfig.from_dict(data)
            errors = config.validate()
            if errors:
                _LOG.error(f"Invalid import configuration: {errors}")
                return False

            return self.save_config(config)

        except Exception as e:
            _LOG.error(f"Failed to import configuration: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of current configuration.
        
        Returns:
            Configuration summary for display/logging
        """
        config = self.config
        return {
            'total_devices': len(config.devices),
            'enabled_devices': len([d for d in config.devices if d.enabled]),
            'integration_name': config.integration_name,
            'log_level': config.log_level,
            'config_file': self.config_file,
            'config_exists': os.path.exists(self.config_file),
            'last_modified': os.path.getmtime(self.config_file) if os.path.exists(self.config_file) else None
        }

    def get_config_file_path(self) -> str:
        """Get the full path to the config file."""
        return os.path.abspath(self.config_file)

    def is_configured(self) -> bool:
        """Check if integration has devices configured."""
        return len(self.config.devices) > 0
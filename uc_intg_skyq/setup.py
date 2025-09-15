"""
Setup flow for SkyQ integration.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import logging
from typing import Any, Dict, List

import ucapi.api_definitions as uc
from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig, SkyQConfigManager

_LOG = logging.getLogger(__name__)


class SkyQSetupHandler:
    """Handles SkyQ integration setup flow."""

    def __init__(self, config_manager: SkyQConfigManager):
        """
        Initialize setup handler.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._setup_state = {}

    async def handle_setup_request(self, setup_request: uc.SetupDriver) -> uc.SetupAction:
        """
        Handle setup request from Remote Two.
        
        Args:
            setup_request: Setup request from Remote Two
            
        Returns:
            Next setup action to perform
        """
        _LOG.info("Processing SkyQ integration setup request")

        if isinstance(setup_request, uc.DriverSetupRequest):
            return await self._handle_initial_setup(setup_request)
        elif isinstance(setup_request, uc.UserDataResponse):
            return await self._handle_user_input(setup_request)
        elif isinstance(setup_request, uc.UserConfirmationResponse):
            return await self._handle_user_confirmation(setup_request)
        elif isinstance(setup_request, uc.AbortDriverSetup):
            return await self._handle_setup_abort(setup_request)
        else:
            _LOG.error(f"Unknown setup request type: {type(setup_request)}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_initial_setup(self, request: uc.DriverSetupRequest) -> uc.SetupAction:
        """Handle initial setup request."""
        _LOG.info("Starting SkyQ integration setup")

        is_reconfigure = request.reconfigure

        if is_reconfigure:
            _LOG.info("Reconfiguring existing SkyQ integration")
            existing_devices = self.config_manager.get_device_configs()
            self._setup_state["existing_devices"] = len(existing_devices)
        else:
            _LOG.info("Setting up new SkyQ integration")
            self._setup_state["existing_devices"] = 0

        return await self._request_device_count()

    async def _request_device_count(self) -> uc.RequestUserInput:
        """Request number of SkyQ devices to configure."""
        settings = [
            {
                "id": "device_count",
                "label": {
                    "en": "Number of SkyQ Devices",
                    "de": "Anzahl der SkyQ-Geräte"
                },
                "field": {
                    "select": {
                        "options": [
                            {"id": "1", "label": {"en": "1 Device", "de": "1 Gerät"}},
                            {"id": "2", "label": {"en": "2 Devices", "de": "2 Geräte"}},
                            {"id": "3", "label": {"en": "3 Devices", "de": "3 Geräte"}},
                            {"id": "4", "label": {"en": "4 Devices", "de": "4 Geräte"}},
                            {"id": "5", "label": {"en": "5 Devices", "de": "5 Geräte"}},
                            {"id": "6", "label": {"en": "6 Devices", "de": "6 Geräte"}},
                            {"id": "7", "label": {"en": "7 Devices", "de": "7 Geräte"}},
                            {"id": "8", "label": {"en": "8 Devices", "de": "8 Geräte"}},
                            {"id": "9", "label": {"en": "9 Devices", "de": "9 Geräte"}},
                            {"id": "10", "label": {"en": "10 Devices", "de": "10 Geräte"}}
                        ]
                    }
                }
            }
        ]

        title = {
            "en": "SkyQ Multi-Device Setup",
            "de": "SkyQ Multi-Gerät-Setup"
        }

        return uc.RequestUserInput(title, settings)

    async def _handle_user_input(self, user_input: uc.UserDataResponse) -> uc.SetupAction:
        """Handle user input response."""
        input_values = user_input.input_values

        if "device_count" in input_values:
            return await self._handle_device_count_input(input_values)
        elif "device_1_ip" in input_values or any(k.endswith("_ip") for k in input_values.keys()):
            return await self._handle_device_configuration_input(input_values)
        else:
            _LOG.error(f"Unexpected user input: {input_values}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_device_count_input(self, input_values: Dict[str, str]) -> uc.SetupAction:
        """Handle device count selection."""
        try:
            device_count = int(input_values["device_count"])
            self._setup_state["device_count"] = device_count

            _LOG.info(f"User selected {device_count} SkyQ devices")

            return await self._request_device_configurations(device_count)

        except (ValueError, KeyError) as e:
            _LOG.error(f"Invalid device count input: {e}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _request_device_configurations(self, device_count: int) -> uc.RequestUserInput:
        """Request configuration for all devices."""
        settings = []

        for i in range(1, device_count + 1):
            settings.append({
                "id": f"device_{i}_ip",
                "label": {
                    "en": f"Device {i} IP Address",
                    "de": f"Gerät {i} IP-Adresse"
                },
                "field": {
                    "text": {
                        "placeholder": "192.168.1.100 or 192.168.1.100:9006"
                    }
                }
            })

            settings.append({
                "id": f"device_{i}_name",
                "label": {
                    "en": f"Device {i} Name",
                    "de": f"Gerät {i} Name"
                },
                "field": {
                    "text": {
                        "placeholder": f"Living Room SkyQ" if i == 1 else f"SkyQ Device {i}"
                    }
                }
            })

        title = {
            "en": "Device Configuration",
            "de": "Gerätekonfiguration"
        }

        return uc.RequestUserInput(title, settings)

    async def _handle_device_configuration_input(self, input_values: Dict[str, str]) -> uc.SetupAction:
        """Handle device configuration input and test connections."""
        device_count = self._setup_state.get("device_count", 1)

        device_configs = []
        for i in range(1, device_count + 1):
            ip_key = f"device_{i}_ip"
            name_key = f"device_{i}_name"

            if ip_key not in input_values:
                _LOG.error(f"Missing IP for device {i}")
                return uc.SetupError(uc.IntegrationSetupError.OTHER)

            ip_input = input_values[ip_key].strip()
            if ":" in ip_input:
                host, port_str = ip_input.split(":", 1)
                try:
                    rest_port = int(port_str)
                except ValueError:
                    _LOG.error(f"Invalid port in IP address: {ip_input}")
                    return uc.SetupError(uc.IntegrationSetupError.OTHER)
            else:
                host = ip_input
                rest_port = 9006

            name = input_values.get(name_key, f"SkyQ Device {i}").strip()
            if not name:
                name = f"SkyQ Device {i}"

            device_config = SkyQDeviceConfig(
                device_id=f"skyq_{i}",
                name=name,
                host=host,
                rest_port=rest_port
            )

            device_configs.append(device_config)

        self._setup_state["device_configs"] = device_configs

        return await self._test_device_connections(device_configs)

    async def _test_device_connections(self, device_configs: List[SkyQDeviceConfig]) -> uc.SetupAction:
        """Test connections to all configured devices."""
        _LOG.info(f"Testing connections to {len(device_configs)} SkyQ devices")

        test_results = []

        async def test_device(config: SkyQDeviceConfig) -> Dict[str, Any]:
            """Test connection to a single device."""
            try:
                async with SkyQClient(config.host, config.rest_port) as client:
                    is_connected = await client.test_connection()

                    if is_connected:
                        system_info = await client.get_system_information()
                        return {
                            "config": config,
                            "success": True,
                            "device_info": system_info,
                            "error": None
                        }
                    else:
                        return {
                            "config": config,
                            "success": False,
                            "device_info": None,
                            "error": "Connection test failed"
                        }
            except Exception as e:
                _LOG.warning(f"Failed to connect to {config.host}:{config.rest_port}: {e}")
                return {
                    "config": config,
                    "success": False,
                    "device_info": None,
                    "error": str(e)
                }

        test_tasks = [test_device(config) for config in device_configs]
        test_results = await asyncio.gather(*test_tasks)

        successful_devices = [result for result in test_results if result["success"]]
        failed_devices = [result for result in test_results if not result["success"]]

        _LOG.info(f"Connection test results: {len(successful_devices)} successful, {len(failed_devices)} failed")

        self._setup_state["test_results"] = test_results

        if len(successful_devices) == 0:
            return await self._show_connection_error(failed_devices)
        elif len(failed_devices) == 0:
            return await self._show_success_confirmation(successful_devices)
        else:
            return await self._show_partial_success_confirmation(successful_devices, failed_devices)

    async def _show_connection_error(self, failed_devices: List[Dict[str, Any]]) -> uc.SetupError:
        """Show error when all device connections failed."""
        _LOG.error("All SkyQ device connections failed")

        for result in failed_devices:
            config = result["config"]
            error = result["error"]
            _LOG.error(f"Device {config.name} ({config.host}:{config.rest_port}): {error}")

        return uc.SetupError(uc.IntegrationSetupError.CONNECTION_REFUSED)

    async def _show_success_confirmation(self, successful_devices: List[Dict[str, Any]]) -> uc.RequestUserConfirmation:
        """Show confirmation when all devices connected successfully."""
        device_count = len(successful_devices)

        device_list = []
        for result in successful_devices:
            config = result["config"]
            device_info = result.get("device_info", {})
            model = device_info.get("modelName", "SkyQ Box")
            device_list.append(f"• {config.name} ({config.host}) - {model}")

        header_text = {
            "en": f"Successfully connected to all {device_count} SkyQ devices:",
            "de": f"Erfolgreich mit allen {device_count} SkyQ-Geräten verbunden:"
        }

        device_text = "\n".join(device_list)

        footer_text = {
            "en": "Click Continue to complete the setup and create entities for all devices.",
            "de": "Klicken Sie auf Weiter, um die Einrichtung abzuschließen und Entitäten für alle Geräte zu erstellen."
        }

        title = {
            "en": "Setup Complete",
            "de": "Setup abgeschlossen"
        }

        message = f"{header_text['en']}\n\n{device_text}\n\n{footer_text['en']}"

        return uc.RequestUserConfirmation(
            title=title,
            header=header_text,
            footer=footer_text
        )

    async def _show_partial_success_confirmation(self, successful_devices: List[Dict[str, Any]],
                                               failed_devices: List[Dict[str, Any]]) -> uc.RequestUserConfirmation:
        """Show confirmation when some devices failed to connect."""
        success_count = len(successful_devices)
        fail_count = len(failed_devices)

        success_list = []
        for result in successful_devices:
            config = result["config"]
            device_info = result.get("device_info", {})
            model = device_info.get("modelName", "SkyQ Box")
            success_list.append(f"✅ {config.name} ({config.host}) - {model}")

        fail_list = []
        for result in failed_devices:
            config = result["config"]
            error = result["error"]
            fail_list.append(f"❌ {config.name} ({config.host}) - {error}")

        header_text = {
            "en": f"Connected to {success_count} of {success_count + fail_count} SkyQ devices:",
            "de": f"Verbunden mit {success_count} von {success_count + fail_count} SkyQ-Geräten:"
        }

        message_parts = []
        message_parts.append("Successful connections:")
        message_parts.extend(success_list)
        message_parts.append("\nFailed connections:")
        message_parts.extend(fail_list)

        device_text = "\n".join(message_parts)

        footer_text = {
            "en": "Continue to set up the working devices. You can add failed devices later.",
            "de": "Fahren Sie fort, um die funktionierenden Geräte einzurichten. Fehlgeschlagene Geräte können später hinzugefügt werden."
        }

        title = {
            "en": "Partial Setup Success",
            "de": "Teilweise erfolgreiche Einrichtung"
        }

        return uc.RequestUserConfirmation(
            title=title,
            header=header_text,
            footer=footer_text
        )

    async def _handle_user_confirmation(self, confirmation: uc.UserConfirmationResponse) -> uc.SetupAction:
        """Handle user confirmation response."""
        if confirmation.confirm:
            return await self._complete_setup()
        else:
            _LOG.info("User cancelled setup")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _complete_setup(self) -> uc.SetupComplete:
        """Complete the setup process."""
        _LOG.info("Completing SkyQ integration setup")

        test_results = self._setup_state.get("test_results", [])
        successful_devices = [result["config"] for result in test_results if result["success"]]

        if not successful_devices:
            _LOG.error("No successful devices to set up")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

        try:
            for device_config in successful_devices:
                self.config_manager.add_device_config(device_config)

            _LOG.info(f"Setup completed successfully for {len(successful_devices)} devices")

            self._setup_state.clear()

            return uc.SetupComplete()

        except Exception as e:
            _LOG.error(f"Failed to save configuration: {e}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_setup_abort(self, abort: uc.AbortDriverSetup) -> uc.SetupError:
        """Handle setup abort request."""
        _LOG.warning(f"Setup aborted: {abort.error}")

        self._setup_state.clear()

        return uc.SetupError(abort.error)
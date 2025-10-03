"""
SkyQ integration driver for Unfolded Circle Remote

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import ucapi
from ucapi import DeviceStates, Events, IntegrationSetupError, SetupComplete, SetupError, RequestUserInput, UserDataResponse

from uc_intg_skyq.config import SkyQConfigManager, SkyQDeviceConfig
from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.media_player import SkyQMediaPlayer
from uc_intg_skyq.remote import SkyQRemote

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOG = logging.getLogger(__name__)

api: Optional[ucapi.IntegrationAPI] = None
config_manager: Optional[SkyQConfigManager] = None
clients: Dict[str, SkyQClient] = {}
media_players: Dict[str, SkyQMediaPlayer] = {}
remotes: Dict[str, SkyQRemote] = {}

_entities_ready: bool = False
_initialization_lock: asyncio.Lock = asyncio.Lock()

setup_state = {"step": "initial", "device_count": 1, "devices_data": []}


async def _initialize_entities():
    global config_manager, api, clients, media_players, remotes, _entities_ready

    async with _initialization_lock:
        if _entities_ready:
            _LOG.debug("Entities already initialized, skipping")
            return

        if not config_manager or not config_manager.config.devices:
            _LOG.info("Integration not configured, skipping entity initialization")
            return

        _LOG.info("Initializing Media Player + Remote entities for %d configured devices", len(config_manager.config.devices))
        await api.set_device_state(DeviceStates.CONNECTING)

        connected_devices = 0

        api.available_entities.clear()
        clients.clear()
        media_players.clear()
        remotes.clear()

        for device_config in config_manager.config.devices:
            if not device_config.enabled:
                _LOG.info("Skipping disabled device: %s", device_config.name)
                continue

            _LOG.info("Connecting to SkyQ device: %s at %s:%s", device_config.name, device_config.host, device_config.rest_port)

            try:
                client = SkyQClient(device_config.host, device_config.rest_port, device_config.remote_port)

                if not await client.test_connection():
                    _LOG.error("Failed to connect to SkyQ device %s at %s:%s", device_config.name, device_config.host, device_config.rest_port)
                    await client.disconnect()
                    continue

                device_info = await client.get_system_information()
                if device_info:
                    try:
                        if hasattr(device_info, 'modelName'):
                            device_model = getattr(device_info, 'modelName', 'SkyQ') or getattr(device_info, 'hardwareModel', 'SkyQ')
                            device_hostname = getattr(device_info, 'deviceName', device_config.name) or device_config.name
                        else:
                            device_model = device_info.get('modelName', 'SkyQ') or device_info.get('hardwareModel', 'SkyQ')
                            device_hostname = device_info.get('deviceName', device_config.name) or device_config.name
                        _LOG.info("Connected to SkyQ %s: %s", device_model, device_hostname)
                    except Exception as info_error:
                        _LOG.warning("Error parsing device info: %s", info_error)
                        device_model = "SkyQ"
                        device_hostname = device_config.name
                else:
                    _LOG.warning("Could not get system info, but connection successful")
                    device_model = "SkyQ"
                    device_hostname = device_config.name

                # Create media player entity
                media_player_id = f"skyq_media_{device_config.device_id}"
                media_player = SkyQMediaPlayer(device_config, client)
                media_player.identifier = media_player_id
                media_player._integration_api = api

                # Create remote entity
                remote_id = f"skyq_remote_{device_config.device_id}"
                remote = SkyQRemote(device_config, client)
                remote.identifier = remote_id
                remote._integration_api = api

                # Initialize both entities
                media_player_success = await media_player.initialize()
                remote_success = await remote.initialize()

                if media_player_success and remote_success:
                    clients[device_config.device_id] = client
                    media_players[device_config.device_id] = media_player
                    remotes[device_config.device_id] = remote

                    # Add both entities
                    api.available_entities.add(media_player)
                    api.available_entities.add(remote)

                    connected_devices += 1
                    _LOG.info("Successfully setup Media Player + Remote for device: %s", device_config.name)
                else:
                    _LOG.error("Failed to initialize entities for device: %s", device_config.name)
                    if media_player_success:
                        await media_player.shutdown()
                    if remote_success:
                        await remote.shutdown()
                    await client.disconnect()

            except Exception as e:
                _LOG.error("Failed to setup device %s: %s", device_config.name, e, exc_info=True)
                continue

        if connected_devices > 0:
            _entities_ready = True
            await api.set_device_state(DeviceStates.CONNECTED)
            _LOG.info("SkyQ integration completed - %d/%d devices connected", connected_devices, len(config_manager.config.devices))
        else:
            _entities_ready = False
            await api.set_device_state(DeviceStates.ERROR)
            _LOG.error("No devices could be connected during initialization")


async def setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    global config_manager, _entities_ready, setup_state

    if isinstance(msg, ucapi.DriverSetupRequest):
        device_count = int(msg.setup_data.get("device_count", 1))

        if device_count == 1:
            return await _handle_single_device_setup(msg.setup_data)
        else:
            setup_state = {"step": "collect_ips", "device_count": device_count, "devices_data": []}
            return await _request_device_ips(device_count)

    elif isinstance(msg, ucapi.UserDataResponse):
        if setup_state["step"] == "collect_ips":
            return await _handle_device_ips_collection(msg.input_values)

    return SetupError(IntegrationSetupError.OTHER)


async def _handle_single_device_setup(setup_data: Dict[str, Any]) -> ucapi.SetupAction:
    """Handle single device setup - SIMPLIFIED and SAFE."""
    host_input = setup_data.get("host")
    if not host_input:
        _LOG.error("No host provided in setup data")
        return SetupError(IntegrationSetupError.OTHER)

    try:
        if ':' in host_input:
            host, port_str = host_input.split(':', 1)
            rest_port = int(port_str)
        else:
            host = host_input
            rest_port = 8080
    except ValueError:
        _LOG.error("Invalid host:port format: %s", host_input)
        return SetupError(IntegrationSetupError.OTHER)

    _LOG.info("Testing connection to SkyQ device at %s:%s", host, rest_port)

    try:
        test_client = SkyQClient(host, rest_port)
        connection_successful = await test_client.test_connection()

        if not connection_successful and ':' not in host_input:
            await test_client.disconnect()
            _LOG.info("Port %s failed, trying alternate port...", rest_port)

            alternate_port = 9006 if rest_port == 8080 else 8080
            test_client = SkyQClient(host, alternate_port)
            connection_successful = await test_client.test_connection()

            if connection_successful:
                rest_port = alternate_port
                _LOG.info("Connection successful on alternate port %s", alternate_port)
            else:
                _LOG.info("Alternate port also failed, reverting to original port %s", rest_port)
                rest_port = 8080 if rest_port == 9006 else rest_port
                test_client = SkyQClient(host, rest_port)
                connection_successful = True

        if not connection_successful:
            _LOG.error("Connection test failed for host: %s (tried ports 8080 and 9006)", host)
            await test_client.disconnect()
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

        # SIMPLIFIED device name logic - avoid the Device object issue entirely
        device_name = f"SkyQ Device ({host})"
        
        try:
            device_info = await test_client.get_system_information()
            if device_info:
                # Safe device name extraction - no .get() on Device objects
                if hasattr(device_info, 'deviceName'):
                    # Real Device object - use getattr with fallback
                    extracted_name = getattr(device_info, 'deviceName', None)
                    if extracted_name and extracted_name.strip():
                        device_name = extracted_name.strip()
                        _LOG.info("Device name from pyskyqremote: %s", device_name)
                elif isinstance(device_info, dict):
                    # Dictionary - safe to use .get()
                    extracted_name = device_info.get('deviceName', '')
                    if extracted_name and extracted_name.strip():
                        device_name = extracted_name.strip()
                        _LOG.info("Device name from HTTP: %s", device_name)
                else:
                    _LOG.warning("Unknown device info format, using fallback name")
        except Exception as info_error:
            _LOG.warning("Error getting device info (non-critical): %s", info_error)

        await test_client.disconnect()

        device_id = f"skyq_{host.replace('.', '_')}_{rest_port}"

        if rest_port == 8080:
            remote_port = 49160
        elif rest_port >= 8080 and rest_port < 8090:
            remote_port = 49160 + (rest_port - 8080)
        else:
            remote_port = 49160

        device_config = SkyQDeviceConfig(
            device_id=device_id,
            name=device_name,
            host=host,
            rest_port=rest_port,
            remote_port=remote_port,
            enabled=True
        )

        _LOG.info("Device configured: HTTP=%s:%s, Remote=%s:%s", host, rest_port, host, remote_port)

        config_manager.add_device_config(device_config)

        await _initialize_entities()
        return SetupComplete()

    except Exception as e:
        _LOG.error("Setup error: %s", e, exc_info=True)
        return SetupError(IntegrationSetupError.OTHER)


async def _request_device_ips(device_count: int) -> RequestUserInput:
    settings = []

    for i in range(device_count):
        settings.extend([
            {
                "id": f"device_{i}_ip",
                "label": {"en": f"Device {i+1} IP Address"},
                "description": {"en": f"IP address for SkyQ device {i+1} (e.g., 192.168.1.{100+i} or 192.168.1.{100+i}:9006)"},
                "field": {"text": {"value": f"192.168.1.{100+i}"}}
            },
            {
                "id": f"device_{i}_name",
                "label": {"en": f"Device {i+1} Name"},
                "description": {"en": f"Friendly name for device {i+1}"},
                "field": {"text": {"value": f"SkyQ Device {i+1}"}}
            }
        ])

    return RequestUserInput(
        title={"en": f"Configure {device_count} SkyQ Devices"},
        settings=settings
    )


async def _handle_device_ips_collection(input_values: Dict[str, Any]) -> ucapi.SetupAction:
    devices_to_test = []

    device_index = 0
    while f"device_{device_index}_ip" in input_values:
        ip_input = input_values[f"device_{device_index}_ip"]
        name = input_values[f"device_{device_index}_name"]

        try:
            if ':' in ip_input:
                host, port_str = ip_input.split(':', 1)
                rest_port = int(port_str)
            else:
                host = ip_input
                rest_port = 9006
        except ValueError:
            _LOG.error(f"Invalid IP format for device {device_index + 1}: {ip_input}")
            return SetupError(IntegrationSetupError.OTHER)

        devices_to_test.append({
            "host": host,
            "rest_port": rest_port,
            "name": name,
            "index": device_index
        })
        device_index += 1

    _LOG.info(f"Testing connections to {len(devices_to_test)} devices...")
    test_results = await _test_multiple_devices(devices_to_test)

    successful_devices = 0
    for device_data, success in zip(devices_to_test, test_results):
        if success:
            device_id = f"skyq_{device_data['host'].replace('.', '_')}_{device_data['rest_port']}"
            device_config = SkyQDeviceConfig(
                device_id=device_id,
                name=device_data['name'],
                host=device_data['host'],
                rest_port=device_data['rest_port'],
                remote_port=49160,
                enabled=True
            )
            config_manager.add_device_config(device_config)
            successful_devices += 1
            _LOG.info(f"Device {device_data['index'] + 1} ({device_data['name']}) connection successful")
        else:
            _LOG.error(f"Device {device_data['index'] + 1} ({device_data['name']}) connection failed")

    if successful_devices == 0:
        _LOG.error("No devices could be connected")
        return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

    await _initialize_entities()
    _LOG.info(f"Multi-device setup completed: {successful_devices}/{len(devices_to_test)} devices configured")
    return SetupComplete()


async def _test_multiple_devices(devices: List[Dict]) -> List[bool]:
    async def test_device(device_data):
        try:
            client = SkyQClient(device_data['host'], device_data['rest_port'])
            success = await client.test_connection()
            await client.disconnect()
            return success
        except Exception as e:
            _LOG.error(f"Device {device_data['index'] + 1} test error: {e}")
            return False

    tasks = [test_device(device) for device in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [result if isinstance(result, bool) else False for result in results]


async def on_subscribe_entities(entity_ids: List[str]):
    global media_players, remotes, _entities_ready, config_manager

    _LOG.info(f"Entities subscription requested: {entity_ids}")

    if not _entities_ready:
        _LOG.error("RACE CONDITION: Subscription before entities ready! Attempting recovery...")
        if config_manager and config_manager.config.devices:
            await _initialize_entities()
        else:
            _LOG.error("Cannot recover - no configuration available")
            return

    for entity_id in entity_ids:
        # Check media players
        for device_id, media_player in media_players.items():
            if media_player.identifier == entity_id:
                _LOG.info("Media player subscribed for device %s, updating attributes", device_id)
                api.configured_entities.add(media_player)
                await media_player.update_attributes()
                break
        
        # Check remotes
        for device_id, remote in remotes.items():
            if remote.identifier == entity_id:
                _LOG.info("Remote subscribed for device %s, updating attributes", device_id)
                api.configured_entities.add(remote)
                await remote.update_attributes()
                break


async def on_unsubscribe_entities(entity_ids: List[str]):
    _LOG.info("Entities unsubscribed: %s", entity_ids)


async def on_connect():
    global _entities_ready, config_manager

    _LOG.info("Remote connected. Checking configuration state...")

    if not config_manager:
        config_manager = SkyQConfigManager()

    config_manager._config = None
    _ = config_manager.config

    if config_manager.config.devices and not _entities_ready:
        _LOG.info("Configuration found but entities missing, reinitializing...")
        try:
            await _initialize_entities()
        except Exception as e:
            _LOG.error("Failed to reinitialize entities: %s", e)
            await api.set_device_state(DeviceStates.ERROR)
            return

    if config_manager.config.devices and _entities_ready:
        await api.set_device_state(DeviceStates.CONNECTED)
    elif not config_manager.config.devices:
        await api.set_device_state(DeviceStates.DISCONNECTED)
    else:
        await api.set_device_state(DeviceStates.ERROR)


async def on_disconnect():
    _LOG.info("Remote disconnected")


async def main():
    global api, config_manager

    _LOG.info("Starting SkyQ Media Player + Remote integration driver")

    try:
        loop = asyncio.get_running_loop()
        api = ucapi.IntegrationAPI(loop)

        config_manager = SkyQConfigManager()
        _LOG.info(f"Using config file: {config_manager.get_config_file_path()}")

        if config_manager.config.devices:
            _LOG.info("Found existing configuration, pre-initializing Media Player + Remote entities for reboot survival")
            loop.create_task(_initialize_entities())

        driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
        if not os.path.exists(driver_path):
            driver_path = os.path.join(os.getcwd(), "driver.json")

        api.add_listener(Events.CONNECT, on_connect)
        api.add_listener(Events.DISCONNECT, on_disconnect)
        api.add_listener(Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
        api.add_listener(Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)

        await api.init(os.path.abspath(driver_path), setup_handler)

        if config_manager.config.devices:
            _LOG.info("%d device(s) already configured with Media Player + Remote", len(config_manager.config.devices))
        else:
            _LOG.info("No devices configured, waiting for setup...")
            await api.set_device_state(DeviceStates.DISCONNECTED)

        await asyncio.Future()

    except Exception as e:
        _LOG.error("Fatal error in main: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Integration stopped by user")
    except Exception as e:
        _LOG.error("Integration crashed: %s", e, exc_info=True)
        sys.exit(1)
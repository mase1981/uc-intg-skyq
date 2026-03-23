"""
SkyQ Setup Flow handler.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi.api_definitions import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_skyq.client import SkyQClient
from uc_intg_skyq.config import SkyQDeviceConfig
from uc_intg_skyq.const import SKYQ_ALT_REST_PORT, SKYQ_DEFAULT_REST_PORT, SKYQ_REMOTE_PORT

_LOG = logging.getLogger(__name__)


class SkyQSetupFlow(BaseSetupFlow[SkyQDeviceConfig]):
    """Setup flow for SkyQ device configuration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "SkyQ Device Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": "SkyQ"}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
            ],
        )

    async def query_device(self, input_values: dict[str, Any]) -> SkyQDeviceConfig:
        host_input = input_values.get("host", "").strip()
        if not host_input:
            raise ValueError("IP address is required")

        name = input_values.get("name", "SkyQ").strip() or "SkyQ"

        if ":" in host_input:
            host, port_str = host_input.split(":", 1)
            rest_port = int(port_str)
            explicit_port = True
        else:
            host = host_input
            rest_port = SKYQ_DEFAULT_REST_PORT
            explicit_port = False

        client = SkyQClient(host, rest_port)
        try:
            connected = await asyncio.wait_for(client.test_connection(), timeout=10.0)

            if not connected and not explicit_port:
                alt_port = SKYQ_ALT_REST_PORT if rest_port == SKYQ_DEFAULT_REST_PORT else SKYQ_DEFAULT_REST_PORT
                _LOG.info("Port %d failed, trying %d", rest_port, alt_port)
                client = SkyQClient(host, alt_port)
                connected = await asyncio.wait_for(client.test_connection(), timeout=10.0)
                if connected:
                    rest_port = alt_port

            if not connected:
                raise ValueError(f"Cannot connect to SkyQ device at {host}")

            info = await client.get_system_information()
            if info:
                if isinstance(info, dict):
                    device_name = info.get("deviceName", "")
                else:
                    device_name = getattr(info, "deviceName", "")
                if device_name and device_name.strip() and name == "SkyQ":
                    name = device_name.strip()

        except asyncio.TimeoutError:
            raise ValueError(f"Connection to {host} timed out") from None
        finally:
            await client.disconnect()

        if rest_port == SKYQ_DEFAULT_REST_PORT:
            remote_port = SKYQ_REMOTE_PORT
        elif SKYQ_DEFAULT_REST_PORT <= rest_port < SKYQ_DEFAULT_REST_PORT + 10:
            remote_port = SKYQ_REMOTE_PORT + (rest_port - SKYQ_DEFAULT_REST_PORT)
        else:
            remote_port = SKYQ_REMOTE_PORT

        identifier = f"{host.replace('.', '_')}_{rest_port}"

        return SkyQDeviceConfig(
            identifier=identifier,
            name=name,
            host=host,
            rest_port=rest_port,
            remote_port=remote_port,
        )

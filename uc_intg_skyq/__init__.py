#!/usr/bin/env python3
"""
Integration driver library for SkyQ devices and Remote Two/3.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import logging  # isort:skip
import json
import os

logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    _driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
    with open(_driver_path, 'r') as f:
        _driver_data = json.load(f)
        __version__ = _driver_data["version"]
        version_tuple = tuple(int(x) for x in __version__.split("."))
except:
    # Fallback if driver.json not found
    __version__ = "1.0.0"
    version_tuple = (1, 0, 0)
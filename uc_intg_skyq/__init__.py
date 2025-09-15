#!/usr/bin/env python3
"""
Integration driver library for SkyQ devices and Remote Two/3.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Simple version definition - no complex file loading
__version__ = "1.0.5"
version_tuple = (1, 0, 0)
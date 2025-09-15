"""
SkyQ Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "1.0.6"
    version_tuple = (1, 0, 5)

__all__ = ["__version__", "version_tuple"]
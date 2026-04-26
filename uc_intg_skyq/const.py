"""
Constants for SkyQ integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

SKYQ_DEFAULT_REST_PORT = 8080
SKYQ_ALT_REST_PORT = 9006
SKYQ_REMOTE_PORT = 49160
SKYQ_POLL_INTERVAL = 10
SKYQ_API_TIMEOUT = 5
SKYQ_CONNECT_RETRIES = 5
SKYQ_CONNECT_RETRY_DELAY = 3
SKYQ_DIGIT_DELAY = 0.5

APP_EPG = "com.bskyb.epgui"

SIMPLE_COMMANDS = [
    "power", "standby", "on", "off", "select", "channelup", "channeldown",
    "sky", "help", "services", "search", "home", "up", "down", "left", "right",
    "red", "green", "yellow", "blue",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "play", "pause", "stop", "record", "fastforward", "rewind",
    "text", "back", "menu", "guide", "info",
    "volumeup", "volumedown", "mute", "tvguide", "i",
    "boxoffice", "dismiss", "backup", "tv", "radio", "interactive",
    "mysky", "planner", "top", "subtitle", "audio", "announce", "last", "list",
]

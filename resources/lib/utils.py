import sys
import random
import xbmc
import xbmcaddon
from urllib.parse import urlencode

ADDON = xbmcaddon.Addon()
BASE_URL = sys.argv[0]

def log(msg, level=xbmc.LOGINFO):
    """Log messages to Kodi's log file."""
    addon_name = ADDON.getAddonInfo('name')
    xbmc.log(f'[{addon_name}] {msg}', level)

def build_url(query):
    """Build a plugin URL with the given query parameters."""
    return f"{BASE_URL}?{urlencode(query)}"

def get_random_agent() -> str:
    """Get random user agent."""
    USER_AGENTS = [
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"),
        ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"),
    ]
    return random.choice(USER_AGENTS)

def get_setting(key):
    return ADDON.getSetting(key)

def get_setting_bool(key):
    return ADDON.getSettingBool(key)

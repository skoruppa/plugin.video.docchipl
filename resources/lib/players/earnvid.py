import re
import requests
from urllib.parse import urlparse
from ..utils import get_random_agent
from .utils import unpack_js, fetch_resolution_from_m3u8

def get_video_from_earnvid_player(player_url: str):
    try:
        headers = {"User-Agent": get_random_agent(), "Referer": player_url}
        parsed_url = urlparse(player_url)
        base_url_with_scheme = f"{parsed_url.scheme}://{parsed_url.netloc}"

        response = requests.get(player_url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text

        if not re.search(r"eval\(function\(p,a,c,k,e", html_content):
            return None, None, None
        unpacked_js_code = unpack_js(html_content)
        stream_match = re.search(r'"hls4"\s*:\s*"([^"]+)"', unpacked_js_code)
        if not stream_match:
            return None, None, None

        stream_url = f"{base_url_with_scheme}{stream_match.group(1)}"
        try:
            quality = fetch_resolution_from_m3u8(stream_url, headers) or "unknown"
        except Exception:
            quality = "unknown"
        stream_headers = {'request': headers}
        return stream_url, quality, stream_headers
    except Exception as e:
        print(f"EarnVid Player Error: Unexpected: {e}")
        return None, None, None
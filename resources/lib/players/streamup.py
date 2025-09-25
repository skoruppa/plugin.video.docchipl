import re
import requests
from urllib.parse import urlparse
from ..utils import get_random_agent
from .utils import fetch_resolution_from_m3u8

def get_video_from_streamup_player(player_url: str):
    try:
        parsed_url = urlparse(player_url)
        base_url_with_scheme = f"{parsed_url.scheme}://{parsed_url.netloc}"
        filecode_match = re.search(r'/([a-zA-Z0-9]+)$', parsed_url.path)
        if not filecode_match: return None, None, None
        filecode = filecode_match.group(1)

        api_headers = {"User-Agent": get_random_agent(), "Referer": player_url}
        api_url = f"{base_url_with_scheme}/ajax/stream?filecode={filecode}"
        
        response = requests.get(api_url, headers=api_headers, timeout=15)
        response.raise_for_status()
        json_data = response.json()
        
        stream_url = json_data.get("streaming_url")
        if not stream_url: return None, None, None
        
        stream_headers_dict = {"User-Agent": api_headers["User-Agent"], "Referer": base_url_with_scheme + "/", "Origin": base_url_with_scheme}
        stream_headers = {'request': stream_headers_dict}
        
        quality = fetch_resolution_from_m3u8(stream_url, stream_headers_dict) or "unknown"
        return stream_url, quality, stream_headers
    except Exception as e:
        print(f"StreamUP Player Error: Unexpected Error: {e}")
        return None, None, None
    

if __name__ == '__main__':
    # Poprawiony blok testowy
    from ._test_utils import run_tests
    urls_to_test = [
        "https://strmup.to/wpVmyon50fFld"
    ]
    run_tests(get_video_from_streamup_player, urls_to_test)
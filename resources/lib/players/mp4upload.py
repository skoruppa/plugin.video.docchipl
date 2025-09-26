import re
import requests
from ..utils import get_random_agent

def get_video_from_mp4upload_player(player_url: str):
    try:
        headers = {"User-Agent": get_random_agent(), "Referer": "https://www.mp4upload.com/"}
        response = requests.get(player_url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text
        
        stream_url_match = re.search(r'player\.src\(\s*{\s*type:\s*"video/mp4",\s*src:\s*"([^"]+)"', html_content)
        if not stream_url_match:
            return None, None, None
        stream_url = stream_url_match.group(1)
        
        quality = "unknown"
        height_match = re.search(r"embed:\s*'[^']*?\bHEIGHT=(\d+)", html_content)
        if height_match:
            quality = f"{height_match.group(1)}p"

        kodi_params = headers.copy()
        kodi_params['verifypeer'] = 'false'  # Ignore SSL

        stream_headers = {'request': kodi_params}
        return stream_url, quality, stream_headers
    except Exception as e:
        print(f"MP4Upload Player Error: Unexpected Error: {e}")
        return None, None, None
    

if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://www.mp4upload.com/embed-mhcydywd0i83.html",
    ]
    run_tests(get_video_from_mp4upload_player, urls_to_test)
import re
import requests
from urllib.parse import urlparse
from ..utils import get_random_agent, log
import xbmc


def get_video_from_pixeldrain_player(player_url: str):
    headers = {"User-Agent": get_random_agent()}

    try:
        parsed_url = urlparse(player_url)
        path = parsed_url.path

        match = re.search(r'/(u|l|file)/([0-9a-zA-Z\-]+)', path)
        if not match:
            log(f"PixelDrain Error: Invalid URL format for {player_url}", xbmc.LOGERROR)
            return None, None, None

        mtype, mid = match.groups()

        stream_url = None

        if mtype == 'l':
            api_url = f"https://pixeldrain.com/api/list/{mid}"
            with requests.Session() as session:
                response = session.get(api_url, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()

            if not data.get('success'):
                error_message = data.get('message', 'Unknown API error')
                log(f"PixelDrain API Error for list {mid}: {error_message}", xbmc.LOGERROR)
                return None, None, None

            video_files = [f for f in data.get('files', []) if f.get('mime_type') and 'video' in f['mime_type']]
            if not video_files:
                log(f"PixelDrain Error: No video files found in list {mid}.", xbmc.LOGERROR)
                return None, None, None

            largest_video = max(video_files, key=lambda x: x.get('size', 0))
            file_id = largest_video.get('id')
            if not file_id:
                log("PixelDrain Error: Could not determine file ID from the largest video.", xbmc.LOGERROR)
                return None, None, None

            stream_url = f"https://pixeldrain.com/api/file/{file_id}"

        elif mtype in ('u', 'file'):
            stream_url = f"https://pixeldrain.com/api/file/{mid}"

        if stream_url:
            stream_headers = {'request': headers}
            quality = "unknown"
            return stream_url, quality, stream_headers

    except requests.exceptions.RequestException as http_err:
        log(f"PixelDrain Player Error: An HTTP error occurred: {http_err}", xbmc.LOGERROR)
        return None, None, None
    except Exception as e:
        log(f"PixelDrain Player Error: An unexpected error occurred: {e}", xbmc.LOGERROR)
        return None, None, None

    return None, None, None


if __name__ == '__main__':
    from ._test_utils import run_tests

    urls_to_test = [
        "https://pixeldrain.com/u/rkHjhTWZ?embed"
    ]

    run_tests(get_video_from_pixeldrain_player, urls_to_test)
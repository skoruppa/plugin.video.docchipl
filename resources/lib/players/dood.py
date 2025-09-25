import re
import requests
from ..utils import get_random_agent, log
import xbmc

def get_video_from_dood_player(url):
    user_agent = get_random_agent()
    quality = "unknown"
    dood_host_match = re.search(r"https://(.*?)/", url)
    if not dood_host_match:
        return None, None, None
    dood_host = dood_host_match.group(1)

    try:
        s = requests.Session()
        s.headers.update({"User-Agent": user_agent})
        
        response = s.get(url)
        new_url = response.url # Pobieramy finalny URL po ewentualnych przekierowaniach
        stream_headers = {"request": {"Referer": new_url, "User-Agent": user_agent}}
        content = response.text

        if "'/pass_md5/" not in content:
            return None, None, None

        md5 = content.split("'/pass_md5/")[1].split("',")[0]
        video_url_path = f"https://{dood_host}/pass_md5/{md5}"
        
        # Dood wymaga tego samego referera, co strona z odtwarzaczem
        video_response = s.get(video_url_path, headers={"Referer": new_url})
        video_content = video_response.text
        return video_content, quality, stream_headers

    except Exception as e:
        log(f"Dood Player Error: {e}", xbmc.LOGERROR)
        return None, None, None
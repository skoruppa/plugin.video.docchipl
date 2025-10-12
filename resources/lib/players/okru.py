import re
import requests
import json
from bs4 import BeautifulSoup
from ..utils import get_random_agent

def fix_quality(quality):
    quality_mapping = {
        "ultra": 2160, "quad": 1440, "full": 1080, "hd": 720,
        "sd": 480, "low": 360, "lowest": 240, "mobile": 144
    }
    return quality_mapping.get(quality, 0)

def process_video_json(video_json):
    videos = []
    for item in video_json:
        video_url = item.get('url')
        quality_name = item.get('name')

        if video_url and quality_name:
            quality_pixels = fix_quality(quality_name)
            if video_url.startswith("https://") and quality_pixels > 0:
                videos.append({'url': video_url, 'quality': quality_pixels})

    if not videos:
        return None, None

    highest_quality_video = max(videos, key=lambda x: x['quality'])
    return highest_quality_video['url'], f"{highest_quality_video['quality']}p"

def get_video_from_okru_player(url):
    user_agent = get_random_agent()
    headers = {"User-Agent": user_agent}
    video_headers = {
        "request": {
            "User-Agent": user_agent,
            "Origin": "https://ok.ru",
            "Referer": "https://ok.ru/",
        }
    }
    media_id_match = re.search(r'/video(?:embed)?/(\d+)', url)
    if not media_id_match:
        return None, None, None
    media_id = media_id_match.group(1)

    try:
        with requests.Session() as session:
            session.headers.update(headers)

            api_url = "https://www.ok.ru/dk?cmd=videoPlayerMetadata"
            payload = {'mid': media_id}

            try:
                with session.post(api_url, data=payload) as response:
                    if response.status_code == 200:
                        metadata = response.json()
                        if 'videos' in metadata:
                            stream, quality = process_video_json(metadata['videos'])
                            if stream:
                                return stream, quality, video_headers
            except:
                pass

            embed_url = f"https://ok.ru/videoembed/{media_id}"

            with session.get(embed_url, verify=False) as response:
                text = response.text

            document = BeautifulSoup(text, "html.parser")
            player_string_div = document.select_one("div[data-options]")
            if not player_string_div:
                return None, None, None

            player_data_str = player_string_div.get("data-options", "")
            player_data_cleaned = player_data_str.replace('&quot;', '"').replace('&amp;', '&')

            player_json = json.loads(player_data_cleaned)
            video_json_str = player_json.get('flashvars', {}).get('metadata')

            if not video_json_str:
                return None, None, None

            video_json = json.loads(video_json_str).get('videos')
            if not video_json:
                return None, None, None

            stream, quality = process_video_json(video_json)
            return stream, quality, video_headers
    except:
        return None, None, None


if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://ok.ru/videoembed/4511946705484"
    ]
    run_tests(get_video_from_okru_player, urls_to_test)
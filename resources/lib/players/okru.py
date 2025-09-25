import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ..utils import get_random_agent

def fix_quality(quality):
    quality_mapping = {"ultra": "2160p", "quad": "1440p", "full": "1080p", "hd": "720p", "sd": "480p", "low": "360p", "lowest": "240p", "mobile": "144p"}
    return quality_mapping.get(quality, quality)

def extract_link(item, attr):
    return item.get(attr, '').replace("\\\\u0026", "&")

def videos_from_json(video_json, user_agent):
    videos = []
    for item in video_json:
        video_url = extract_link(item, 'url')
        quality_str = item.get('name')
        if video_url.startswith("https://"):
            videos.append({'url': video_url, 'quality': quality_str})
    if not videos: return None, None, None
    
    quality_order = ['mobile', 'lowest', 'low', 'sd', 'hd', 'full', 'quad', 'ultra']
    highest_quality_video = sorted(videos, key=lambda x: quality_order.index(x['quality']) if x['quality'] in quality_order else -1)[-1]
    
    quality_label = fix_quality(highest_quality_video['quality'])
    video_headers = {"request": {"User-Agent": user_agent, "Origin": "https://ok.ru", "Referer": "https://ok.ru/", "host": urlparse(highest_quality_video['url']).hostname}}
    return highest_quality_video['url'], quality_label, video_headers

def get_video_from_okru_player(url):
    user_agent = get_random_agent()
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, verify=False) # verify=False for potential SSL issues
        text = response.text
    except requests.exceptions.RequestException:
        return None, None, None

    document = BeautifulSoup(text, "html.parser")
    player_string = document.select_one("div[data-options]")
    if not player_string: return None, None, None
    player_data = player_string.get("data-options", "")
    player_json = json.loads(player_data)
    if 'flashvars' not in player_json or 'metadata' not in player_json['flashvars']: return None, None, None
    video_json = json.loads(player_json['flashvars']['metadata']).get('videos')
    if not video_json: return None, None, None
    return videos_from_json(video_json, user_agent)
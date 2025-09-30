import re
import requests
from bs4 import BeautifulSoup
from ..utils import get_random_agent
from urllib.parse import urlencode

def build_video_url(base_url, document):
    url = base_url.split('?')[0]
    params = {
        input_elem["name"]: input_elem["value"]
        for input_elem in document.select("input[type=hidden]")
    }
    query_string = urlencode(params)

    return f"{url}?{query_string}"


def get_video_from_gdrive_player(drive_url: str):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", drive_url)
    if not match:
        return None, None, None
    item_id = match.group(1)
    video_url = f"https://drive.usercontent.google.com/download?id={item_id}"
    headers = {"User-Agent": get_random_agent()}

    response = requests.get(video_url, headers=headers)
    text = response.text
    if 'Error 404 (Not Found)' in text:
        return None, None, None
    elif not text.startswith("<!DOCTYPE html>"):
        return video_url, "unknown", {'request': headers}
    soup = BeautifulSoup(text, "html.parser")
    quality = "unknown"
    final_video_url = build_video_url(video_url, soup)
    return final_video_url, quality, {'request': headers}
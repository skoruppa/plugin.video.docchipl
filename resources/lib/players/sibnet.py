import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from ..utils import get_random_agent

def get_video_from_sibnet_player(url: str) -> tuple:
    headers = {"User-Agent": get_random_agent()}
    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            return None, None, None
        html = response.text
        document = BeautifulSoup(html, "html.parser")
        script = document.select_one("script:-soup-contains('player.src')")
        if not script or not script.string:
            return None, None, None
        
        script_data = script.string
        slug_match = re.search(r'player\.src\(\[\{src:\s*"([^"]+)"', script_data)
        if not slug_match:
            return None, None, None
        slug = slug_match.group(1)

        video_headers = {"request": {"Referer": url, "User-Agent": headers['User-Agent']}}
        if "http" in slug:
            video_url = slug
        else:
            host = urlparse(url).netloc
            video_url = f"https://{host}{slug}"
        
        # Sprawdzamy przekierowania
        head_response = requests.head(video_url, headers=video_headers["request"], allow_redirects=False)
        if head_response.status_code in (301, 302, 307) and "Location" in head_response.headers:
            location = head_response.headers["Location"]
            if not location.startswith("http"):
                location = urljoin(f"https://{host}", location)
            video_url = location
    except requests.exceptions.RequestException:
        return None, None, None
    return video_url, "unknown", video_headers
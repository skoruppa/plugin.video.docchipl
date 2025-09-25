import re
import requests
from bs4 import BeautifulSoup  
from urllib.parse import urlparse
from ..utils import get_random_agent

def get_video_from_uqload_player(url: str):
    if "embed-" in url:
        url = url.replace("embed-", "")
    parsed_url = urlparse(url)
    headers = {
        "User-Agent": get_random_agent(),
        "Referer": f"{parsed_url.scheme}://{parsed_url.netloc}",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        text = response.text
        soup = BeautifulSoup(text, 'html.parser')
        try:
            match = re.search(r"\[\d+x(\d+),", soup.find("div", id="forumcode").textarea.text)
        except AttributeError:
            return None, None, None
        quality = f'{match.group(1)}p' if match else "unknown"
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'sources:' in script.string:
                match = re.search(r'sources:\s*\["(https?.*?\.mp4)"\]', script.string)
                if match:
                    stream_url = match.group(1)
                    video_headers = {'request': headers}
                    return stream_url, quality, video_headers
    except requests.exceptions.RequestException:
        return None, None, None
    return None, None, None
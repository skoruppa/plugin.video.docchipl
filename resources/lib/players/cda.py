import re
import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
from ..utils import get_random_agent


def decrypt_url(url: str) -> str:
    for p in ("_XDDD", "_CDA", "_ADC", "_CXD", "_QWE", "_Q5", "_IKSDE"):
        url = url.replace(p, "")
    url = urllib.parse.unquote(url)
    b = []
    for c in url:
        f = c if isinstance(c, int) else ord(c)
        b.append(chr(33 + (f + 14) % 94) if 33 <= f <= 126 else chr(f))
    a = "".join(b)
    a = a.replace(".cda.mp4", "")
    a = a.replace(".2cda.pl", ".cda.pl")
    a = a.replace(".3cda.pl", ".cda.pl")
    if "/upstream" in a:
        a = a.replace("/upstream", ".mp4/upstream")
        return "https://" + a
    return "https://" + a + ".mp4"


def normalize_cda_url(url):
    pattern = r"https?://(?:www\.)?cda\.pl/(?:video/)?([\w]+)(?:\?.*)?|https?://ebd\.cda\.pl/\d+x\d+/([\w]+)"
    match = re.match(pattern, url)

    if match:
        video_id = match.group(1) or match.group(2)
        return f"https://ebd.cda.pl/620x368/{video_id}", video_id
    else:
        return None, None


def get_highest_quality(qualities: dict) -> tuple:
    qualities.pop('auto', None)  # worthless quality
    highest_quality = max(qualities.keys(), key=lambda x: int(x.rstrip('p')))
    return highest_quality, qualities[highest_quality]


def fetch_video_data(session: requests.Session, url: str, headers: dict) -> dict:
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException:
        return None
    soup = BeautifulSoup(html, "html.parser")
    player_div = soup.find("div", id=lambda x: x and x.startswith("mediaplayer"))
    if not player_div or "player_data" not in player_div.attrs:
        return None
    return json.loads(player_div["player_data"])

def get_video_from_cda_player(url: str) -> tuple:
    url, video_id = normalize_cda_url(url)
    user_agent = get_random_agent()
    headers = {"User-Agent": user_agent}
    if not url:
        return None, None, None
    session = requests.Session()
    video_data = fetch_video_data(session, url, headers)
    if not video_data:
        return None, None, None
    qualities = video_data['video']['qualities']
    current_quality = video_data['video']['quality']
    highest_quality, quality_id = get_highest_quality(qualities)
    if quality_id != current_quality:
        url = f'{url}?wersja={highest_quality}'
        video_data = fetch_video_data(session, url, headers)
        if not video_data:
            return None, None, None
    file = video_data['video']['file']
    if file:
        url = decrypt_url(file)
        headers = {"request": {"Referer": f"https://ebd.cda.pl/",
                   "User-Agent": user_agent}}
    else:
        url = video_data['video']['manifest_apple']
    if url:
        return url, highest_quality, headers
    raise ValueError("Failed to fetch video URL.")


if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://ebd.cda.pl/620x368/26162334f2"
    ]
    run_tests(get_video_from_cda_player, urls_to_test)
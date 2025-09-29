import requests
import base64
import json
from bs4 import BeautifulSoup
import re
from ..utils import get_random_agent, log
import xbmc
from .rumble import get_video_from_rumble_player

headers = {"User-Agent": get_random_agent()}
GET_SECONDARY_URL = "https://www.lycoris.cafe/api/watch/getSecondaryLink"
GET_LINK_URL = "https://www.lycoris.cafe/api/watch/getLink"


def check_url_status(url, timeout=10):
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, verify=False)
        if resp.status_code not in (405, 501):
            return resp.status_code
    except:
        pass

    try:
        resp = requests.get(
            url,
            headers={"Range": "bytes=0-0"},
            allow_redirects=True,
            stream=True,
            timeout=timeout,
            verify=False
        )
        return resp.status_code
    except:
        return None


def decode_video_links(encoded_url):
    if not encoded_url:
        return None

    # Check for our signature
    if not encoded_url.endswith('LC'):
        return encoded_url

    # Remove signature
    encoded_url = encoded_url[:-2]

    try:
        # Reverse the scrambling
        decoded = ''.join(
            chr(ord(char) - 7)  # Shift back
            for char in reversed(encoded_url)  # Reverse back
        )

        # Decode base64
        base64_decoded = base64.b64decode(decoded).decode('utf-8')
        try:
            data = json.loads(base64_decoded)  # Próba załadowania ciągu jako JSON
            return data  # Jeśli nie wystąpi wyjątek, to JSON jest poprawny
        except json.JSONDecodeError:
            return base64_decoded
    except Exception as error:
        print(f"Error decoding URL: {error}")
        return None


def fetch_and_decode_video(session: requests.Session, episode_id: str, is_secondary: bool = False):
    GET_SECONDARY_URL = "https://www.lycoris.cafe/api/watch/getSecondaryLink"
    GET_LINK_URL = "https://www.lycoris.cafe/api/watch/getLink"
    try:
        if not is_secondary:
            converted_text = bytes(episode_id, "utf-8").decode("unicode_escape")
            final_text = converted_text.encode("latin1").decode("utf-8")
            params = {"link": final_text}
            url = GET_LINK_URL
        else:
            params = {"id": episode_id}
            url = GET_SECONDARY_URL

        response = session.get(url, params=params, verify=False)
        response.raise_for_status()
        data = response.text
        return decode_video_links(data)
    except requests.exceptions.RequestException as e:
        log(f"Lycoris request error: {e}", xbmc.LOGERROR)
        return None


def get_highest_quality(video_links):
    quality_map = {
        "SD": 480,
        "HD": 720,
        "FHD": 1080
    }

    filtered_links = {k: v for k, v in video_links.items() if k in quality_map}

    if not filtered_links:
        return None, None, None

    highest_quality = max(filtered_links.keys(), key=lambda q: quality_map.get(q, 0))
    highest_resolution = f"{quality_map[highest_quality]}p"

    return filtered_links[highest_quality], highest_resolution, None


def get_video_from_lycoris_player(url: str):
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": get_random_agent()})
        
        response = session.get(url, verify=False)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', {'type': 'application/json'})

        if script and script.string and "episodeInfo" in script.string:
            data = json.loads(script.string.strip())
            body = json.loads(data["body"])
            
            highest_quality = None
            if body['episodeInfo']['FHD']: highest_quality = {"url": body['episodeInfo']['FHD'], 'quality': '1080p'}
            elif body['episodeInfo']['HD']: highest_quality = {"url": body['episodeInfo']['HD'], 'quality': '720p'}
            elif body['episodeInfo']['SD']: highest_quality = {"url": body['episodeInfo']['SD'], 'quality': '480p'}

            if body['episodeInfo']['id']:
                video_links = fetch_and_decode_video(session, body['episodeInfo']['id'], is_secondary=True)
                if not video_links:
                    if highest_quality:
                        video_link = fetch_and_decode_video(session, highest_quality['url'], is_secondary=False)
                        return video_link, highest_quality['quality'], None
                else:
                    video_url, quality, _ = get_highest_quality(video_links)

                    if video_url:
                        status = check_url_status(video_url)
                        if status == 403:
                            if body['episodeInfo']['rumbleLink']:
                                return get_video_from_rumble_player(body['episodeInfo']['rumbleLink'])
                            else:
                                return None, None, None
                        return video_url, quality, None

        return None, None, None
    except Exception as e:
        log(f"Lycoris Player Error: {e}", xbmc.LOGERROR)
        return None, None, None

if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://www.lycoris.cafe/embed?id=178025&episode=11"
    ]
    run_tests(get_video_from_lycoris_player, urls_to_test)

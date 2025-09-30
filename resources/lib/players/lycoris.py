import requests
import base64
import json
from bs4 import BeautifulSoup
from ..utils import get_random_agent, log
import xbmc
from .rumble import get_video_from_rumble_player

DECRYPT_API_KEY = "303a897d-sd12-41a8-84d1-5e4f5e208878"


def check_url_status(session, url, timeout=10):
    try:
        resp = session.head(url, allow_redirects=True, timeout=timeout, verify=False)
        if resp.status_code not in (405, 501):
            return resp.status_code
    except requests.exceptions.RequestException:
        pass

    try:
        resp = session.get(
            url,
            headers={"Range": "bytes=0-0"},
            allow_redirects=True,
            stream=True,
            timeout=timeout,
            verify=False
        )
        return resp.status_code
    except requests.exceptions.RequestException:
        return None


def get_video_from_lycoris_player(url: str):
    try:
        session = requests.Session()
        user_agent = get_random_agent()
        session.headers.update({"User-Agent": user_agent})

        response = session.get(url, verify=False, timeout=15)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', {'type': 'application/json'})

        if not (script and script.string and "episodeInfo" in script.string):
            return None, None, None

        data = json.loads(script.string.strip())
        body = json.loads(data["body"])

        episode_info = body.get('episodeInfo', {})
        episode_id = episode_info.get('id')

        if not episode_id:
            log("Lycoris Player Error: Episode ID not found.", xbmc.LOGERROR)
            return None, None, None

        # Get encoded video link
        video_link_url = f"https://www.lycoris.cafe/api/watch/getVideoLink?id={episode_id}"
        link_response = session.get(video_link_url, timeout=15)
        link_response.raise_for_status()
        encrypted_text = link_response.text

        base64_encoded_data = base64.b64encode(encrypted_text.encode('latin-1')).decode('utf-8')

        decrypt_url = "https://www.lycoris.cafe/api/watch/decryptVideoLink"
        decrypt_headers = {
            "User-Agent": user_agent,
            "x-api-key": DECRYPT_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"encoded": base64_encoded_data}

        decrypt_response = session.post(decrypt_url, headers=decrypt_headers, json=payload, timeout=15)
        decrypt_response.raise_for_status()
        video_sources = decrypt_response.json()

        highest_quality = None
        if video_sources.get('FHD'):
            highest_quality = {"url": video_sources['FHD'], 'quality': '1080p'}
        elif video_sources.get('HD'):
            highest_quality = {"url": video_sources['HD'], 'quality': '720p'}
        elif video_sources.get('SD'):
            highest_quality = {"url": video_sources['SD'], 'quality': '480p'}

        if highest_quality:
            url_candidate, quality = highest_quality['url'], highest_quality['quality']
            status = check_url_status(session, url_candidate)
            if status == 200:
                return url_candidate, quality, None

        # Fallback to Rumble if primary sources fail
        rumble_url = episode_info.get('rumbleLink')
        if rumble_url:
            return get_video_from_rumble_player(rumble_url)

        return None, None, None

    except Exception as e:
        log(f"Lycoris Player Error: An unexpected error occurred: {e}", xbmc.LOGERROR)
        return None, None, None


if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://www.lycoris.cafe/embed?id=178025&episode=12"
    ]
    run_tests(get_video_from_lycoris_player, urls_to_test)
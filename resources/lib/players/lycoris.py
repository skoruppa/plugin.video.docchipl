import requests
import base64
import json
from bs4 import BeautifulSoup
import re
from ..utils import get_random_agent, log
import xbmc
from .rumble import get_video_from_rumble_player

headers = {"User-Agent": get_random_agent()}


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
            if body['episodeInfo']['primarySource']['FHD']:
                highest_quality = {"url": body['episodeInfo']['primarySource']['FHD'], 'quality': 1080}
            elif body['episodeInfo']['primarySource']['HD']:
                highest_quality = {"url": body['episodeInfo']['primarySource']['HD'], 'quality': 720}
            elif body['episodeInfo']['primarySource']['SD']:
                highest_quality = {"url": body['episodeInfo']['primarySource']['SD'], 'quality': 480}

            url_candidate, quality = highest_quality['url'], highest_quality['quality']

            status = check_url_status(url_candidate)
            if status != 200:
                rumble_url = body['episodeInfo'].get('rumbleLink')
                if rumble_url:
                    rumble = get_video_from_rumble_player(rumble_url)
                    return rumble
                return None, None, None

            return url_candidate, quality, None

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

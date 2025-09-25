import requests
import re
from bs4 import BeautifulSoup
from ..utils import get_random_agent, log
import xbmc

def get_video_from_streamtape_player(url: str):
    """
    Extracts the video URL from a Streamtape player page.
    This version is fully synchronous using the requests library.
    """
    quality = "unknown"
    base_url = "https://streamtape.com/e/"

    # Normalize URL if it's not in the embed format
    if not url.startswith(base_url):
        parts = url.split("/")
        video_id = parts[4] if len(parts) > 4 else None
        if not video_id:
            return None, None, None
        new_url = base_url + video_id
    else:
        new_url = url

    headers = {
        "User-Agent": get_random_agent(),
        "Referer": new_url,
    }

    try:
        # Make the GET request to the player page
        response = requests.get(new_url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        content = response.text

        # Find the script tag containing the video link logic
        soup = BeautifulSoup(content, 'html.parser')
        target_line = "document.getElementById('robotlink')"
        script_tag = soup.find("script", string=lambda text: text and target_line in text)
        
        if not script_tag or not script_tag.string:
            log("Streamtape: Could not find the target script tag.", xbmc.LOGWARNING)
            return None, None, None

        script_content = script_tag.string

        # Extract the two obfuscated parts of the URL
        # Part 1 is typically in an innerHTML assignment
        first_part_match = re.search(r"innerHTML = \"(//[^']*)'", script_content)
        if not first_part_match:
            log("Streamtape: Could not find the first part of the URL.", xbmc.LOGWARNING)
            return None, None, None
        first_part = first_part_match.group(1)

        # Part 2 is often concatenated after a substring operation
        second_part_match = re.search(r"\.substring\(\d+\)\s*\+\s*'([^']*)'", script_content)
        second_part = second_part_match.group(1) if second_part_match else ''

        # Handle a variant where a double substring is used
        if not second_part:
             second_part_match = re.search(r"\.substring\(\d+\)\s*\)\.substring\(\d+\)\s*\+\s*'([^']*)'", script_content)
             second_part = second_part_match.group(1) if second_part_match else ''
        
        # Combine the parts to form the final URL
        stream_data = first_part + second_part
        stream_url = f'https:{stream_data}'
        
        # Prepare headers for Kodi to use during playback
        video_headers = {'request': headers}

        return stream_url, quality, video_headers

    except requests.exceptions.RequestException as e:
        log(f"Streamtape request failed: {e}", xbmc.LOGERROR)
        return None, None, None
    except Exception as e:
        log(f"Streamtape unexpected error: {e}", xbmc.LOGERROR)
        return None, None, None
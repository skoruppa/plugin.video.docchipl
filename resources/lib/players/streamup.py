import base64
import re
import requests
import json
from urllib.parse import urlparse
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from ..utils import get_random_agent
from .utils import fetch_resolution_from_m3u8

def get_video_from_streamup_player(player_url: str):
    try:
        with requests.Session() as session:
            user_agent = get_random_agent()
            page_headers = {"User-Agent": user_agent}

            page_response = session.get(player_url, headers=page_headers, timeout=15)
            page_response.raise_for_status()
            page_content = page_response.text

            media_id = player_url.split('/')[-1]
            session_id_match = re.search(r"'([a-f0-9]{32})'", page_content)
            encrypted_data_match = re.search(r"'([A-Za-z0-9+/=]{200,})'", page_content)

            parsed_url = urlparse(page_response.url)
            base_url_with_scheme = f"{parsed_url.scheme}://{parsed_url.netloc}"

            headers = {"User-Agent": user_agent, "Referer": player_url}

            if encrypted_data_match and session_id_match:
                session_id = session_id_match.group(1)
                encrypted_data_b64 = encrypted_data_match.group(1)

                key_url = f"{base_url_with_scheme}/ajax/stream?session={session_id}"

                key_response = session.get(key_url, headers=headers, timeout=15)
                key_response.raise_for_status()
                key_b64 = key_response.text

                key = base64.b64decode(key_b64)
                encrypted_data = base64.b64decode(encrypted_data_b64)
                iv = encrypted_data[:16]
                ciphertext = encrypted_data[16:]

                cipher = AES.new(key, AES.MODE_CBC, iv)
                decrypted_padded = cipher.decrypt(ciphertext)
                decrypted_data_str = unpad(decrypted_padded, AES.block_size).decode('utf-8')
                stream_info = json.loads(decrypted_data_str)
            else:
                s_url = f"{base_url_with_scheme}/ajax/stream?filecode={media_id}"
                s_response = session.get(s_url, headers=headers, timeout=15)
                s_response.raise_for_status()
                response = s_response.text
                stream_info = json.loads(response)

            stream_url = stream_info.get("streaming_url")
            if not stream_url:
                return None, None, None

            stream_headers_dict = {
                "User-Agent": user_agent,
                "Referer": base_url_with_scheme + "/",
                "Origin": base_url_with_scheme
            }
            stream_headers = {'request': stream_headers_dict}

            quality = fetch_resolution_from_m3u8(stream_url, stream_headers_dict) or "unknown"

            return stream_url, quality, stream_headers

    except Exception as e:
        return None, None, None


if __name__ == '__main__':
    from ._test_utils import run_tests
    urls_to_test = [
        "https://streamup.ws/rhNq4BtUoJvsi"
    ]
    run_tests(get_video_from_streamup_player, urls_to_test)
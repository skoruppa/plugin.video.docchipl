import re
import requests
from urllib.parse import urlparse
from Cryptodome.Cipher import AES
from ..utils import get_random_agent
from .utils import fetch_resolution_from_m3u8

DECRYPTION_KEY_HEX = "6b69656d7469656e6d75613931316361"

def _unpad_pkcs7(padded_data: bytes) -> bytes:
    if not padded_data:
        return b''
    pad_value = padded_data[-1]
    if 1 <= pad_value <= AES.block_size and padded_data[-pad_value:] == bytes([pad_value]) * pad_value:
        return padded_data[:-pad_value]
    return padded_data


def _decrypt_to_raw_text(encrypted_hex_str: str, key_hex: str) -> str:
    key_bytes = bytes.fromhex(key_hex)
    full_payload_bytes = bytes.fromhex(encrypted_hex_str.strip())
    iv = full_payload_bytes[:16]
    ciphertext = full_payload_bytes[16:]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted_padded_bytes = cipher.decrypt(ciphertext)
    decrypted_bytes = _unpad_pkcs7(decrypted_padded_bytes)
    return decrypted_bytes.decode('utf-8', errors='ignore')


def get_video_from_upn_player(player_url: str):
    try:
        parsed_url = urlparse(player_url)
        base_url_with_scheme = f"{parsed_url.scheme}://{parsed_url.netloc}"
        headers = {"User-Agent": get_random_agent(), "Referer": f"{base_url_with_scheme}/"}
        
        video_id_match = re.search(r'#([a-zA-Z0-9]+)', player_url)
        if not video_id_match: return None, None, None
        video_id = video_id_match.group(1)
        api_url = f"{base_url_with_scheme}/api/v1/video?id={video_id}&w=1920&h=1200&r="

        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        encrypted_response_hex = response.text
        
        decrypted_text = _decrypt_to_raw_text(encrypted_response_hex, DECRYPTION_KEY_HEX)
        source_match = re.search(r'"source"\s*:\s*"([^"]+)"', decrypted_text)
        if not source_match: return None, None, None
        stream_url = source_match.group(1).replace('\\/', '/')
        
        quality = fetch_resolution_from_m3u8(stream_url, headers) or "unknown"
        stream_headers = {'request': headers}
        return stream_url, quality, stream_headers
    except Exception as e:
        print(f"UPN Player Error: Unexpected error: {e}")
        return None, None, None


if __name__ == '__main__':
    # Poprawiony blok testowy
    from ._test_utils import run_tests
    urls_to_test = [
        "https://mioro.upns.pro/#pubv6n",
        "https://tokyosubs.rpmhub.site/#9prqi",
    ]
    run_tests(get_video_from_upn_player, urls_to_test)
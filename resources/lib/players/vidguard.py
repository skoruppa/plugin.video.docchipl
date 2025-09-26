import re
import json
import base64
import requests
import traceback
import xbmc
from urllib.parse import urlparse, parse_qs, urlencode

from ..utils import get_random_agent, log
from .utils import fetch_resolution_from_m3u8


def _decode_e(hex_string: str, key: int) -> str:
    result = ""
    for i in range(0, len(hex_string), 2):
        hex_byte = hex_string[i:i + 2]
        int_byte = int(hex_byte, 16)
        xored_byte = int_byte ^ key
        result += chr(xored_byte)
    return result


def _decode_f(s: str) -> str:
    reversed_s = s[::-1]
    char_list = list(reversed_s)
    for i in range(0, len(char_list) - 1, 2):
        char_list[i], char_list[i + 1] = char_list[i + 1], char_list[i]
    return "".join(char_list)


def _decode_player_and_get_stream(script_content: str) -> str | None:
    try:
        replacements = {
            "((ﾟｰﾟ)+(ﾟｰﾟ)+(ﾟΘﾟ))": "9", "((o^_^o)+(o^_^o))": "6",
            "((o^_^o)-(ﾟΘﾟ))": "2", "((ﾟｰﾟ)+(o^_^o))": "7",
            "((ﾟｰﾟ)+(ﾟΘﾟ))": "5", "((ﾟｰﾟ)+(ﾟｰﾟ))": "8",
            "(o^_^o)": "3", "(ﾟｰﾟ)": "4", "(ﾟΘﾟ)": "1",
            "(c^_^o)": "0", "(ღ^_^o)": "0"
        }
        sorted_map = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)

        processed_code = script_content.strip()[33:-2]
        processed_code = processed_code.replace(r'\u002b', '+').replace(r'\u0027', "'").replace(r'\/', '/')
        processed_code = processed_code.replace(r'\n', '').replace(r'\\\u0022', '\\"')

        start_marker = "(ﾟɆﾟ)['_']((ﾟɆﾟ)['_']("
        end_marker = "))('_');"
        start_index = processed_code.find(start_marker)
        if start_index == -1: raise ValueError("Nie znaleziono znacznika początku.")
        start_index += len(start_marker)
        end_index = processed_code.rfind(end_marker, start_index)
        if end_index == -1: raise ValueError("Nie znaleziono znacznika końca.")
        payload = processed_code[start_index:end_index]

        payload = re.sub(r'\s+', '', payload)
        for search, replace in sorted_map:
            payload = payload.replace(search, replace)

        def octal_replacer(match):
            num_block = match.group(1)
            octal_string = "".join(filter(str.isdigit, num_block))
            return chr(int(octal_string, 8)) if octal_string else ""

        decoded_with_junk = re.sub(
            r"\(ﾟɆﾟ\)\[ﾟεﾟ\]\+([0-9\+]+)",
            octal_replacer,
            payload
        )

        json_start_index = decoded_with_junk.find('{')
        if json_start_index == -1:
            raise ValueError("Nie znaleziono obiektu JSON w zdekodowanym kodzie.")

        json_end_index = decoded_with_junk.rfind('}')
        if json_end_index == -1:
            raise ValueError("Nie znaleziono końca obiektu JSON.")

        json_string = decoded_with_junk[json_start_index: json_end_index + 1]
        svg_object = json.loads(json_string)

        return svg_object.get('stream')

    except Exception as e:
        log(f"VidGuard Player Decode Error: {e}", xbmc.LOGERROR)
        log(traceback.format_exc(), xbmc.LOGERROR)
        return None


def get_video_from_vidguard_player(player_url: str):
    try:
        parsed_url = urlparse(player_url)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        headers = {
            "User-Agent": get_random_agent(),
            "Referer": origin + '/',
            "Origin": origin,
        }

        response = requests.get(player_url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text

        script_content = None
        script_blocks = re.findall(r"<script[^>]*>(.*?)</script>", html_content, re.DOTALL)
        for block in script_blocks:
            if 'ﾟωﾟ' in block:
                script_content = block.strip()
                break
        if not script_content:
            log("VidGuard Player Error: Could not find the obfuscated script.", xbmc.LOGWARNING)
            return None, None, None

        raw_stream_url = _decode_player_and_get_stream(script_content)
        if not raw_stream_url:
            return None, None, None

        parsed_stream_url = urlparse(raw_stream_url)
        query_params = parse_qs(parsed_stream_url.query)
        if 'sig' in query_params:
            original_sig = query_params['sig'][0]
            step1 = _decode_e(original_sig, 2)
            padding_needed = len(step1) % 4
            if padding_needed: step1 += '=' * (4 - padding_needed)
            try:
                step2 = base64.b64decode(step1).decode('utf-8')
            except Exception as e:
                log(f"VidGuard Base64 Decode Error: {e}", xbmc.LOGERROR)
                return None, None, None
            if len(step2) < 10:
                return None, None, None
            trimmed = step2[5:-5]
            new_sig = _decode_f(trimmed)
            query_params['sig'] = [new_sig]
            new_query = urlencode(query_params, doseq=True)
            final_stream_url = parsed_stream_url._replace(query=new_query).geturl()
        else:
            final_stream_url = raw_stream_url

        stream_headers = {'request': headers}
        quality = fetch_resolution_from_m3u8(final_stream_url, headers) or "unknown"

        return final_stream_url, quality, stream_headers
    except Exception as e:
        log(f"VidGuard Player Error: Unexpected error: {e}", xbmc.LOGERROR)
        log(traceback.format_exc(), xbmc.LOGERROR)
        return None, None, None


if __name__ == '__main__':
    from ._test_utils import run_tests

    urls_to_test = [
        "https://vidguard.to/e/JzkPxzX4NpAObyd"
    ]
    run_tests(get_video_from_vidguard_player, urls_to_test)
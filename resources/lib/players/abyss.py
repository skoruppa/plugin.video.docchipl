import re
import json
import ast
import requests
import traceback
import xbmc
from urllib.parse import quote
from ..utils import get_random_agent, log

def _extract_base64_from_obfuscated_js(obfuscated_code: str) -> str | None:
    try:
        array_match = re.search(r"=\s*(\[.*?\]);", obfuscated_code, re.DOTALL)
        if not array_match:
            log("Abyss Player: Could not find the string array.", xbmc.LOGWARNING)
            return None
        shuffled_array = ast.literal_eval(array_match.group(1))

        target_match = re.search(r"}\((?:_0x[a-f0-9]+),\s*(0x[a-f0-9]+)\)\);", obfuscated_code, re.DOTALL)
        if not target_match:
            log("Abyss Player: Could not find the target checksum.", xbmc.LOGWARNING)
            return None
        target_checksum = int(target_match.group(1), 16)

        offset_match = re.search(r"=\s*_0x[a-f0-9]+\s*-\s*(0x[a-f0-9]+);", obfuscated_code)
        if not offset_match:
            log("Abyss Player: Could not find the index offset.", xbmc.LOGWARNING)
            return None
        INDEX_OFFSET = int(offset_match.group(1), 16)

        checksum_js_expr_match = re.search(r"try\s*\{\s*var\s+.*?=\s*(.*?);", obfuscated_code, re.DOTALL)
        if not checksum_js_expr_match:
            log("Abyss Player: Could not extract the checksum formula.", xbmc.LOGWARNING)
            return None

        checksum_js_expr = checksum_js_expr_match.group(1).replace('\n', '')
        python_expr = re.sub(r"parseInt\(_0x[a-f0-9]+\((0x[a-f0-9]+)\)\)", r"g(\1)", checksum_js_expr)

        def calculate_checksum(arr):
            def g(hex_index_as_int):
                val_str = arr[hex_index_as_int - INDEX_OFFSET]
                num_match = re.match(r"^(-?\d+)", val_str)
                return int(num_match.group(1)) if num_match else 0
            return eval(python_expr, {"g": g}, {})

        i = 0
        max_iterations = len(shuffled_array) * 2
        while i < max_iterations:
            try:
                if int(calculate_checksum(shuffled_array)) == target_checksum:
                    break
            except (ValueError, IndexError):
                pass
            shuffled_array.append(shuffled_array.pop(0))
            i += 1
        else:
            log("Abyss Player: Failed to match checksum after max iterations.", xbmc.LOGWARNING)
            return None

        var_name_match = re.search(r",\s*(_0x[a-f0-9]+)\s*=\s*'lOybFPJO3Q'", obfuscated_code, re.DOTALL)
        if not var_name_match:
            var_name_match = re.search(r",\s*(_0x[a-f0-9]+)\s*=\s*_0x[a-f0-9]+\(0x[a-f0-9]+\)", obfuscated_code, re.DOTALL)
            if not var_name_match:
                log("Abyss Player: Critical error: Could not locate Base64 variable.", xbmc.LOGERROR)
                return None
        var_name = var_name_match.group(1)

        construction_match = re.search(fr"{var_name}\s*=\s*(.*?),\s*_0x[a-f0-9]+\s*=", obfuscated_code, re.DOTALL)
        if not construction_match:
            log(f"Abyss Player: Error: Could not find construction line for {var_name}.", xbmc.LOGERROR)
            return None
        
        construction_string = construction_match.group(1).strip().replace("\n", "")
        parts = construction_string.split('+')
        result_string = ""

        for part in parts:
            part = part.strip()
            if part.startswith("'"):
                result_string += ast.literal_eval(part)
            else:
                hex_arg_match = re.search(r"\((0x[a-f0-9]+)\)", part)
                if hex_arg_match:
                    hex_value = hex_arg_match.group(1)
                    index = int(hex_value, 16)
                    result_string += shuffled_array[index - INDEX_OFFSET]

        return result_string

    except Exception as e:
        log(f"Abyss Player: Unexpected error during JS deobfuscation: {e}", xbmc.LOGERROR)
        log(traceback.format_exc(), xbmc.LOGERROR)
        return None


def _decode_custom_base64_to_bytes(encoded_string: str) -> bytes:
    CUSTOM_ALPHABET = "RB0fpH8ZEyVLkv7c2i6MAJ5u3IKFDxlS1NTsnGaqmXYdUrtzjwObCgQP94hoeW+/="
    DECODING_MAP = {char: index for index, char in enumerate(CUSTOM_ALPHABET)}
    encoded_string = encoded_string.replace('_', '')
    result_bytes = bytearray()
    i = 0
    while i < len(encoded_string):
        chunk = [DECODING_MAP.get(encoded_string[j], 0) for j in range(i, i + 4)]
        byte1 = (chunk[0] << 2) | (chunk[1] >> 4)
        byte2 = ((chunk[1] & 15) << 4) | (chunk[2] >> 2)
        byte3 = ((chunk[2] & 3) << 6) | chunk[3]
        result_bytes.append(byte1)
        if i + 2 < len(encoded_string) and encoded_string[i + 2] != 'v':
            result_bytes.append(byte2)
        if i + 3 < len(encoded_string) and encoded_string[i + 3] != 'v':
            result_bytes.append(byte3)
        i += 4
    return bytes(result_bytes)


def _construct_abyss_stream_url(config_data: dict):
    sources = config_data.get('sources')
    if not sources or not isinstance(sources, list):
        return None, None

    best_source = None
    max_quality = -1
    for source in sources:
        if 'label' in source and ('size' in source or 'ize' in source):
            try:
                quality_num = int(re.sub(r'\D', '', source['label']))
                if quality_num > max_quality:
                    max_quality = quality_num
                    best_source = source
            except (ValueError, TypeError):
                continue
    if not best_source:
        return None, None

    quality_label = best_source.get('label')
    size = best_source.get('size') or best_source.get('ize')
    if 'url' in best_source and 'path' in best_source:
        source_url_to_encode = f"{best_source['url']}/{best_source['path']}"
        encoded_url = quote(source_url_to_encode, safe='')
        final_stream_url = f"https://abysscdn.com/#chunk/{size}/{size}?maxChunkSize=15728640&url={encoded_url}"
        return final_stream_url, quality_label
    elif size and quality_label:
        final_stream_url = f"https://abysscdn.com/#mp4/{size}/{quality_label}"
        return final_stream_url, quality_label
    return None, None


def get_video_from_abyss_player(player_url: str):
    try:
        headers = {"User-Agent": get_random_agent(), "Referer": player_url}

        response = requests.get(player_url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text

        all_scripts = re.findall(r"<script>(.*?)</script>", html_content, re.DOTALL)
        obfuscated_code = None
        for script_content in all_scripts:
            if "var _0x" in script_content and "atob" in script_content:
                obfuscated_code = script_content.strip()
                break

        if not obfuscated_code:
            log("Abyss Player Error: Could not find the obfuscated JS with 'atob'.", xbmc.LOGWARNING)
            return None, None, None

        base64_string = _extract_base64_from_obfuscated_js(obfuscated_code)
        if not base64_string:
            # Błąd został już zalogowany w funkcji pomocniczej
            return None, None, None

        binary_data = _decode_custom_base64_to_bytes(base64_string)
        json_string = binary_data.decode('utf-8', errors='ignore')

        decoder = json.JSONDecoder()
        config_data, _ = decoder.raw_decode(json_string)

        stream_url, quality = _construct_abyss_stream_url(config_data)

        if not stream_url:
            log("Abyss Player Error: Failed to construct the final stream URL.", xbmc.LOGWARNING)
            return None, None, None

        stream_headers = {'request': headers}
        return stream_url, quality, stream_headers

    except requests.exceptions.RequestException as e:
        log(f"Abyss Player Error: Request failed: {e}", xbmc.LOGERROR)
        return None, None, None
    except Exception as e:
        log(f"Abyss Player Error: Unexpected Error: {e}", xbmc.LOGERROR)
        log(traceback.format_exc(), xbmc.LOGERROR)
        return None, None, None


if __name__ == '__main__':
    # Poprawiony blok testowy
    from ._test_utils import run_tests
    urls_to_test = [
        "https://abysscdn.com/?v=50AVrRTHN",
        "https://abysscdn.com/?v=9sT02O89c"
    ]
    run_tests(get_video_from_abyss_player, urls_to_test)
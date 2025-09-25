import re
import requests
import xbmc
from ..utils import log

def unpack_js(encoded_js):
    match = re.search(r"}\('(.*)', *(\d+), *(\d+), *'(.*?)'\.split\('\|'\)", encoded_js)
    if not match: return ""
    payload, radix, count, symtab = match.groups()
    radix, count = int(radix), int(count)
    symtab = symtab.split('|')
    if len(symtab) != count: raise ValueError("Malformed p.a.c.k.e.r symtab")
    def unbase(val):
        alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[:radix]
        base_dict = {char: index for index, char in enumerate(alphabet)}
        result = 0
        for i, char in enumerate(reversed(val)):
            result += base_dict[char] * (radix ** i)
        return result
    def lookup(match):
        word = match.group(0)
        index = unbase(word)
        return symtab[index] if index < len(symtab) else word
    decoded = re.sub(r'\b\w+\b', lookup, payload)
    return decoded.replace('\\', '')

def fetch_resolution_from_m3u8(m3u8_url: str, headers: dict) -> str | None:
    try:
        response = requests.get(m3u8_url, headers=headers, timeout=10)
        response.raise_for_status()
        m3u8_content = response.text
        resolutions = re.findall(r'RESOLUTION=\d+x(\d+)', m3u8_content)
        if resolutions:
            max_resolution = max(int(r) for r in resolutions)
            return f"{max_resolution}p"
    except requests.exceptions.RequestException as e:
        log(f"Could not fetch m3u8 resolution: {e}", level=xbmc.LOGWARNING)
    return None
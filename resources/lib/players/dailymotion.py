import requests
from urllib.parse import urlparse, parse_qs
from ..utils import get_random_agent

DAILYMOTION_URL = "https://www.dailymotion.com"


def get_video_from_dailymotion_player(url: str) -> tuple:
    if '/embed/' not in url:
        url = url.replace('/video/', '/embed/video/')
    
    response = requests.get(url)
    response.raise_for_status()
    html_string = response.text
    try:
        internal_data_start = html_string.find("\"dmInternalData\":") + len("\"dmInternalData\":")
        internal_data_end = html_string.find("</script>", internal_data_start)
        internal_data = html_string[internal_data_start:internal_data_end]

        ts = internal_data.split("\"ts\":", 1)[1].split(",", 1)[0].strip()
        v1st = internal_data.split("\"v1st\":\"", 1)[1].split("\",", 1)[0].strip()

        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_query = query_params.get("video", [None])[0] or parsed_url.path.split("/")[-1]

        json_url = f"{DAILYMOTION_URL}/player/metadata/video/{video_query}?locale=en-US&dmV1st={v1st}&dmTs={ts}&is_native_app=0"
    
        metadata_response = requests.get(json_url)
        metadata_response.raise_for_status()
        parsed = metadata_response.json()

        if "qualities" in parsed and "error" not in parsed:
            return videos_from_daily_response(parsed)
        else:
            return None, None, None
    except Exception:
        return None, None, None


def fetch_m3u8_url(master_url: str, headers: dict) -> tuple:
    response = requests.get(master_url, headers=headers)
    response.raise_for_status()
    m3u8_content = response.text

    streams = []
    lines = m3u8_content.splitlines()

    for i, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF"):
            quality = None
            for part in line.split(","):
                if "NAME" in part:
                    quality = part.split("=")[1].strip("\"")

            if quality:
                stream_url = lines[i + 1]
                streams.append((quality, stream_url))

    if streams:
        best_stream = max(streams, key=lambda x: int(x[0]))
        return best_stream[1], best_stream[0]
    else:
        return None, None


def videos_from_daily_response(parsed: dict) -> tuple:
    master_url = next((q.get("url") for q in parsed.get("qualities", {}).get("auto", []) if "url" in q), None)
    if not master_url:
        return None, None, None
    master_headers = headers_builder()
    best_url, best_quality = fetch_m3u8_url(master_url, master_headers)
    stream_headers = {"request": master_headers}
    return best_url, f"{best_quality}p", stream_headers


def headers_builder() -> dict:
    return {
        "User-Agent": get_random_agent(),
        "Accept": "*/*",
        "Referer": f"{DAILYMOTION_URL}/",
        "Origin": DAILYMOTION_URL
    }
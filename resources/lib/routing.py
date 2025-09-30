import sys
from urllib.parse import parse_qsl, urlencode
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import build_url, log
from .api.docchi import DocchiAPI
from .api.kitsu import KitsuAPI
from .db import kodi_db as db_helper

ADDON = xbmcaddon.Addon()
ADDON_HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
MAX_WORKERS_METADATA = 10
STREAM_RESOLUTION_TIMEOUT = 10

docchi_client = DocchiAPI()
kitsu_client = KitsuAPI()

from .players import cda, okru, sibnet, dailymotion, vk, uqload, gdrive, streamtape, \
    lulustream, savefiles, rumble, vidtube, upn, mp4upload, \
    earnvid, filemoon, streamup, lycoris, vidguard, pixeldrain

PLAYER_MAPPING = {
    'cda': cda.get_video_from_cda_player, 'ok': okru.get_video_from_okru_player,
    'sibnet': sibnet.get_video_from_sibnet_player, 'dailymotion': dailymotion.get_video_from_dailymotion_player,
    'uqload': uqload.get_video_from_uqload_player, 'vk': vk.get_video_from_vk_player,
    'gdrive': gdrive.get_video_from_gdrive_player, 'google drive': gdrive.get_video_from_gdrive_player,
    'lulustream': lulustream.get_video_from_lulustream_player,
    'streamtape': streamtape.get_video_from_streamtape_player,
    'rumble': rumble.get_video_from_rumble_player, 'vidtube': vidtube.get_video_from_vidtube_player,
    'upn': upn.get_video_from_upn_player, 'upns': upn.get_video_from_upn_player, 'rpm': upn.get_video_from_upn_player,
    'rpmhub': upn.get_video_from_upn_player, 'mp4upload': mp4upload.get_video_from_mp4upload_player,
    'earnvid': earnvid.get_video_from_earnvid_player, 'filemoon': filemoon.get_video_from_filemoon_player,
    'streamup': streamup.get_video_from_streamup_player, 'lycoris.cafe': lycoris.get_video_from_lycoris_player,
    'vidguard': vidguard.get_video_from_vidguard_player, 'savefiles': savefiles.get_video_from_savefiles_player,
    'pixeldrain': pixeldrain.get_video_from_pixeldrain_player
}
DEFAULT_PLAYER_MAPPING = {
    'savefiles': savefiles.get_video_from_savefiles_player,
    'bigwarp': savefiles.get_video_from_savefiles_player,
    'streamhls': savefiles.get_video_from_savefiles_player
}


def _process_player(player):
    player_hosting = player['player_hosting'].lower()
    player_url = player['player']
    translator = player['translator_title'] or "Unknown"
    resolver_func = PLAYER_MAPPING.get(player_hosting)
    if not resolver_func and player_hosting == 'default':
        for key, func in DEFAULT_PLAYER_MAPPING.items():
            if key in player_url:
                resolver_func = func
                break
    if resolver_func:
        try:
            url, quality, headers = resolver_func(player_url)
            if url:
                return {'url': url, 'quality': quality or 'unknown', 'hosting': player_hosting,
                        'translator': translator, 'headers': headers}
        except Exception as e:
            log(f"Error processing player {player_hosting}: {e}", xbmc.LOGERROR)
    return None


def main_menu():
    xbmcplugin.setPluginCategory(ADDON_HANDLE, "Docchi.pl")
    menu_items = [
        ("Aktualny Sezon", {'mode': 'list_anime', 'catalog_id': 'season'}),
        ("Popularne", {'mode': 'list_anime', 'catalog_id': 'trending'}),
        ("Najnowsze Odcinki", {'mode': 'list_anime', 'catalog_id': 'latest'}),
        ("Szukaj...", {'mode': 'search'})
    ]
    for label, params in menu_items:
        li = xbmcgui.ListItem(label=label)
        url = build_url(params)
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_anime(catalog_id):
    xbmcplugin.setPluginCategory(ADDON_HANDLE, "Anime")
    try:
        if catalog_id == 'season':
            season, year = docchi_client.get_current_season()
            anime_list = docchi_client.get_seasonal_anime(season, year)
        elif catalog_id == 'trending':
            trending_list_raw = docchi_client.get_trending_anime()

            def get_mal_id_for_item(item):
                slug = item.get('slug')
                if not slug: return None
                db_map = db_helper.get_mapping_by_slug(slug)
                if db_map and db_map.get('mal_id'):
                    item['mal_id'] = db_map['mal_id']
                    return item
                try:
                    details = docchi_client.get_anime_details(slug)
                    if details and details.get('mal_id'):
                        item['mal_id'] = details['mal_id']
                        item['series_type'] = details.get('series_type')
                        return item
                except Exception as e:
                    log(f"Could not fetch details for trending slug {slug}: {e}", xbmc.LOGWARNING)
                return None

            with ThreadPoolExecutor(max_workers=MAX_WORKERS_METADATA) as executor:
                results = executor.map(get_mal_id_for_item, trending_list_raw)
            anime_list = [item for item in results if item]
        elif catalog_id == 'latest':
            anime_list = _process_latest_anime()
        else:
            anime_list = []
    except Exception as e:
        log(f"Failed to fetch anime list for {catalog_id}: {e}", xbmc.LOGERROR)
        anime_list = []
    _populate_anime_list_concurrently(anime_list)


def list_episodes(slug, kitsu_id, media_type):
    xbmcplugin.setPluginCategory(ADDON_HANDLE, "Odcinki")
    try:
        docchi_episodes = docchi_client.get_available_episodes(slug)
        if not isinstance(docchi_episodes, list): docchi_episodes = []
    except Exception as e:
        log(f"Failed to fetch Docchi episodes for {slug}: {e}", xbmc.LOGERROR)
        docchi_episodes = []
    if not docchi_episodes:
        xbmcgui.Dialog().notification("Informacja", "Brak dostępnych odcinków.", xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return
    kitsu_episodes_map = {}
    if kitsu_id:
        all_kitsu_episodes = kitsu_client.get_episodes_by_anime_id(kitsu_id)
        for ep in all_kitsu_episodes:
            num = ep.get('attributes', {}).get('number')
            if num: kitsu_episodes_map[num] = ep
    for docchi_episode in docchi_episodes:
        ep_num = docchi_episode.get('anime_episode_number')
        if not ep_num: continue
        kitsu_meta = kitsu_episodes_map.get(ep_num)
        if kitsu_meta:
            attrs = kitsu_meta.get('attributes', {})
            kitsu_title = (attrs.get('titles') or {}).get('en_us') or (attrs.get('titles') or {}).get('en')
            if kitsu_title:
                title = f"{ep_num}. {kitsu_title}"
            else:
                title = f"Odcinek {ep_num}"
            li = xbmcgui.ListItem(label=title)
            infotag = li.getVideoInfoTag()
            infotag.setTitle(title)
            infotag.setEpisode(ep_num)
            infotag.setPlot(attrs.get('synopsis'))
            infotag.setFirstAired(attrs.get('airdate'))
            thumbnail_obj = attrs.get('thumbnail') or {}
            thumbnail = thumbnail_obj.get('original')
            if thumbnail: li.setArt({'thumb': thumbnail, 'icon': thumbnail})
        else:
            title = f"Odcinek {ep_num}"
            li = xbmcgui.ListItem(label=title)
            infotag = li.getVideoInfoTag()
            infotag.setTitle(title)
            infotag.setEpisode(ep_num)
        if media_type == 'movie':
            infotag.setMediaType('movie')
            xbmcplugin.setContent(ADDON_HANDLE, "movies")
        else:
            infotag.setMediaType('episode')
            xbmcplugin.setContent(ADDON_HANDLE, "episodes")
        li.setProperty('IsPlayable', 'true')

        url = build_url({'mode': 'list_streams', 'slug': slug, 'episode': ep_num, 'title': title})
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def _get_stream_priority(stream):
    hosting = stream['hosting'].lower()
    translator = stream['translator'].lower()
    if hosting == 'lycoris.cafe': return 0
    if 'ai' in translator: return 2
    return 1


def list_streams(slug, episode, title):
    xbmcplugin.setPluginCategory(ADDON_HANDLE, title)

    players = docchi_client.get_episode_players(slug, episode)
    if not players:
        xbmcgui.Dialog().notification("Brak źródeł", "Nie znaleziono odtwarzaczy.", xbmcgui.NOTIFICATION_INFO)
        return

    resolved_streams = []
    with ThreadPoolExecutor(max_workers=len(players)) as executor:
        future_to_player = {executor.submit(_process_player, p): p for p in players}
        try:
            for future in as_completed(future_to_player, timeout=STREAM_RESOLUTION_TIMEOUT):
                result = future.result()
                if result:
                    resolved_streams.append(result)
        except Exception:
            log(f"Stream extractor timed out after {STREAM_RESOLUTION_TIMEOUT}s. Some sources may be missing.",
                xbmc.LOGWARNING)

    if not resolved_streams:
        xbmcgui.Dialog().notification("Brak źródeł",
                                      "Nie udało się przetworzyć żadnego odtwarzacza w wyznaczonym czasie.",
                                      xbmcgui.NOTIFICATION_WARNING)
        return

    resolved_streams.sort(key=_get_stream_priority)
    for stream in resolved_streams:
        label = f"[{stream['hosting'].upper()}] [{stream['quality']}] - {stream['translator']}"
        li = xbmcgui.ListItem(label=label)
        li.setProperty('IsPlayable', 'true')
        if '.m3u8' in stream['url']:
            li.setProperty("inputstream", "inputstream.adaptive")
            li.setProperty("inputstream.adaptive.manifest_type", "hls")
        final_url = stream['url']
        if stream.get('headers') and stream['headers'].get('request'):
            final_url = f"{final_url}|{urlencode(stream['headers']['request'])}"
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=final_url, listitem=li, isFolder=False)
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def search():
    keyboard = xbmc.Keyboard('', 'Szukaj anime')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        display_search_results(keyboard.getText())


def display_search_results(query):
    xbmcplugin.setPluginCategory(ADDON_HANDLE, f"Wyniki dla: {query}")
    try:
        anime_list = docchi_client.search_anime(query)
    except Exception as e:
        log(f"Search failed for '{query}': {e}", xbmc.LOGERROR)
        anime_list = []
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    _populate_anime_list_concurrently(anime_list)


def _fetch_and_prepare_listitem(anime_docchi):
    mal_id = anime_docchi.get('mal_id')
    slug = anime_docchi.get('slug')
    if not (mal_id and slug): return None
    li = xbmcgui.ListItem(label=anime_docchi.get('title'))
    kitsu_id, kitsu_data = None, None
    cached_data = db_helper.get_cached_metadata(mal_id)
    if cached_data:
        log(f"Metadata Cache HIT for mal_id {mal_id}", xbmc.LOGINFO)
        kitsu_data = cached_data
    else:
        log(f"Metadata Cache MISS for mal_id {mal_id}", xbmc.LOGINFO)
        kitsu_data = kitsu_client.get_anime_by_mal_id(mal_id)
        if kitsu_data:
            kitsu_id = kitsu_data.get('id')
            db_helper.set_cached_metadata(mal_id, kitsu_id, kitsu_data)
            db_helper.save_mapping(mal_id, slug, kitsu_id)

    infotag = li.getVideoInfoTag()
    if kitsu_data:
        kitsu_id = kitsu_data.get('id')
        attrs = kitsu_data.get('attributes', {})
        infotag.setTitle(attrs.get('canonicalTitle', anime_docchi.get('title')))
        infotag.setPlot(attrs.get('synopsis'))
        if attrs.get('averageRating'): infotag.setRating(float(attrs.get('averageRating', 0)) / 10)
        if attrs.get('startDate'):
            infotag.setFirstAired(attrs.get('startDate'))
            infotag.setYear(int(attrs.get('startDate').split('-')[0]))
        infotag.setGenres(kitsu_data.get('genres', []))
        kitsu_subtype = (attrs.get('subtype') or 'TV').upper()
        media_type = 'movie' if kitsu_subtype == 'MOVIE' else 'tvshow'
        infotag.setMediaType(media_type)
        art = {'poster': (attrs.get('posterImage') or {}).get('large'),
               'fanart': (attrs.get('coverImage') or {}).get('large'),
               'thumb': (attrs.get('posterImage') or {}).get('small')}
        li.setArt({k: v for k, v in art.items() if v})
    else:
        li.setArt({'icon': 'DefaultVideo.png', 'thumb': anime_docchi.get('cover')})
        docchi_subtype = (anime_docchi.get('series_type') or 'TV').upper()
        media_type = 'movie' if docchi_subtype == 'MOVIE' else 'tvshow'
        infotag.setMediaType(media_type)
        infotag.setTitle(anime_docchi.get('title'))  # Ustawiamy tytuł nawet jeśli nie ma danych z Kitsu

    url = build_url({'mode': 'list_episodes', 'slug': slug, 'kitsu_id': kitsu_id or '', 'media_type': media_type})
    return url, li


def _populate_anime_list_concurrently(anime_list):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_METADATA) as executor:
        results = executor.map(_fetch_and_prepare_listitem, anime_list)
    for result in filter(None, results):
        url, li = result
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.setContent(ADDON_HANDLE, "tvshows")
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def _process_latest_anime():
    season, year = docchi_client.get_current_season()
    latest = docchi_client.get_latest_episodes(season, year)
    unique_anime = {}
    for anime in latest:
        slug = anime.get("anime_id") or anime.get("slug")
        if slug and slug not in unique_anime:
            unique_anime[slug] = {"slug": slug, "cover": anime.get("cover"), "title": anime.get("title")}
    unique_anime_list = list(unique_anime.values())
    for u_anime in unique_anime_list:
        try:
            db_map = db_helper.get_mapping_by_slug(u_anime['slug'])
            if db_map and db_map.get('mal_id'):
                u_anime['mal_id'] = db_map['mal_id']
            else:
                details = docchi_client.get_anime_details(u_anime['slug'])
                u_anime['mal_id'] = details.get('mal_id')
                u_anime['series_type'] = details.get('series_type')
                if u_anime['mal_id']: db_helper.save_mapping(u_anime['mal_id'], u_anime['slug'])
        except Exception:
            u_anime['mal_id'] = None
    return [item for item in unique_anime_list if item.get('mal_id')]


def router():
    path = sys.argv[2][1:] if len(sys.argv) > 2 else ""
    params = dict(parse_qsl(path))
    mode = params.get('mode')
    if mode is None:
        main_menu()
    elif mode == 'list_anime':
        list_anime(params['catalog_id'])
    elif mode == 'list_episodes':
        list_episodes(params.get('slug'), params.get('kitsu_id'), params.get('media_type'))
    elif mode == 'list_streams':
        list_streams(params.get('slug'), params.get('episode'), params.get('title'))
    elif mode == 'search':
        search()
    elif mode == 'display_search_results':
        display_search_results(params.get('query'))
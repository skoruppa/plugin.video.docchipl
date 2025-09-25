import requests
from ..utils import log
import xbmc

BASE_URL = "https://kitsu.io/api/edge"
TIMEOUT = 30


class KitsuAPI:
    @staticmethod
    def get_anime_by_mal_id(mal_id: str):
        if not mal_id: return None
        try:
            mapping_url = f'{BASE_URL}/mappings?filter[externalSite]=myanimelist/anime&filter[externalId]={mal_id}'
            resp_map = requests.get(url=mapping_url, timeout=TIMEOUT)
            resp_map.raise_for_status()
            data_map = resp_map.json()
            related_item_url = data_map['data'][0]['relationships']['item']['links']['related']
            return KitsuAPI.get_anime_details_by_url(related_item_url)
        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            log(f"Kitsu API Error (get_anime_by_mal_id for {mal_id}): {e}", xbmc.LOGWARNING)
            return None

    @staticmethod
    def get_anime_details_by_kitsu_id(kitsu_id: str):
        if not kitsu_id: return None
        details_url = f'{BASE_URL}/anime/{kitsu_id}'
        return KitsuAPI.get_anime_details_by_url(details_url)

    @staticmethod
    def get_anime_details_by_url(url: str):
        try:
            resp_details = requests.get(url=url, timeout=TIMEOUT)
            resp_details.raise_for_status()
            data_details = resp_details.json()
            main_data = data_details.get('data', {})
            if main_data:
                genre_relationships = main_data.get('relationships', {}).get('genres', {}).get('data', [])
                genre_ids = {g['id'] for g in genre_relationships}
                genres = [inc['attributes']['name'] for inc in data_details.get('included', []) if
                          inc['type'] == 'genres' and inc['id'] in genre_ids]
                main_data['genres'] = genres
            return main_data
        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            log(f"Kitsu API Error (get_anime_details_by_url for {url}): {e}", xbmc.LOGWARNING)
            return None

    @staticmethod
    def get_episodes_by_anime_id(kitsu_id: str):
        """
        Pobiera listę WSZYSTKICH odcinków dla danego anime z Kitsu,
        obsługując paginację.
        """
        if not kitsu_id:
            return []

        episodes = []
        url = f'{BASE_URL}/anime/{kitsu_id}/episodes?page[limit]=20&sort=number'

        try:
            while url:
                resp = requests.get(url, timeout=TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
                episodes.extend(data.get('data', []))
                # Przejdź do następnej strony, jeśli istnieje
                url = data.get('links', {}).get('next')
            return episodes
        except (requests.exceptions.RequestException, KeyError) as e:
            log(f"Kitsu API Error (get_episodes for {kitsu_id}): {e}", xbmc.LOGWARNING)
            return []
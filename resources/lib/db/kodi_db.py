import sqlite3
import xbmcaddon
import xbmc
import xbmcvfs
import os
import time
import json
from ..utils import log

# --- Konfiguracja Bazy Danych ---
ADDON = xbmcaddon.Addon()
PROFILE_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
if not xbmcvfs.exists(PROFILE_DIR):
    xbmcvfs.mkdirs(PROFILE_DIR)
DB_PATH = os.path.join(PROFILE_DIR, 'mappings.db')
CACHE_EXPIRY_DAYS = 7  # Jak długo przechowywać metadane w cache (w dniach)


def _get_connection():
    return sqlite3.connect(xbmcvfs.translatePath(DB_PATH))


def init_db():
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            # Tabela do mapowania ID
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mappings (
                    mal_id INTEGER PRIMARY KEY,
                    slug TEXT NOT NULL UNIQUE,
                    kitsu_id TEXT
                )
            """)
            # Tabela do cache'owania metadanych
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    mal_id INTEGER PRIMARY KEY,
                    kitsu_id TEXT,
                    metadata TEXT NOT NULL,
                    cached_at INTEGER NOT NULL
                )
            """)

            # Migracja starej struktury, jeśli istnieje
            cursor.execute("PRAGMA table_info(mappings)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'kitsu_id' not in columns:
                cursor.execute("ALTER TABLE mappings ADD COLUMN kitsu_id TEXT")

            conn.commit()
        log("Baza danych zainicjalizowana pomyślnie.", xbmc.LOGINFO)
    except Exception as e:
        log(f"Krytyczny błąd inicjalizacji bazy danych: {e}", xbmc.LOGERROR)


init_db()


# --- Funkcje Cache Metadanych ---

def get_cached_metadata(mal_id):
    """Sprawdza, czy świeże metadane dla danego mal_id istnieją w cache."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata, cached_at FROM metadata_cache WHERE mal_id = ?", (int(mal_id),))
            result = cursor.fetchone()
            if result:
                metadata_json, cached_at = result
                # Sprawdzamy, czy cache nie wygasł
                if (time.time() - cached_at) < (CACHE_EXPIRY_DAYS * 86400):
                    return json.loads(metadata_json)
                else:
                    # Cache jest przestarzały, usuwamy go
                    _delete_cached_metadata(mal_id)
    except Exception as e:
        log(f"Błąd odczytu z cache dla mal_id {mal_id}: {e}", xbmc.LOGERROR)
    return None


def set_cached_metadata(mal_id, kitsu_id, metadata):
    """Zapisuje metadane do cache."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata)
            current_timestamp = int(time.time())
            cursor.execute(
                "INSERT OR REPLACE INTO metadata_cache (mal_id, kitsu_id, metadata, cached_at) VALUES (?, ?, ?, ?)",
                (int(mal_id), kitsu_id, metadata_json, current_timestamp)
            )
            conn.commit()
    except Exception as e:
        log(f"Błąd zapisu do cache dla mal_id {mal_id}: {e}", xbmc.LOGERROR)


def _delete_cached_metadata(mal_id):
    """Usuwa przestarzały wpis z cache."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metadata_cache WHERE mal_id = ?", (int(mal_id),))
            conn.commit()
    except Exception as e:
        log(f"Błąd usuwania z cache dla mal_id {mal_id}: {e}", xbmc.LOGERROR)


# --- Funkcje Mapowania ID ---

def get_mapping_by_mal_id(mal_id):
    """Pobiera pełne mapowanie (slug, kitsu_id) na podstawie mal_id."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slug, kitsu_id FROM mappings WHERE mal_id = ?", (int(mal_id),))
            result = cursor.fetchone()
            if result:
                return {'slug': result[0], 'kitsu_id': result[1]}
    except Exception as e:
        log(f"Błąd pobierania mapowania dla mal_id {mal_id}: {e}", xbmc.LOGERROR)
    return None


# --- POCZĄTEK POPRAWKI: DODANA BRAKUJĄCA FUNKCJA ---
def get_mapping_by_slug(slug):
    """Pobiera pełne mapowanie (mal_id, kitsu_id) na podstawie sluga."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mal_id, kitsu_id FROM mappings WHERE slug = ?", (slug,))
            result = cursor.fetchone()
            if result:
                return {'mal_id': result[0], 'kitsu_id': result[1]}
    except Exception as e:
        log(f"Błąd pobierania mapowania dla sluga {slug}: {e}", xbmc.LOGERROR)
    return None


# --- KONIEC POPRAWKI ---

def save_mapping(mal_id, slug, kitsu_id=None):
    if not mal_id or not slug:
        return
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO mappings (mal_id, slug, kitsu_id) VALUES (?, ?, ?)",
                (int(mal_id), slug, kitsu_id)
            )
            conn.commit()
    except Exception as e:
        log(f"Błąd zapisu mapowania ({mal_id}<->{slug}): {e}", xbmc.LOGERROR)
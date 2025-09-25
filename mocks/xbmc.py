# Fałszywy moduł xbmc

# Definiujemy stałe, których używa nasza funkcja log()
LOGDEBUG = 0
LOGINFO = 1
LOGWARNING = 2
LOGERROR = 3
LOGFATAL = 4

def log(msg, level=LOGINFO):
    """Prosta funkcja logująca do konsoli zamiast do logów Kodi."""
    print(f"[KODI MOCK LOG] Level {level}: {msg}")

class Keyboard:
    """Atrapa klawiatury do testowania funkcji search."""
    def __init__(self, default='', heading='', hidden=False):
        self._text = "naruto" # Domyślny tekst do testów
        print(f"[KODI MOCK] Keyboard initialized for search.")

    def doModal(self):
        pass

    def isConfirmed(self):
        return True # Zakładamy, że użytkownik zawsze potwierdza

    def getText(self):
        return self._text
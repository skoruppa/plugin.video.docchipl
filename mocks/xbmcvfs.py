# Fałszywy moduł xbmcvfs
import os

def translatePath(path):
    """Zwraca tę samą ścieżkę, co jest wystarczające do testów lokalnych."""
    return path

def mkdirs(path):
    """Tworzy foldery, jeśli nie istnieją."""
    if not os.path.exists(path):
        os.makedirs(path)
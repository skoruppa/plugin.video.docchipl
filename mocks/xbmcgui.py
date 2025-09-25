# Fałszywy moduł xbmcgui

class ListItem:
    def __init__(self, label='', label2='', path=''):
        self.label = label
        print(f"[KODI MOCK] ListItem created: {label}")

    def setProperty(self, key, value):
        pass

    def setInfo(self, type, infoLabels):
        pass

    def setArt(self, dictionary):
        pass


class Dialog:
    def notification(self, heading, message, icon_type, time=5000, sound=True):
        print(f"[KODI MOCK NOTIFICATION] {heading}: {message}")


# Stałe (nieużywane, ale dla kompletności)
NOTIFICATION_INFO = 'info'
NOTIFICATION_WARNING = 'warning'
NOTIFICATION_ERROR = 'error'
# Fałszywy moduł xbmcaddon

class Addon:
    def __init__(self, id='plugin.video.docchipl'):
        self._id = id

    def getAddonInfo(self, info_id):
        if info_id == 'id':
            return self._id
        if info_id == 'name':
            return "Docchi.pl (Mock)"
        if info_id == 'profile':
            # Zwracamy tymczasowy folder w bieżącym katalogu
            import os
            profile_dir = os.path.join(os.getcwd(), '.kodi_mock_profile')
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            return profile_dir
        return ""

    def getSetting(self, key):
        return "" # Zwracamy puste wartości dla ustawień

    def getSettingBool(self, key):
        return False
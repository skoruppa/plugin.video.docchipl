# Fałszywy moduł xbmcplugin

# Potrzebujemy tylko pustych funkcji, aby importy się nie wywalały
# Nasze testy playerów nie używają tych funkcji bezpośrednio.

def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
    pass

def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    pass

def setPluginCategory(handle, category):
    pass

def setResolvedUrl(handle, succeeded, listitem):
    pass
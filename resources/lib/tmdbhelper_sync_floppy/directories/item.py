from tmdbhelper.lib.items.directories.base.basedir_item import BaseDirItem
from tmdbhelper_sync_floppy.settings import FloppySettings


class FloppyDirectoryItem(BaseDirItem):
    priority = 210
    label = 'Floppy'
    params = {'info': 'floppy_directory'}
    types = (None,)

    @property
    def enabled(self):
        return FloppySettings().is_configured

    @property
    def art(self):
        return {'icon': 'DefaultAddonProgram.png'}


class FloppyMenuItem(FloppyDirectoryItem):
    def __init__(self, label, route, tmdb_type='both'):
        self.label = label
        self.params = {'info': route, 'tmdb_type': tmdb_type}


def get_menu_items():
    return [
        FloppyMenuItem('Your Lists', 'floppy_lists'),
        FloppyMenuItem('Watchlist Movies', 'floppy_watchlist', 'movie'),
        FloppyMenuItem('Watchlist TV Shows', 'floppy_watchlist', 'tv'),
        FloppyMenuItem('Collection Movies', 'floppy_collection', 'movie'),
        FloppyMenuItem('Collection TV Shows', 'floppy_collection', 'tv'),
        FloppyMenuItem('Watched Movies', 'floppy_watched', 'movie'),
        FloppyMenuItem('Watched TV Shows', 'floppy_watched', 'tv'),
        FloppyMenuItem('In Progress Movies', 'floppy_progress', 'movie'),
        FloppyMenuItem('In Progress TV Shows', 'floppy_progress', 'tv'),
    ]

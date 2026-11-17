from sys import argv
from xbmc import executebuiltin
from xbmcaddon import Addon


def main():
    addon_id = 'script.module.tmdbhelper.sync.floppy'
    if len(argv) > 1 and argv[1] == 'test_connection':
        from tmdbhelper_lib.sync.providers.interface import SyncProviderLoader
        addon = Addon(addon_id)
        metadata = {'addonid': addon_id, 'path': addon.getAddonInfo('path')}
        provider = SyncProviderLoader(metadata).load()
        from tmdbhelper_sync_floppy.connection import FloppyConnectionTest
        FloppyConnectionTest(provider).run()
        executebuiltin(f'Addon.OpenSettings({addon_id})')
        return
    executebuiltin(
        'RunScript(plugin.video.themoviedb.helper,configure_sync_provider,'
        f'addon_id={addon_id})')


if __name__ == '__main__':
    main()

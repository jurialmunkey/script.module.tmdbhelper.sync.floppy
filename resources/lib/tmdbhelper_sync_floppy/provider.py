from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper.lib.sync.providers.base import SyncProvider
from tmdbhelper_sync_floppy.api import FloppyAPI
from tmdbhelper_sync_floppy.settings import FloppySettings
from tmdbhelper_sync_floppy.sync import synctype, datasync
from tmdbhelper_sync_floppy.actions import basic
from tmdbhelper_sync_floppy.actions.progress import ItemProgress
from tmdbhelper_sync_floppy.actions.userlist import ItemUserList
from tmdbhelper_sync_floppy.directories.item import FloppyDirectoryItem
from tmdbhelper_sync_floppy.directories.routes import LIST_ROUTES
from tmdbhelper_sync_floppy.monitor_lists import FloppyMonitorLists
from tmdbhelper_sync_floppy.scrobbler import ProviderScrobbler


class Provider(SyncProvider):
    interface_version = 3
    provider_id = 'floppy'
    display_name = 'Floppy'
    sync_classes = {
        'SyncWatched': synctype.SyncWatched,
        'SyncPlayback': synctype.SyncPlayback,
        'SyncWatchlist': synctype.SyncWatchlist,
        'SyncCollection': synctype.SyncCollection,
        'SyncNextEpisodes': synctype.SyncNextEpisodes,
        'SyncAllNextEpisodes': synctype.SyncAllNextEpisodes,
        'SyncAiredEpisodes': synctype.SyncAiredEpisodes,
        'SyncHiddenDropped': synctype.SyncHiddenDropped,
    }
    action_classes = {
        'watched': basic.ItemWatched,
        'unwatched': basic.ItemUnwatched,
        'watchlist': basic.ItemWatchlist,
        'collection': basic.ItemCollection,
        'dropped': basic.ItemDropped,
        'progress': ItemProgress,
    }
    service_action_classes = {'floppyuserlist': ItemUserList}
    getter_classes = {
        'movies_to_watch': datasync.FloppyMoviesToWatch,
        'shows_to_watch': datasync.FloppyShowsToWatch,
        'shows_in_progress': datasync.FloppyShowsInProgress,
    }
    directory_item_class = FloppyDirectoryItem
    list_routes = LIST_ROUTES
    monitor_lists_class = FloppyMonitorLists
    scrobbler_class = ProviderScrobbler

    @cached_property
    def settings(self):
        return FloppySettings()

    @cached_property
    def api(self):
        return self.get_api()

    def get_api(self):
        return FloppyAPI(self.settings.server_url, self.settings.api_token)

    def is_authorized(self):
        return self.settings.is_configured

    def get_last_activities(self):
        # Floppy has no last-activities endpoint. Refresh snapshots every ten minutes.
        timestamp = get_timestring_zulu_now()
        return {
            item_type: {
                key: timestamp for key in (
                    'watched_at', 'paused_at', 'watchlisted_at', 'collected_at', 'dropped_at')
            } for item_type in ('movies', 'shows', 'seasons', 'episodes')
        }

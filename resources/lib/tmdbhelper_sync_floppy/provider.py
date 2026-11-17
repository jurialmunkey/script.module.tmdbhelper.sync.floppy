from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper.lib.sync.providers.base import SyncProvider
from tmdbhelper_sync_floppy.api import FloppyAPI
from tmdbhelper_sync_floppy.response import SYNC_ERRORS, describe_error
from tmdbhelper_sync_floppy.settings import FloppySettings
from tmdbhelper_sync_floppy.sync import synctype, datasync
from tmdbhelper_sync_floppy.sync.state import FloppySyncState
from tmdbhelper_sync_floppy.actions import basic
from tmdbhelper_sync_floppy.actions.progress import ItemProgress
from tmdbhelper_sync_floppy.actions.userlist import ItemUserList
from tmdbhelper_sync_floppy.directories.item import FloppyDirectoryItem
from tmdbhelper_sync_floppy.directories.routes import LIST_ROUTES
from tmdbhelper_sync_floppy.monitor_lists import FloppyMonitorLists
from tmdbhelper_sync_floppy.scrobbler import ProviderScrobbler


class Provider(SyncProvider):
    interface_version = 4
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
    activity_keys = ('watched_at', 'paused_at', 'watchlisted_at', 'collected_at', 'dropped_at')
    activity_item_types = ('movies', 'shows', 'seasons', 'episodes')
    # Activity keys backed by a Floppy change feed. Other keys have no activity
    # source, so they report the current time and refresh when their sync expires.
    feed_activity_keys = {'watched_at': 'watched', 'paused_at': 'progress'}

    @cached_property
    def settings(self):
        return FloppySettings()

    @cached_property
    def api(self):
        return self.get_api()

    def get_api(self):
        return FloppyAPI(self.settings.server_url, self.settings.api_token, self.settings.profile)

    def is_authorized(self):
        return self.settings.is_configured

    def validate_setup(self):
        from tmdbhelper_sync_floppy.connection import FloppyConnectionTest
        return FloppyConnectionTest(self).run(show_success=False)

    def get_last_activities(self):
        timestamp = get_timestring_zulu_now()
        activities = dict(
            dict.fromkeys(self.activity_keys, timestamp), **self.get_feed_activities())
        return {item_type: dict(activities) for item_type in self.activity_item_types}

    def get_feed_activities(self):
        if not self.is_authorized():
            return {}
        try:
            state = FloppySyncState(self.api)
            return {
                key: state.get_last_changed(resource)
                for key, resource in self.feed_activity_keys.items()}
        except SYNC_ERRORS as exc:
            # Report the current time so sync retries rather than treating stale data as current.
            kodi_log(f'Floppy last activities: {describe_error(exc)}', 1)
            return {}

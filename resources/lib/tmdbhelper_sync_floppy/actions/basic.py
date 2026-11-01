from tmdbhelper.lib.script.sync.actions import (
    ItemWatched as BasicItemWatched, ItemUnwatched as BasicItemUnwatched,
    ItemWatchlist as BasicItemWatchlist, ItemCollection as BasicItemCollection,
    ItemDropped as BasicItemDropped,
)
from tmdbhelper_sync_floppy.actions.item import ItemSync
from tmdbhelper_sync_floppy.account.watched import FloppyWatchedRequest
from tmdbhelper_sync_floppy.account.watchlist import FloppyWatchlistRequest
from tmdbhelper_sync_floppy.account.collection import FloppyCollectionRequest
from tmdbhelper_sync_floppy.account.dropped import FloppyDroppedRequest


class ItemWatched(ItemSync, BasicItemWatched):
    request_class = FloppyWatchedRequest
    sync_types = ('SyncWatched', 'SyncPlayback', 'SyncWatchlist')
    show_sync_types = ('SyncNextEpisodes', 'SyncAllNextEpisodes', 'SyncAiredEpisodes')

    def get_sync_dependencies(self):
        # Watchlist membership is stored on the show, so a season or episode
        # action must refresh the show's watchlist rather than the episode's.
        dependencies = super().get_sync_dependencies()
        if self.base_item_type != 'show':
            return dependencies
        return tuple(
            item for item in dependencies if item[0] != 'SyncWatchlist'
        ) + (('SyncWatchlist', 'show'),)


class ItemUnwatched(ItemWatched, BasicItemUnwatched):
    pass


class ItemWatchlist(ItemSync, BasicItemWatchlist):
    request_class = FloppyWatchlistRequest


class ItemCollection(ItemSync, BasicItemCollection):
    request_class = FloppyCollectionRequest
    allow_seasons = True

    def get_sync_value(self):
        return self.syncdata.get_value(
            self.tmdb_type, self.tmdb_id, self.season, self.episode,
            key=self.sync_key, item_type=self.item_type)


class ItemDropped(ItemSync, BasicItemDropped):
    request_class = FloppyDroppedRequest
    sync_types = ('SyncHiddenDropped', 'SyncWatchlist', 'SyncNextEpisodes', 'SyncAiredEpisodes')

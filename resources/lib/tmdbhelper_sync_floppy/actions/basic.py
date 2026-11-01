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

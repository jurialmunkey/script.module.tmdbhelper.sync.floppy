from tmdbhelper_sync_floppy.sync.datatype import FloppyDataType, FloppyTVDataType
from tmdbhelper_sync_floppy.sync.snapshot import (
    FloppyWatchlistSnapshot, FloppyCollectionSnapshot, FloppyWatchedSnapshot,
    FloppyPlaybackSnapshot, FloppyNextEpisodesSnapshot, FloppyAllNextEpisodesSnapshot,
    FloppyDroppedSnapshot,
)


class SyncWatchlist(FloppyDataType):
    keys = ('rank', 'listed_at', 'notes')
    key_prefix = 'watchlist'
    method = 'watchlist'
    last_activities_key = 'watchlisted_at'
    snapshot_class = FloppyWatchlistSnapshot

    def get_response_sync(self, *args, **kwargs):
        if self.item_type not in ('movie', 'show'):
            return []
        return super().get_response_sync(*args, **kwargs)


class SyncCollection(FloppyTVDataType):
    keys = ('last_collected_at', 'last_updated_at')
    key_prefix = 'collection'
    method = 'collection'
    last_activities_key = 'collected_at'
    snapshot_class = FloppyCollectionSnapshot


class SyncWatched(FloppyTVDataType):
    keys = ('plays', 'last_watched_at', 'watched_episodes')
    method = 'watched'
    last_activities_key = 'watched_at'
    snapshot_class = FloppyWatchedSnapshot


class SyncPlayback(FloppyTVDataType):
    keys = ('progress', 'paused_at', 'id')
    key_prefix = 'playback'
    method = 'playback'
    last_activities_key = 'paused_at'
    snapshot_class = FloppyPlaybackSnapshot


class SyncNextEpisodes(FloppyTVDataType):
    keys = ('next_episode_id', 'next_episode_aired_at', 'aired_episodes')
    method = 'next_episodes'
    last_activities_key = 'watched_at'
    snapshot_class = FloppyNextEpisodesSnapshot


class SyncAiredEpisodes(SyncNextEpisodes):
    keys = ('aired_episodes',)
    method = 'aired_episodes'


class SyncAllNextEpisodes(FloppyTVDataType):
    keys = ('upnext_episode_id',)
    method = 'all_next_episodes'
    last_activities_key = 'watched_at'
    snapshot_class = FloppyAllNextEpisodesSnapshot


class SyncHiddenDropped(FloppyTVDataType):
    keys = ('hidden_at',)
    key_prefix = 'dropped'
    method = 'dropped'
    last_activities_key = 'dropped_at'
    snapshot_class = FloppyDroppedSnapshot

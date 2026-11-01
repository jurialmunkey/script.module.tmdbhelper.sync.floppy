from tmdbhelper.lib.sync.datasync import (
    SyncDataGetterAll, SyncDataGetterAllMoviesToWatch, SyncDataGetterAllShowsToWatch,
)


class FloppyMoviesToWatch(SyncDataGetterAllMoviesToWatch):
    pass


class FloppyShowsToWatch(SyncDataGetterAllShowsToWatch):
    query_clauses = ('item_type=?', 'dropped_hidden_at IS NULL')
    filter_keys = ('dropped_hidden_at',)


class FloppyShowsInProgress(SyncDataGetterAll):
    query_clauses = (
        'item_type=?', 'dropped_hidden_at IS NULL',
        'last_watched_at IS NOT NULL', 'watched_episodes < aired_episodes',
    )
    clause_keys = ('next_episode_id',)
    additional_keys = ()

    @property
    def query_values(self):
        return ('show',)

    def get_keys(self):
        return (
            *super().get_keys(), 'last_watched_at', 'watched_episodes',
            'aired_episodes', 'dropped_hidden_at')

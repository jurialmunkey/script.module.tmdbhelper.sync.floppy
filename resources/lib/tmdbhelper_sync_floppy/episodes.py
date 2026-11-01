from itertools import chain
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper_sync_floppy.dates import utc_timestamp
from tmdbhelper_sync_floppy.media import FloppyMedia


class FloppyEpisodes:
    def __init__(self, api, tmdb_id, season=None, skip_hidden=False):
        self.api = api
        self.tmdb_id = tmdb_id
        self.season = season
        self.skip_hidden = skip_hidden

    @cached_property
    def seasons(self):
        return self.get_seasons()

    def get_seasons(self):
        path = self.api.media_path('tv', self.tmdb_id)
        entries = self.api.get_snapshot(f'{path}/seasons')
        return [
            item for item in entries
            if (self.season is None and item['item']['season_number'] > 0
                or item['item']['season_number'] == self.season)
            and (not self.skip_hidden or item['status'] not in (2, 4))
        ]

    def get_season_episodes(self, season):
        path = self.api.media_path('tv', self.tmdb_id, season['item']['season_number'])
        return self.api.get_snapshot(f'{path}/episodes')

    def get_records(self):
        entries = chain.from_iterable(self.get_season_episodes(season) for season in self.seasons)
        media = (FloppyMedia(entry) for entry in entries)
        now = get_timestring_zulu_now()
        return [
            item.record for item in media
            if item.is_supported and item.item.get('release_datetime')
            and utc_timestamp(item.item['release_datetime']) <= now
        ]

from xbmc import Monitor
from tmdbhelper_sync_floppy.episodes import FloppyEpisodes
from tmdbhelper_sync_floppy.response import FloppyError, FloppyResponse


class FloppyItemRequest:
    def __init__(self, api, tmdb_type, tmdb_id, season=None, episode=None):
        self.api = api
        self.tmdb_type = tmdb_type
        self.tmdb_id = int(tmdb_id)
        self.season = int(season) if season is not None else None
        self.episode = int(episode) if episode is not None else None

    @property
    def path(self):
        return self.api.media_path(self.tmdb_type, self.tmdb_id, self.season, self.episode)

    def get_targets(self):
        if self.tmdb_type == 'movie' or self.episode is not None:
            return [(self.season, self.episode)]
        return [
            (item['season_number'], item['episode_number'])
            for item in FloppyEpisodes(self.api, self.tmdb_id, self.season).get_records()
        ]

    def run(self, remove):
        targets = self.get_targets()
        if not targets:
            raise FloppyError('No released episodes are available for this action', 404)
        targets = self.filter_targets(targets, remove)
        monitor = Monitor()
        response = FloppyResponse(204)
        for season, episode in targets:
            if monitor.abortRequested():
                raise FloppyError('Floppy action cancelled', 499)
            response = self.send(remove, season, episode)
            response.require_success()
        return response

    def filter_targets(self, targets, remove):
        return targets

    def send(self, remove, season, episode):
        raise NotImplementedError

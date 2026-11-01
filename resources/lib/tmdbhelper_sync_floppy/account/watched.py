from uuid import uuid4
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper_sync_floppy.account.item import FloppyItemRequest
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyWatchedRequest(FloppyItemRequest):
    def filter_targets(self, targets, remove):
        # Marking a show or season watched should not add a second play to
        # episodes that are already watched.
        if remove or self.tmdb_type == 'movie' or self.episode is not None:
            return targets
        from tmdbhelper_sync_floppy.sync.snapshot import FloppyWatchedSnapshot
        try:
            watched = FloppyWatchedSnapshot(self.api, 'show').get_watched_episode_keys(self.tmdb_id)
        except FloppyError as exc:
            # Watched state can be unavailable (e.g. while Floppy initialises sync).
            # Fall back to recording every target rather than blocking the action.
            kodi_log(f'Floppy watched state unavailable, recording all episodes: {exc}', 1)
            return targets
        return [
            (season, episode) for season, episode in targets
            if (self.tmdb_id, season, episode) not in watched]

    def send(self, remove, season, episode):
        if remove:
            media_type = 'movie' if self.tmdb_type == 'movie' else 'episode'
            path = self.api.media_path(media_type, self.tmdb_id)
            params = {'season_number': season, 'episode_number': episode}
            return self.api.request(
                f'{path}/watched-state', method='PUT',
                data={'watched': False, 'client_event_id': str(uuid4())}, params=params)
        path = self.api.media_path(self.tmdb_type, self.tmdb_id)
        if episode is not None:
            path = f'{path}/{season}/episodes/{episode}'
        return self.api.request(
            f'{path}/watch', method='POST', data={'external_id': f'tmdbhelper:{uuid4()}'})

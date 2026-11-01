from uuid import uuid4
from tmdbhelper_sync_floppy.account.item import FloppyItemRequest


class FloppyWatchedRequest(FloppyItemRequest):
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

from uuid import uuid4
from tmdbhelper.lib.monitor.scrobble import ScrobbleRequest, ScrobbleResult


class ProviderScrobbler(ScrobbleRequest):
    def get_scrobbler_item(self):
        player = self.player
        if player.tmdb_type == 'movie':
            media_type = 'movie'
        elif player.tmdb_type == 'tv' and player.season >= 0 and player.episode > 0:
            media_type = 'episode'
        else:
            return None
        payload = {
            'media_type': media_type,
            'ids': {'tmdb': str(player.tmdb_id)},
            'position_seconds': int(player.current_time),
            'duration_seconds': int(player.total_time),
        }
        if media_type == 'episode':
            payload.update(season_number=player.season, episode_number=player.episode)
        return payload

    def send_request(self, method, payload):
        payload.update(
            action=method, completed=self.player.progress >= 80,
            client_event_id=f'tmdbhelper:{uuid4()}')
        response = self.provider.api.request('scrobble', method='POST', data=payload)
        if method == 'pause' and response.status_code == 200:
            # Floppy start/pause only update Now Playing; persist pause positions explicitly.
            saved = self.provider.api.request('playback/progress', method='PUT', data=payload)
            if saved.status_code not in (200, 201, 204):
                return saved
        return response

    def get_result(self, method, response):
        successful = response.status_code in (200, 201, 204)
        return ScrobbleResult(
            successful, successful and method == 'stop' and self.player.progress >= 80)

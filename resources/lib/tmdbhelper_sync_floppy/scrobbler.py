from uuid import uuid4
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.monitor.scrobble import ScrobbleRequest, ScrobbleResult
from tmdbhelper_sync_floppy.response import (
    FloppyResponse, SUCCESS_CODES, SYNC_ERRORS, describe_error,
)


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
        # Runs inside TMDbHelper's player monitor, so never let an error escape.
        try:
            return self.post_scrobble(method, payload)
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy scrobble {method}: {describe_error(exc)}', 1)
            return FloppyResponse(502)

    def post_scrobble(self, method, payload):
        payload.update(
            action=method, completed=self.player.progress >= 80,
            client_event_id=f'tmdbhelper:{uuid4()}')
        # Floppy saves the resume position on "stop", including incomplete stops.
        # "start" and "pause" only update Now Playing. TMDbHelper currently sends
        # only start and stop, so the pause branch is for a future TMDbHelper that
        # forwards pauses.
        response = self.provider.api.request('scrobble', method='POST', data=payload)
        if method == 'pause' and response.status_code in SUCCESS_CODES:
            saved = self.provider.api.request('playback/progress', method='PUT', data=payload)
            if saved.status_code not in SUCCESS_CODES:
                return saved
        return response

    def get_result(self, method, response):
        successful = response.status_code in SUCCESS_CODES
        return ScrobbleResult(
            successful, successful and method == 'stop' and self.player.progress >= 80)

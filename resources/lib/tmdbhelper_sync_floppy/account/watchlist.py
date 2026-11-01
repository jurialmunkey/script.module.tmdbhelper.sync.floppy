from tmdbhelper_sync_floppy.account.item import FloppyItemRequest
from tmdbhelper_sync_floppy.media import FloppyMedia
from tmdbhelper_sync_floppy.response import FloppyError, FloppyResponse


class FloppyWatchlistRequest(FloppyItemRequest):
    def run(self, remove):
        entries = self.api.get_media(self.tmdb_type, status=0)
        planning = [
            entry for entry in entries
            if FloppyMedia(entry).tmdb_id == self.tmdb_id]
        if not remove:
            if planning:
                return FloppyResponse(204)
            return self.api.request(
                f'media/{self.tmdb_type}', method='POST',
                data={'source': 'tmdb', 'media_id': str(self.tmdb_id), 'status': 'Planning'})
        if not planning:
            return FloppyResponse(204)
        history = self.api.get_items(f'{self.path}/history')
        planning_ids = {entry['consumption_id'] for entry in history if entry['status'] == 0}
        if any(entry['consumption_id'] not in planning_ids for entry in planning):
            raise FloppyError(
                'Floppy does not expose this Planning entry in consumption history; '
                'remove it in Floppy to preserve existing plays', 409)
        response = FloppyResponse(204)
        for entry in planning:
            response = self.api.request(
                f'{self.path}/history/{entry["consumption_id"]}', method='DELETE')
            response.require_success()
        return response

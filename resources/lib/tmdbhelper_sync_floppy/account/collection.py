from tmdbhelper_sync_floppy.account.item import FloppyItemRequest
from tmdbhelper_sync_floppy.media import FloppyMedia
from tmdbhelper_sync_floppy.response import FloppyResponse


class FloppyCollectionRequest(FloppyItemRequest):
    def send(self, remove, season, episode):
        path = self.api.media_path(self.tmdb_type, self.tmdb_id)
        if episode is not None:
            path = f'{path}/{season}/episodes/{episode}'
        return self.api.request(f'{path}/collection', method='PUT', data={})

    def matches(self, entry):
        item = FloppyMedia(entry)
        if not item.is_supported or item.tmdb_id != self.tmdb_id:
            return False
        if (item.item_type == 'movie') != (self.tmdb_type == 'movie'):
            return False
        if self.season is not None and item.record['season_number'] != self.season:
            return False
        if self.episode is not None and item.record['episode_number'] != self.episode:
            return False
        return True

    def run(self, remove):
        if not remove:
            return super().run(remove)
        entries = [entry for entry in self.api.get_items('collection') if self.matches(entry)]
        response = FloppyResponse(204)
        for entry in entries:
            response = self.api.request(f'collection/{entry["id"]}', method='DELETE')
            response.require_success()
        return response

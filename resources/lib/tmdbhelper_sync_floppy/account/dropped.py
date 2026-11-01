from tmdbhelper_sync_floppy.account.item import FloppyItemRequest
from tmdbhelper_sync_floppy.response import FloppyResponse


class FloppyDroppedRequest(FloppyItemRequest):
    def run(self, remove):
        entries = self.api.get_details(self.tmdb_type, self.tmdb_id)['consumptions']
        pending = [
            entry for entry in entries
            if entry['status'] == 4 or not remove and entry['status'] in (0, 1, 2)
        ]
        if pending:
            entry = max(pending, key=lambda item: item['consumption_id'])
            return self.api.request(
                f'{self.path}/history/{entry["consumption_id"]}', method='PATCH',
                data={'status': 'In progress' if remove else 'Dropped'})
        if remove:
            return FloppyResponse(204)
        return self.api.request(
            'media/tv', method='POST',
            data={'source': 'tmdb', 'media_id': str(self.tmdb_id), 'status': 'Dropped'})

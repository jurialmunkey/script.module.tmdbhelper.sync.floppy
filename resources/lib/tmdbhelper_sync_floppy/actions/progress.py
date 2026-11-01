from tmdbhelper.lib.script.sync.progress import ItemProgress as BasicItemProgress
from tmdbhelper_sync_floppy.actions.item import ItemSync


class ItemProgress(ItemSync, BasicItemProgress):
    sync_types = ('SyncPlayback',)

    def send_request(self):
        payload = {
            'media_type': 'movie' if self.item_type == 'movie' else 'episode',
            'ids': {'tmdb': str(self.tmdb_id)},
        }
        if self.item_type == 'episode':
            payload.update(season_number=int(self.season), episode_number=int(self.episode))
        return self.api.request('playback/progress', method='DELETE', data=payload)

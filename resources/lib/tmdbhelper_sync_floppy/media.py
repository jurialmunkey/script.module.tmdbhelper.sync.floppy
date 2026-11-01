from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import try_int


class FloppyMedia:
    item_types = {'movie': 'movie', 'tv': 'show', 'season': 'season', 'episode': 'episode'}

    def __init__(self, entry):
        self.entry = entry

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        return self.entry.get('item') or self.entry

    @cached_property
    def item_type(self):
        return self.item_types.get(self.item['media_type'])

    @cached_property
    def ids(self):
        return self.get_ids()

    def get_ids(self):
        ids = dict(self.item.get('ids') or {})
        if self.item['source'] == 'tmdb':
            # Floppy uses the parent show's provider id for seasons and episodes.
            ids['tmdb'] = self.item['media_id']
        return ids

    @cached_property
    def tmdb_id(self):
        return try_int(self.ids.get('tmdb')) or None

    @property
    def is_supported(self):
        return bool(self.item_type and self.tmdb_id)

    @cached_property
    def record(self):
        return self.get_record()

    def get_record(self):
        premiered = self.item.get('release_datetime')
        return {
            'item_type': self.item_type,
            'tmdb_type': 'movie' if self.item_type == 'movie' else 'tv',
            'tmdb_id': self.tmdb_id,
            'season_number': self.item.get('season_number'),
            'episode_number': self.item.get('episode_number'),
            'title': self.item.get('title'),
            'year': try_int(premiered[:4]) if premiered else None,
            'premiered': premiered[:10] if premiered else None,
            'runtime': self.item.get('runtime_minutes', 0) * 60 if self.item.get('runtime_minutes') else None,
        }

from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.consts import RUNSCRIPT
from tmdbhelper.lib.addon.plugin import get_localized
from tmdbhelper.lib.items.directories.mapper_basic import ItemMapper
from tmdbhelper_sync_floppy.media import FloppyMedia


class FloppyMenuMapper(ItemMapper):
    @cached_property
    def builder(self):
        return self.meta.item_builder(self.meta, self.meta.params['tmdb_type'])

    @cached_property
    def label(self):
        return self.builder.label

    def get_params(self):
        return self.builder.params

    def get_art(self):
        return self.builder.art

    def get_infoproperties(self):
        return self.builder.infoproperties.copy()


class FloppyListMapper(ItemMapper):
    @cached_property
    def label(self):
        return self.meta['name']

    def get_infolabels(self):
        return {'plot': self.meta.get('description')}

    def get_art(self):
        return {'icon': self.meta.get('image') or 'DefaultFolder.png'}

    def get_infoproperties(self):
        return {'items': self.meta['items_count']}

    def get_params(self):
        return {
            'info': 'floppy_userlist', 'list_id': str(self.meta['id']),
            'tmdb_type': 'both', 'plugin_category': self.label,
        }

    def get_context_menu(self):
        return [(
            get_localized(20444),
            RUNSCRIPT.format(f'user_list={self.meta["id"]},user_slug=__api_floppy__'),
        )]


class FloppyItemMapper(ItemMapper):
    list_id = None
    list_editable = False

    @cached_property
    def label(self):
        return self.record['title'] or ''

    def get_params(self):
        return {
            'info': 'details', 'tmdb_type': self.record['tmdb_type'],
            'tmdb_id': self.record['tmdb_id'],
            'season': self.record['season_number'], 'episode': self.record['episode_number'],
        }

    def get_infoproperties(self):
        return {
            'tmdb_type': self.record['tmdb_type'], 'tmdb_id': self.record['tmdb_id'],
            'floppy_list_id': str(self.list_id) if self.list_id is not None else None,
            'floppy_list_editable': 'True' if self.list_editable else None,
        }


class FloppyMediaMapper(FloppyItemMapper):
    @cached_property
    def media(self):
        return FloppyMedia(self.meta)

    @cached_property
    def record(self):
        return self.media.record

    def get_infolabels(self):
        return {
            'title': self.label,
            'mediatype': 'tvshow' if self.record['item_type'] == 'show' else self.record['item_type'],
            'year': self.record['year'], 'premiered': self.record['premiered'],
            'duration': self.record['runtime'], 'plot': self.media.item.get('synopsis'),
            'season': self.record['season_number'], 'episode': self.record['episode_number'],
        }

    def get_art(self):
        return {
            'thumb': self.media.item.get('image'),
            'fanart': self.media.item.get('backdrop'),
        }

    def get_unique_ids(self):
        return self.media.ids

    def get_item(self):
        if not self.media.is_supported:
            return {}
        return super().get_item()


class FloppyRecordMapper(FloppyItemMapper):
    """Directory output from a normalized provider snapshot, without database access."""

    @cached_property
    def record(self):
        return self.meta

    def get_infolabels(self):
        return {
            'title': self.label, 'year': self.record.get('year'),
            'mediatype': 'tvshow' if self.record['item_type'] == 'show' else self.record['item_type'],
            'season': self.record.get('season_number'), 'episode': self.record.get('episode_number'),
        }

    def get_unique_ids(self):
        return {'tmdb': self.record['tmdb_id']}

from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.items.directories.mapper_basic import ItemMapper
from tmdbhelper.lib.sync.providers.monitor_lists import MonitorListsSupplier
from jurialmunkey.ftools import cached_property
from tmdbhelper_sync_floppy.media import FloppyMedia
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyMonitorListMapper(ItemMapper):
    @cached_property
    def label(self):
        return f'Floppy: {self.meta["name"]}'

    def get_params(self):
        return {'user_slug': self.meta['user_slug'], 'list_slug': str(self.meta['id'])}


class FloppyMonitorItemMapper:
    def __init__(self, entry):
        self.media = FloppyMedia(entry)

    @property
    def item(self):
        if not self.media.is_supported or self.media.item_type not in ('movie', 'show'):
            return None
        item_type = self.media.item_type
        return {
            'type': item_type,
            item_type: {
                'title': self.media.item['title'],
                'ids': {'tmdb': self.media.tmdb_id, 'imdb': self.media.ids.get('imdb')},
            },
        }


class FloppyMonitorLists(MonitorListsSupplier):
    item_mapper_class = FloppyMonitorListMapper

    def get_mapped_item(self, item, add_infoproperties=None):
        return self.item_mapper_class(item, add_infoproperties).item

    def get_lists(self):
        if not self.provider.is_authorized():
            return []
        try:
            entries = self.provider.api.get_lists()
        except FloppyError as exc:
            kodi_log(f'Floppy monitored lists: {exc}', 1)
            return []
        watchlists = [
            {'id': f'watchlist/{media_type}', 'name': f'Watchlist {label}'}
            for media_type, label in (('movie', 'Movies'), ('tv', 'TV Shows'))
        ]
        return [
            self.get_mapped_item(dict(item, user_slug=self.user_slug))
            for item in watchlists + entries
        ]

    def get_list_items(self, list_slug):
        if not self.provider.is_authorized():
            return None
        try:
            if list_slug in ('watchlist/movie', 'watchlist/tv'):
                entries = self.provider.api.get_media(list_slug.split('/')[1], status=0)
            else:
                entries = self.provider.api.get_list_items(list_slug)
            return [
                item for item in (FloppyMonitorItemMapper(entry).item for entry in entries)
                if item is not None
            ]
        except FloppyError as exc:
            kodi_log(f'Floppy monitored list: {exc}', 1)
            return None

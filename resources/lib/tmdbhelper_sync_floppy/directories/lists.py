from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.items.directories.lists_default import ListDefault, ListProperties
from tmdbhelper.lib.items.directories.tmdb.lists_standard import ListStandard, ListStandardProperties
from tmdbhelper.lib.sync.providers.registry import SyncProviderRegistry
from tmdbhelper_sync_floppy.directories.item import get_menu_items
from tmdbhelper_sync_floppy.directories.mapper import (
    FloppyMenuMapper, FloppyListMapper, FloppyMediaMapper, FloppyRecordMapper,
)
from tmdbhelper_sync_floppy.response import SYNC_ERRORS, describe_error
from tmdbhelper_sync_floppy.sync.snapshot import (
    FloppyWatchlistSnapshot, FloppyCollectionSnapshot, FloppyWatchedSnapshot,
    FloppyPlaybackSnapshot, FloppyNextEpisodesSnapshot,
)


class FloppyProperties(ListProperties):
    item_mapper_class = FloppyMenuMapper
    container_content = ''

    @cached_property
    def entries(self):
        return self.get_entries()

    def get_entries(self):
        return get_menu_items() if self.provider.is_authorized() else []

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        try:
            return [self.get_mapped_item(item) for item in self.entries]
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy directory: {describe_error(exc)}', 1)
            return []

    def get_mapped_item(self, item, add_infoproperties=None):
        return self.item_mapper_class(item, add_infoproperties).item


class FloppyListsProperties(FloppyProperties):
    item_mapper_class = FloppyListMapper

    def get_entries(self):
        return self.provider.api.get_lists() if self.provider.is_authorized() else []


class ListFloppyDirectory(ListDefault):
    list_properties_class = FloppyProperties
    kodi_details = False

    def configure_list_properties(self, list_properties):
        list_properties = super().configure_list_properties(list_properties)
        list_properties.provider = SyncProviderRegistry().get_provider('floppy')
        list_properties.plugin_name = 'Floppy'
        list_properties.pagination = False
        return list_properties

    def get_items(self, tmdb_type=None, **kwargs):
        self.list_properties.tmdb_type = tmdb_type or 'both'
        return self.get_items_finalised()


class ListFloppyLists(ListFloppyDirectory):
    list_properties_class = FloppyListsProperties


class FloppyUserListProperties(ListStandardProperties):
    item_mapper_class = FloppyMediaMapper

    @cached_property
    def url(self):
        return f'lists/{int(self.list_id)}/items'

    def get_cached_items(self, *args, **kwargs):
        return self.get_uncached_items()

    @cached_property
    def list_editable(self):
        try:
            return self.provider.api.is_editable_list(self.list_id)
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy list permissions: {describe_error(exc)}', 1)
            return False

    def get_api_response(self, page=1):
        if not self.provider.is_authorized():
            return None
        try:
            data = self.provider.api.read(
                self.url,
                params={'limit': 20, 'offset': (page - 1) * 20})
            total = data['pagination']['total']
            return {
                'results': data['results'], 'total_results': total,
                'total_pages': (total + 19) // 20,
            }
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy list: {describe_error(exc)}', 1)
            return None

    def get_mapped_item(self, item, add_infoproperties=None):
        mapper = self.item_mapper_class(item, add_infoproperties)
        mapper.list_id = self.list_id
        mapper.list_editable = self.list_editable
        return mapper.item


class ListFloppyUserList(ListStandard):
    list_properties_class = FloppyUserListProperties

    def configure_list_properties(self, list_properties):
        list_properties = super().configure_list_properties(list_properties)
        list_properties.provider = SyncProviderRegistry().get_provider('floppy')
        list_properties.plugin_name = 'Floppy'
        list_properties.page_length = 1
        return list_properties

    def get_items(self, list_id, tmdb_type=None, **kwargs):
        self.list_properties.list_id = list_id
        return super().get_items(tmdb_type=tmdb_type or 'both', **kwargs)


class FloppySnapshotProperties(FloppyProperties):
    item_mapper_class = FloppyRecordMapper
    snapshot_class = FloppyWatchlistSnapshot

    @property
    def container_content(self):
        return 'movies' if self.tmdb_type == 'movie' else 'tvshows'

    def get_entries(self):
        if not self.provider.is_authorized():
            return []
        item_type = 'movie' if self.tmdb_type == 'movie' else 'show'
        items = self.snapshot_class(self.provider.api, item_type).get_items()
        return [item for item in items if item['item_type'] == item_type]


class ListFloppyWatchlist(ListFloppyDirectory):
    list_properties_class = FloppySnapshotProperties
    kodi_details = True


class FloppyCollectionProperties(FloppySnapshotProperties):
    snapshot_class = FloppyCollectionSnapshot


class ListFloppyCollection(ListFloppyWatchlist):
    list_properties_class = FloppyCollectionProperties


class FloppyWatchedProperties(FloppySnapshotProperties):
    snapshot_class = FloppyWatchedSnapshot


class ListFloppyWatched(ListFloppyWatchlist):
    list_properties_class = FloppyWatchedProperties


class FloppyProgressProperties(FloppySnapshotProperties):
    def get_entries(self):
        if not self.provider.is_authorized():
            return []
        if self.tmdb_type == 'movie':
            return FloppyPlaybackSnapshot(self.provider.api, 'movie').get_items()
        return [
            item for item in FloppyNextEpisodesSnapshot(self.provider.api, 'show').get_items()
            if item['next_episode_id']
        ]


class ListFloppyProgress(ListFloppyWatchlist):
    list_properties_class = FloppyProgressProperties

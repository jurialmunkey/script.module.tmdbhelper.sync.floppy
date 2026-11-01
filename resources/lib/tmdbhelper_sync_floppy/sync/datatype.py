from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.sync.datatype import DataType, DataTypeEpisodesInShows
from tmdbhelper_sync_floppy.response import SYNC_ERRORS, describe_error
from tmdbhelper_sync_floppy.sync.itemdata import FloppySyncItem


class FloppyDataType(DataType):
    expiry_time = 600

    def get_response_sync(self, *args, **kwargs):
        if not self.provider.is_authorized():
            return None
        try:
            return self.snapshot_class(self.provider.api, self.item_type).get_items()
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy sync {self.method}: {describe_error(exc)}', 1)
            return None

    def get_syncitem(self, meta):
        item = FloppySyncItem(self.item_type, meta, self.keys, key_prefix=self.key_prefix)
        # Validate and map before shared DataType clears the previous snapshot.
        item.data
        return item


class FloppyTVDataType(DataTypeEpisodesInShows, FloppyDataType):
    pass

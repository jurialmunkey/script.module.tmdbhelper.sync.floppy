from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.plugin import get_infolabel, get_localized
from tmdbhelper_sync_floppy.actions.item import ItemAction
from tmdbhelper_sync_floppy.response import FloppyError
from tmdbhelper_sync_floppy.settings import FloppySettings


class ItemUserList(ItemAction):
    preconfigured = True

    @cached_property
    def lists(self):
        return self.api.get_editable_lists()

    def get_remove(self):
        return bool(
            get_infolabel('ListItem.Property(floppy_list_id)')
            and get_infolabel('ListItem.Property(floppy_list_editable)') == 'True')

    def get_name(self):
        return get_localized(32355 if self.remove else 32298)

    def get_list_id(self):
        if self.remove:
            list_id = get_infolabel('ListItem.Property(floppy_list_id)')
            if not self.api.is_editable_list(list_id):
                raise FloppyError('This Floppy list is read-only', 403)
            return list_id
        if not self.lists:
            Dialog().ok('Floppy', FloppySettings().addon.getLocalizedString(32005))
            return None
        selected = Dialog().select(get_localized(32298), [item['name'] for item in self.lists])
        return None if selected == -1 else self.lists[selected]['id']

    def send_request(self):
        list_id = self.get_list_id()
        if list_id is None:
            return None
        path = self.api.media_path(self.tmdb_type, self.tmdb_id)
        return self.api.request(
            f'{path}/lists/{int(list_id)}', method='DELETE' if self.remove else 'PUT',
            data={} if not self.remove else None)

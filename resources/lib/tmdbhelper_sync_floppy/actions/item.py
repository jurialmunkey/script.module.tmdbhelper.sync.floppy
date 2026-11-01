from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.dialog import busy_decorator
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.script.sync.provider import ItemSync as ProviderItemSync
from tmdbhelper.lib.script.sync.request import ItemSync as RequestItemSync
from tmdbhelper_sync_floppy.response import FloppyError, FloppyResponse, SYNC_ERRORS, describe_error


class ItemAction(RequestItemSync):
    service_name = 'Floppy'

    @cached_property
    def api(self):
        return self.sync_provider.api

    @property
    def is_available(self):
        return self.sync_provider.is_authorized()

    def get_self(self):
        if not self.is_available:
            return None
        return super().get_self()

    @busy_decorator
    def get_sync_response(self):
        before = self.api.mutation_count
        try:
            response = self.send_request()
        except FloppyError as exc:
            response = FloppyResponse(exc.status_code, {'detail': str(exc)})
        except SYNC_ERRORS as exc:
            kodi_log(f'Floppy action: {describe_error(exc)}', 1)
            response = FloppyResponse(502, {'detail': 'Floppy returned an unexpected response'})
        if response is not None:
            response.changed = self.api.mutation_count != before
        return response

    def send_request(self):
        raise NotImplementedError

    def get_status_code_message(self):
        detail = self.sync_response.json().get('detail')
        return f'Floppy: {detail}' if detail else super().get_status_code_message()


class ItemSync(ProviderItemSync, ItemAction):
    def send_request(self):
        request = self.request_class(
            self.api, self.tmdb_type, self.tmdb_id, self.season, self.episode)
        return request.run(self.remove)

    def reset_lastactivities(self):
        # A multi-episode operation can change some entries before a later failure.
        if self.sync_response is not None and self.sync_response.changed:
            self.get_sync_invalidator().run()

    def refresh_containers(self):
        if self.sync_response is not None and self.sync_response.changed:
            from tmdbhelper.lib.script.method.kodi_utils import container_refresh
            container_refresh()
            return
        super().refresh_containers()

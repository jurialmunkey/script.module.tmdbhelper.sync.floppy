from xbmcgui import Dialog
from tmdbhelper.lib.addon.dialog import busy_decorator
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyConnectionTest:
    read_checks = (
        ('watchlist:read', 'media/movie', {'limit': 1}),
        ('progress:read', 'playback/progress', {'limit': 1}),
        ('lists:read', 'lists', {'limit': 1}),
        ('sync:read', 'sync/connections', None),
    )

    def __init__(self, provider):
        self.provider = provider
        self.settings = provider.settings

    def get_localized(self, string_id):
        return self.settings.addon.getLocalizedString(string_id)

    def check_settings(self):
        if not self.settings.server_url:
            raise FloppyError(self.get_localized(32009))
        if not self.settings.api_token:
            raise FloppyError(self.get_localized(32010))

    def check_permission(self, scope, path, params):
        response = self.provider.api.request(path, params=params)
        try:
            data = response.require_success()
        except FloppyError as exc:
            raise FloppyError(
                self.get_localized(32012).format(scope, str(exc), exc.status_code),
                exc.status_code,
            ) from None
        try:
            if not isinstance(data['results'], list):
                raise TypeError
        except (KeyError, TypeError):
            raise FloppyError(self.get_localized(32013).format(scope)) from None

    @busy_decorator
    def check(self):
        self.check_settings()
        for scope, path, params in self.read_checks:
            self.check_permission(scope, path, params)

    def run(self, show_success=True):
        heading = self.get_localized(32007)
        try:
            self.check()
        except (FloppyError, ValueError) as exc:
            Dialog().ok(heading, str(exc))
            return False
        if show_success:
            Dialog().ok(heading, self.get_localized(32011))
        return True

from urllib.parse import urlsplit, urlunsplit
from xbmcaddon import Addon


class FloppySettings:
    addon_id = 'script.module.tmdbhelper.sync.floppy'

    def __init__(self):
        self.addon = Addon(self.addon_id)

    @property
    def server_url(self):
        value = self.addon.getSetting('server_url').strip().rstrip('/')
        if not value:
            return ''
        parts = urlsplit(value)
        if parts.scheme not in ('http', 'https') or not parts.hostname:
            raise ValueError('Floppy server URL must be an HTTP or HTTPS address')
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError('Floppy server URL must not contain credentials, a query or a fragment')
        path = parts.path.rstrip('/')
        if path.endswith('/api/v1'):
            path = path[:-7]
        return urlunsplit((parts.scheme, parts.netloc, path, '', ''))

    @property
    def api_token(self):
        return self.addon.getSetting('api_token').strip()

    @property
    def is_configured(self):
        return bool(self.server_url and self.api_token)

from urllib.parse import quote
from time import monotonic
from requests import Session, RequestException
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper_sync_floppy.pagination import FloppyPagination
from tmdbhelper_sync_floppy.response import FloppyResponse, SUCCESS_CODES


class FloppyAPI:
    timeout = 30

    def __init__(self, server_url, api_token):
        self.server_url = server_url
        self.api_token = api_token
        self.snapshots = {}
        self.mutation_count = 0

    @cached_property
    def session(self):
        return self.get_session()

    def get_session(self):
        session = Session()
        session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json',
        })
        return session

    def request(self, path, method='GET', data=None, params=None):
        url = f'{self.server_url}/api/v1/{path.strip("/")}/'
        try:
            response = self.session.request(
                method, url, json=data, params=params, timeout=self.timeout,
                allow_redirects=False)
        except RequestException as exc:
            # Exception messages can contain URLs or credentials. Log only the type.
            kodi_log(f'Floppy: {method} {path}: {type(exc).__name__}', 1)
            return FloppyResponse(503, {'detail': 'Unable to connect to Floppy'})
        status_code = response.status_code
        success = status_code in SUCCESS_CODES
        is_write = method != 'GET' and path != 'sync/bootstrap'
        changed = False
        if not success:
            kodi_log(f'Floppy: {method} {path}: HTTP {status_code}', 1)
        elif is_write:
            # Record the write before reading the body: a successful write with an
            # unreadable body has still changed server state.
            self.snapshots.clear()
            self.mutation_count += 1
            changed = True
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = None
        if not isinstance(body, dict):
            if success and not is_write:
                return FloppyResponse(502, {
                    'detail': f'Floppy returned an invalid response for {path}'})
            body = {} if success else {'detail': f'HTTP {status_code}'}
        return FloppyResponse(status_code, body, changed=changed)

    def read(self, path, params=None):
        return self.request(path, params=params).require_success()

    def get_items(self, path, params=None):
        return FloppyPagination(self, path, params).get_items()

    def get_snapshot(self, path, params=None):
        key = (path, tuple(sorted((params or {}).items())))
        return self.get_cached_snapshot(key, lambda: self.get_items(path, params))

    def get_cached_snapshot(self, key, getter):
        try:
            timestamp, items = self.snapshots[key]
        except KeyError:
            pass
        else:
            if monotonic() - timestamp < 30:
                return items
        items = getter()
        self.snapshots[key] = (monotonic(), items)
        return items

    def get_media(self, media_type, status=None):
        params = {'status': status} if status is not None else {}
        return self.get_snapshot(f'media/{media_type}', params)

    @staticmethod
    def media_path(media_type, tmdb_id, season=None, episode=None):
        path = f'media/{media_type}/tmdb/{quote(str(tmdb_id), safe="")}'
        if season is not None:
            path = f'{path}/{int(season)}'
        if episode is not None:
            path = f'{path}/{int(episode)}'
        return path

    def get_details(self, media_type, tmdb_id, season=None, episode=None):
        return self.read(self.media_path(media_type, tmdb_id, season, episode))

    def get_lists(self):
        return self.get_items('lists')

    def get_list_items(self, list_id):
        return self.get_items(f'lists/{int(list_id)}/items')

    def get_editable_lists(self):
        return [item for item in self.get_lists() if self.is_editable_list(item['id'])]

    def is_editable_list(self, list_id):
        response = self.request(f'lists/{int(list_id)}/smart-rules')
        if response.status_code == 403:
            return False
        return not response.require_success()['is_smart']

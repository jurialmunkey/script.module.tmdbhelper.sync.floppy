from xbmc import Monitor
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyPagination:
    limit = 200

    def __init__(self, api, path, params=None):
        self.api = api
        self.path = path
        self.params = dict(params or {})

    def get_page(self, offset):
        return self.api.read(
            self.path, params=dict(self.params, limit=self.limit, offset=offset))

    def get_items(self):
        monitor = Monitor()
        offset = 0
        total = None
        items = []
        while not monitor.abortRequested():
            page = self.get_page(offset)
            pagination = page['pagination']
            page_total = pagination['total']
            limit = pagination['limit']
            entries = page['results']
            if total is not None and total != page_total:
                raise FloppyError('Floppy list changed during pagination; retry the snapshot')
            total = page_total
            if limit <= 0 or pagination['offset'] != offset:
                raise FloppyError('Floppy returned an invalid pagination position')
            if len(entries) != min(limit, max(total - offset, 0)):
                raise FloppyError('Floppy returned an incomplete page')
            items.extend(entries)
            offset += limit
            if offset >= total:
                return items
        raise FloppyError('Floppy request cancelled', 499)

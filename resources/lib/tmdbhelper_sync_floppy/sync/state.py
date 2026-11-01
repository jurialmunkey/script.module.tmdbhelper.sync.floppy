from xbmc import Monitor
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyWatchedState:
    """Read a complete canonical baseline and replay concurrent changes."""

    def __init__(self, api):
        self.api = api

    def get_items(self):
        bootstrap = self.api.request('sync/bootstrap', method='POST', data={}).require_success()
        if bootstrap['contract'] != 2:
            raise FloppyError('Floppy watched sync requires contract 2')
        self.context = bootstrap['context']
        self.cursor = bootstrap['cursors']['watched']
        states = self.get_baseline()
        self.replay_changes(states)
        return list(states.values())

    def get_baseline(self):
        states = {}
        after = None
        positions = set()
        monitor = Monitor()
        while not monitor.abortRequested():
            page = self.api.read('sync/snapshot', params={
                'context': self.context, 'resource': 'watched',
                'after': after, 'limit': 200,
            })
            if page['resource'] != 'watched' or page['cursor'] != self.cursor:
                raise FloppyError('Floppy snapshot baseline changed')
            states.update({item['item_id']: item for item in page['results']})
            if not page['has_more']:
                return states
            after = page['after']
            if not after or after in positions:
                raise FloppyError('Floppy repeated a snapshot continuation')
            positions.add(after)
        raise FloppyError('Floppy request cancelled', 499)

    def replay_changes(self, states):
        monitor = Monitor()
        while not monitor.abortRequested():
            page = self.api.read('sync/changes', params={
                'contract': 2, 'context': self.context,
                'cursor': self.cursor, 'limit': 200,
            })
            if not page['complete']:
                raise FloppyError('Floppy returned an incomplete watched change feed')
            for item in page['results']:
                if item['item_id'] is None:
                    raise FloppyError('Floppy change omitted its item identity; retry the snapshot')
                if item['kind'] == 'delete':
                    states.pop(item['item_id'], None)
                else:
                    states[item['item_id']] = item
            cursor = page['next_cursor']
            if page['has_more'] and cursor <= self.cursor:
                raise FloppyError('Floppy repeated a watched change cursor')
            self.cursor = cursor
            if not page['has_more']:
                return
        raise FloppyError('Floppy request cancelled', 499)

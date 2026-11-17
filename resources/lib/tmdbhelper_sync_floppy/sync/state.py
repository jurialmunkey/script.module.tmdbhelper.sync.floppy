from xbmc import Monitor
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu_now
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyResourceState:
    """Maintain one resource's canonical rows within a shared sync checkpoint."""

    resource = None
    limit = 200

    def __init__(self, api, checkpoint):
        self.api = api
        self.checkpoint = checkpoint

    @property
    def states(self):
        return self.checkpoint['items'][self.resource]

    @property
    def cursor(self):
        return self.checkpoint['cursors'][self.resource]

    @cursor.setter
    def cursor(self, value):
        self.checkpoint['cursors'][self.resource] = value

    def mark_changed(self):
        self.checkpoint['changed_at'][self.resource] = get_timestring_zulu_now()

    def initialize(self):
        self.checkpoint['items'][self.resource] = {}
        self.get_baseline()
        self.mark_changed()

    def get_baseline(self):
        after = None
        positions = set()
        monitor = Monitor()
        while not monitor.abortRequested():
            page = self.api.read_url(self.checkpoint['snapshots'][self.resource], params={
                'context': self.checkpoint['context'], 'resource': self.resource,
                'after': after, 'limit': self.limit,
            })
            if page['resource'] != self.resource or page['cursor'] != self.cursor:
                raise FloppyError(f'Floppy {self.resource} snapshot baseline changed')
            self.apply_rows(page['results'])
            if not page['has_more']:
                return
            after = page['after']
            if not after or after in positions:
                raise FloppyError(f'Floppy repeated a {self.resource} snapshot continuation')
            positions.add(after)
        raise FloppyError('Floppy request cancelled', 499)

    def replay_changes(self):
        """Apply changes after the stored cursor. Returns True when the checkpoint changed."""
        changed = False
        monitor = Monitor()
        while not monitor.abortRequested():
            page = self.api.read_url(self.checkpoint['feeds'][self.resource], params={
                'contract': 2, 'context': self.checkpoint['context'],
                'cursor': self.cursor, 'limit': self.limit,
            })
            if not page['complete']:
                raise FloppyError(f'Floppy returned an incomplete {self.resource} change feed')
            if page['generation'] != self.checkpoint['generation']:
                raise FloppyError(
                    f'Floppy {self.resource} generation changed', code='sync_reset_required')
            if page['results']:
                self.apply_rows(page['results'])
                self.mark_changed()
            cursor = page['next_cursor']
            if cursor < self.cursor or (page['has_more'] and cursor == self.cursor):
                raise FloppyError(f'Floppy repeated a {self.resource} change cursor')
            changed = changed or bool(page['results']) or cursor != self.cursor
            self.cursor = cursor
            if not page['has_more']:
                return changed
        raise FloppyError('Floppy request cancelled', 499)

    def apply_rows(self, rows):
        for row in rows:
            self.apply_row(row)

    def apply_row(self, row):
        if row['item_id'] is None:
            raise FloppyError(f'Floppy {self.resource} row omitted its item identity')
        key = str(row['item_id'])
        if row.get('kind') == 'delete':
            self.states.pop(key, None)
            return
        self.states[key] = self.get_row(row, self.states.get(key))

    def get_row(self, row, previous):
        return row


class FloppyWatchedResourceState(FloppyResourceState):
    resource = 'watched'


class FloppyProgressResourceState(FloppyResourceState):
    resource = 'progress'
    position_keys = ('position_seconds', 'duration_seconds', 'completed')

    def get_row(self, row, previous):
        # Floppy can omit updated_at from progress rows. Keep the previous time for
        # an unchanged position so it does not appear as a new pause.
        if row.get('updated_at'):
            return row
        return dict(
            row,
            updated_at=self.get_previous_updated_at(row, previous) or get_timestring_zulu_now())

    def get_previous_updated_at(self, row, previous):
        if previous is None:
            return None
        if any(previous.get(key) != row.get(key) for key in self.position_keys):
            return None
        return previous.get('updated_at')


class FloppySyncState:
    """Maintain canonical watched and progress snapshots from one bootstrap context."""

    resource_classes = (FloppyWatchedResourceState, FloppyProgressResourceState)
    reset_codes = (
        'sync_reset_required',
        'cursor_expired',
        'cursor_invalid',
        'sync_not_initialized',
        'invalid_context',
        'invalid_page',
    )

    def __init__(self, api):
        self.api = api

    def get_cached_checkpoint(self):
        return self.api.get_cached_snapshot('sync_state', self.get_checkpoint)

    def get_items(self, resource):
        return list(self.get_cached_checkpoint()['items'][resource].values())

    def get_last_changed(self, resource):
        return self.get_cached_checkpoint()['changed_at'][resource]

    def get_resources(self, checkpoint):
        return [resource_class(self.api, checkpoint) for resource_class in self.resource_classes]

    def get_checkpoint(self):
        store = self.api.sync_store
        with store.lock() as lock:
            if lock.lockstate == -1:
                raise FloppyError('Floppy request cancelled while waiting for sync storage', 499)
            checkpoint, changed = self.get_current_checkpoint(store.load())
            if changed:
                store.save(checkpoint)
        return checkpoint

    def get_current_checkpoint(self, checkpoint):
        if checkpoint is None:
            return self.get_initial_checkpoint(), True
        try:
            # Evaluate every resource so that each cursor advances.
            changed = [resource.replay_changes() for resource in self.get_resources(checkpoint)]
        except FloppyError as exc:
            if exc.code not in self.reset_codes:
                raise
            return self.get_initial_checkpoint(), True
        return checkpoint, any(changed)

    def get_initial_checkpoint(self):
        bootstrap = self.api.request('sync/bootstrap', method='POST', data={}).require_success()
        if bootstrap['contract'] != 2:
            raise FloppyError('Floppy sync requires contract 2')
        resources = [resource_class.resource for resource_class in self.resource_classes]
        checkpoint = {
            'context': bootstrap['context'],
            'generation': bootstrap['generation'],
            'cursors': {resource: bootstrap['cursors'][resource] for resource in resources},
            'feeds': {resource: bootstrap['feeds'][resource] for resource in resources},
            'snapshots': {resource: bootstrap['snapshots'][resource] for resource in resources},
            'changed_at': {},
            'items': {},
        }
        for resource in self.get_resources(checkpoint):
            resource.initialize()
        for resource in self.get_resources(checkpoint):
            resource.replay_changes()
        return checkpoint

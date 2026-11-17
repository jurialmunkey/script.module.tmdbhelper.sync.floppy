from contextlib import closing
from hashlib import sha256
from json import dumps, loads
from os import makedirs, remove
from os.path import join
from sqlite3 import Error, connect
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.files.sqlite_mutex import SQLiteMutex
from tmdbhelper_sync_floppy.response import FloppyError


class FloppySyncStore:
    """Persist source states and their shared checkpoint as one account-scoped snapshot."""

    legacy_filename = 'watched.db'

    def __init__(self, profile, server_url, api_token):
        self.profile = profile
        self.path = join(profile, 'sync.db')
        self.account_key = sha256(dumps([server_url, api_token]).encode('utf-8')).hexdigest()
        try:
            makedirs(profile, exist_ok=True)
            with closing(connect(self.path)) as connection, connection:
                connection.execute(
                    'CREATE TABLE IF NOT EXISTS sync_v1 '
                    '(account TEXT PRIMARY KEY, data TEXT NOT NULL)'
                )
        except (OSError, Error) as exc:
            raise FloppyError('Unable to initialize Floppy sync storage') from exc
        self.remove_legacy()

    def remove_legacy(self):
        # Watched-only checkpoints were replaced by the shared watched/progress checkpoint.
        try:
            remove(join(self.profile, self.legacy_filename))
        except FileNotFoundError:
            pass
        except OSError as exc:
            # The legacy file is unused, so a locked copy must not block sync.
            kodi_log(f'Floppy: unable to remove legacy watched storage ({type(exc).__name__})', 1)

    def lock(self):
        try:
            return SQLiteMutex(f'{self.path}.{self.account_key}', timeout=300)
        except (OSError, Error) as exc:
            raise FloppyError('Unable to lock Floppy sync storage') from exc

    def load(self):
        try:
            with closing(connect(self.path)) as connection:
                row = connection.execute(
                    'SELECT data FROM sync_v1 WHERE account=?',
                    (self.account_key,),
                ).fetchone()
        except Error as exc:
            raise FloppyError('Unable to read Floppy sync storage') from exc
        return loads(row[0]) if row is not None else None

    def save(self, checkpoint):
        data = dumps(checkpoint)
        try:
            with closing(connect(self.path)) as connection, connection:
                connection.execute(
                    'INSERT OR REPLACE INTO sync_v1 (account, data) VALUES (?, ?)',
                    (self.account_key, data),
                )
        except Error as exc:
            raise FloppyError('Unable to save Floppy sync storage') from exc

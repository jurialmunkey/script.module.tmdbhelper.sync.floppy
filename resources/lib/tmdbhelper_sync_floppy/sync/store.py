from contextlib import closing
from hashlib import sha256
from json import dumps, loads
from os import makedirs
from os.path import join
from sqlite3 import Error, connect
from tmdbhelper.lib.files.sqlite_mutex import SQLiteMutex
from tmdbhelper_sync_floppy.response import FloppyError


class FloppyWatchedStore:
    """Persist source state and its checkpoint as one account-scoped snapshot."""

    def __init__(self, profile, server_url, api_token):
        self.path = join(profile, 'watched.db')
        self.account_key = sha256(dumps([server_url, api_token]).encode('utf-8')).hexdigest()
        try:
            makedirs(profile, exist_ok=True)
            with closing(connect(self.path)) as connection, connection:
                connection.execute(
                    'CREATE TABLE IF NOT EXISTS watched_v1 '
                    '(account TEXT PRIMARY KEY, data TEXT NOT NULL)'
                )
        except (OSError, Error) as exc:
            raise FloppyError('Unable to initialize Floppy watched storage') from exc

    def lock(self):
        try:
            return SQLiteMutex(f'{self.path}.{self.account_key}', timeout=300)
        except (OSError, Error) as exc:
            raise FloppyError('Unable to lock Floppy watched storage') from exc

    def load(self):
        try:
            with closing(connect(self.path)) as connection:
                row = connection.execute(
                    'SELECT data FROM watched_v1 WHERE account=?',
                    (self.account_key,),
                ).fetchone()
        except Error as exc:
            raise FloppyError('Unable to read Floppy watched storage') from exc
        return loads(row[0]) if row is not None else None

    def save(self, checkpoint):
        data = dumps(checkpoint)
        try:
            with closing(connect(self.path)) as connection, connection:
                connection.execute(
                    'INSERT OR REPLACE INTO watched_v1 (account, data) VALUES (?, ?)',
                    (self.account_key, data),
                )
        except Error as exc:
            raise FloppyError('Unable to save Floppy watched storage') from exc

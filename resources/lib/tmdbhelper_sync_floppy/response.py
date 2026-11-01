SUCCESS_CODES = (200, 201, 204)


class FloppyError(RuntimeError):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


# Errors that an unexpected Floppy payload can raise while it is read or mapped.
# Entry points called by TMDbHelper catch these so that one bad response fails
# only the Floppy operation and leaves cached sync data unchanged.
SYNC_ERRORS = (FloppyError, KeyError, IndexError, TypeError, ValueError, AttributeError)


def describe_error(exc):
    if isinstance(exc, FloppyError):
        return str(exc)
    return f'unexpected response ({type(exc).__name__}: {exc})'


class FloppyResponse:
    def __init__(self, status_code=200, data=None, changed=False):
        self.status_code = status_code
        self.data = {} if data is None else data
        self.changed = changed

    def json(self):
        return self.data

    def require_success(self):
        if self.status_code not in SUCCESS_CODES:
            raise FloppyError(
                self.data.get('detail') or f'HTTP {self.status_code}',
                self.status_code)
        return self.data

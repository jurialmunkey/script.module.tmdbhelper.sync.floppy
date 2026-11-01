class FloppyError(RuntimeError):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


class FloppyResponse:
    def __init__(self, status_code=200, data=None, changed=False):
        self.status_code = status_code
        self.data = {} if data is None else data
        self.changed = changed

    def json(self):
        return self.data

    def require_success(self):
        if self.status_code not in (200, 201, 204):
            raise FloppyError(
                self.data.get('detail') or f'HTTP {self.status_code}',
                self.status_code)
        return self.data

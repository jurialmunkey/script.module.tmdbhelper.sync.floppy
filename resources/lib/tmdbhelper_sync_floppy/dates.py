from datetime import datetime, timezone
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu


def utc_timestamp(value):
    if not value:
        return None
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return get_timestring_zulu(date.astimezone(timezone.utc))

import re
from datetime import datetime, timezone
from tmdbhelper.lib.addon.tmdate import get_timestring_zulu

# Python before 3.11 only parses fractional seconds of exactly 3 or 6 digits.
FRACTION = re.compile(r'\.(\d+)')


def utc_timestamp(value):
    if not value:
        return None
    value = value.replace('Z', '+00:00')
    value = FRACTION.sub(lambda match: f'.{match.group(1)[:6].ljust(6, "0")}', value, count=1)
    date = datetime.fromisoformat(value)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return get_timestring_zulu(date.astimezone(timezone.utc))

import datetime

import dateutil
import dateutil.parser


HUMAN_BOOLS = {
    'true': True,
    'false': False,
    '1': True,
    '0': False,
    '': False,
    'on': True,
    'off': False,
}


def to_human_bool(value):
    return {True: 'true', False: 'false'}[bool(value)]


def from_human_bool(text):
    return HUMAN_BOOLS.get((text or '').lower(), True)


def safe_int(value, default=None):
    try:
        return int(value)
    except:
        return value


def parse_date(date, force_safe=False):
    parts = date.split('-')
    if force_safe and len(parts) > 1 and (safe_int(parts[1], 0) <= 0 or safe_int(parts[1], 13) >= 13):
        # Force 01 for invalid value
        parts[1] = '01'
    if force_safe and len(parts) > 2 and (safe_int(parts[2], 0) <= 0 or safe_int(parts[2], 32) >= 32):
        # Force 01 for invalid value
        parts[2] = '01'
    date = '-'.join(parts)
    return datetime.date(*dateutil.parser.parse(date).timetuple()[:3])

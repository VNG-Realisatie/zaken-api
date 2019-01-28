from datetime import datetime

from django.utils import timezone

import dateutil.parser

ZAAK_READ_KWARGS = {
    'HTTP_ACCEPT_CRS': 'EPSG:4326',
}

ZAAK_WRITE_KWARGS = {
    'HTTP_ACCEPT_CRS': 'EPSG:4326',
    'HTTP_CONTENT_CRS': 'EPSG:4326',
}


def utcdatetime(*args, **kwargs) -> datetime:
    return datetime(*args, **kwargs).replace(tzinfo=timezone.utc)


def isodatetime(*args, **kwargs) -> str:
    dt = utcdatetime(*args, **kwargs)
    return dt.isoformat()


def parse_isodatetime(val) -> datetime:
    return dateutil.parser.parse(val)

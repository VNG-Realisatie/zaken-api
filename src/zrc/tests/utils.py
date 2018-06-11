from datetime import datetime

from django.utils import timezone


def utcdatetime(*args, **kwargs) -> datetime:
    return datetime(*args, **kwargs).replace(tzinfo=timezone.utc)


def isodatetime(*args, **kwargs) -> str:
    dt = utcdatetime(*args, **kwargs)
    return dt.isoformat()

from datetime import datetime

from django.utils import timezone


def isodatetime(*args, **kwargs) -> str:
    dt = datetime(*args, **kwargs).replace(tzinfo=timezone.utc)
    return dt.isoformat()

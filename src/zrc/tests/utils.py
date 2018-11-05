from datetime import datetime

from django.conf import settings
from django.utils import timezone

import dateutil.parser
import jwt


def utcdatetime(*args, **kwargs) -> datetime:
    return datetime(*args, **kwargs).replace(tzinfo=timezone.utc)


def isodatetime(*args, **kwargs) -> str:
    dt = utcdatetime(*args, **kwargs)
    return dt.isoformat()


def parse_isodatetime(val) -> datetime:
    return dateutil.parser.parse(val)


def generate_jwt(scopes: list, secret: str=None) -> str:
    if secret is None:
        secret = settings.JWT_SECRET

    payload = {
        'scopes': scopes,
    }
    encoded = jwt.encode(payload, secret, algorithm='HS256')
    return encoded

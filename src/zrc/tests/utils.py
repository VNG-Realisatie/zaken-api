import os
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from zrc.utils import parse_isodatetime  # noqa

ZAAK_READ_KWARGS = {"HTTP_ACCEPT_CRS": "EPSG:4326"}

ZAAK_WRITE_KWARGS = {"HTTP_ACCEPT_CRS": "EPSG:4326", "HTTP_CONTENT_CRS": "EPSG:4326"}


def utcdatetime(*args, **kwargs) -> datetime:
    return datetime(*args, **kwargs).replace(tzinfo=timezone.utc)


def isodatetime(*args, **kwargs) -> str:
    dt = utcdatetime(*args, **kwargs)
    return dt.isoformat()


def get_oas_spec(service):
    spec_dirs = settings.TEST_SPEC_DIRS

    try:
        filepath = next((os.path.join(path, f"{service}.yaml") for path in spec_dirs))
    except StopIteration:
        raise IOError(f"OAS for {service} not found")

    with open(filepath, "rb") as oas_spec:
        return oas_spec.read()

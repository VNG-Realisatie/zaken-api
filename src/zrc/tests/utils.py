import os
from datetime import datetime

from django.conf import settings
from django.utils import timezone

import yaml

DEFAULT_PATH_PARAMETERS = {
    'version': '1',
}

SPEC_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')

with open(SPEC_PATH, 'r') as infile:
    SPEC = yaml.load(infile)


def get_operation_url(operation, **kwargs):
    for path, methods in SPEC['paths'].items():
        for name, method in methods.items():
            if name == 'parameters':
                continue

            if method['operationId'] == operation:
                format_kwargs = DEFAULT_PATH_PARAMETERS.copy()
                format_kwargs.update(**kwargs)
                return path.format(**format_kwargs)

    raise ValueError(f"Operation {operation} not found")


def isodatetime(*args, **kwargs) -> str:
    dt = datetime(*args, **kwargs).replace(tzinfo=timezone.utc)
    return dt.isoformat()

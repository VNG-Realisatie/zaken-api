import os

from django.conf import settings

import yaml

DEFAULT_PATH_PARAMETERS = {
    'version': '1',
}

SPEC_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')

with open(SPEC_PATH, 'r') as infile:
    SPEC = yaml.load(infile)


def get_operation_url(operation, version='1'):
    for path, methods in SPEC['paths'].items():
        for name, method in methods.items():
            if name == 'parameters':
                continue

            if method['operationId'] == operation:
                return path.format(**DEFAULT_PATH_PARAMETERS)

    raise ValueError(f"Operation {operation} not found")

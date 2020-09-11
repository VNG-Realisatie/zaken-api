import sys

from ..dev import DATABASES, INSTALLED_APPS, LOGGING

if "test" in sys.argv:
    DATABASES["default"]["PORT"] = 5433

    for logger in LOGGING["loggers"].values():
        logger["level"] = "CRITICAL"


INSTALLED_APPS += ["django_extensions"]

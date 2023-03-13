import os

os.environ.setdefault("DB_HOST", "db")
os.environ.setdefault("DB_NAME", "postgres")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "")

from .production import *  # noqa isort:skip

# Helper function
missing_environment_vars = []


def getenv(key, default=None, required=False, split=False):
    val = os.getenv(key, default)
    if required and val is None:
        missing_environment_vars.append(key)
    if split and val:
        val = val.split(",")
    return val


#
# Custom settings
#

ENVIRONMENT = "docker"
NOTIFICATIONS_DISABLED = bool(getenv("NOTIFICATIONS_DISABLED", False))

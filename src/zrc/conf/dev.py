import os
import sys
import warnings

os.environ.setdefault("DEBUG", "yes")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault(
    "SECRET_KEY", "8u9chcd4g1%i5z)u@s6#c#0u%s_gggx*915w(yzrf#awezmu^i"
)
os.environ.setdefault("IS_HTTPS", "no")

os.environ.setdefault("DB_NAME", "zrc")
os.environ.setdefault("DB_USER", "zrc")
os.environ.setdefault("DB_PASSWORD", "zrc")

os.environ.setdefault("ZTC_JWT_SECRET", "zrc-to-ztc")

from .includes.base import *  # noqa isort:skip

#
# Standard Django settings.
#
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ADMINS = ()
MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

LOGGING["loggers"].update(
    {
        "zrc": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "django": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["django"],
            "level": "DEBUG",
            "propagate": False,
        },
        "performance": {"handlers": ["console"], "level": "INFO", "propagate": True},
    }
)

#
# Custom settings
#
ENVIRONMENT = "development"

#
# Library settings
#

# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ("127.0.0.1",)
DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

# in memory cache and django-axes don't get along.
# https://django-axes.readthedocs.io/en/latest/configuration.html#known-configuration-problems
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "drc_sync": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "kcc_sync": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += (
    "rest_framework.renderers.BrowsableAPIRenderer",
)

warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

SPEC_CACHE_TIMEOUT = None

if "test" in sys.argv:
    NOTIFICATIONS_DISABLED = True
    ALLOWED_HOSTS += ["testserver.com"]

# Override settings with local settings.
try:
    from .includes.local import *  # noqa
except ImportError:
    pass

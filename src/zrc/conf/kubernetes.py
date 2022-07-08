import os

os.environ.setdefault("DB_HOST", "")
os.environ.setdefault("DB_NAME", "")
os.environ.setdefault("DB_USER", "")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault(
    "SECRET_KEY", "8u9chcd4g1%i5z)u@s6#c#0u%s_gggx*915w(yzrf#awezmu^i"
)
os.environ.setdefault("ZTC_JWT_SECRET", "zrc-to-ztc")


from .production import *  # noqa isort:skip

#
# Custom settings
#

ENVIRONMENT = "kubernetes"

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

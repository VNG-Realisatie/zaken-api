"""
Continuous integration settings module.
"""
import logging
import os

os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("SECRET_KEY", "dummy")
os.environ.setdefault("ALLOWED_HOSTS", "testserver.com")

from .includes.base import *  # noqa isort:skip

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
    "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    # Cache for ZIO removal sync with DRC
    "drc_sync": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    },
}

LOGGING = None  # Quiet is nice
logging.disable(logging.CRITICAL)

ENVIRONMENT = "CI"

#
# Django-axes
#
AXES_BEHIND_REVERSE_PROXY = False

#
# ZRC specific settings
#
NOTIFICATIONS_DISABLED = True

#
# Jenkins settings
#
INSTALLED_APPS += ["zrc.tests", "django_jenkins"]
PROJECT_APPS = [app for app in INSTALLED_APPS if app.startswith("zrc.")]

JENKINS_TASKS = ("django_jenkins.tasks.run_pylint", "django_jenkins.tasks.run_pep8")

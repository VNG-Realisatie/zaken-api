from django.apps import AppConfig


class SyncConfig(AppConfig):
    name = 'zrc.sync'

    def ready(self):
        from . import signals  # noqa

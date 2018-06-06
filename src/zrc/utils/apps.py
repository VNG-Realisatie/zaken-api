from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = 'zrc.utils'

    def ready(self):
        from . import checks  # noqa

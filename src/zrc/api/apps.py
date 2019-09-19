from django.apps import AppConfig


class ZRCApiConfig(AppConfig):
    name = 'zrc.api'

    def ready(self):
        # ensure that the metaclass for every viewset has run
        from . import viewsets  # noqa

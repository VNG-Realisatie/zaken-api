from django.apps import AppConfig


class ZRCApiConfig(AppConfig):
    name = 'zrc.api'

    def ready(self):
        from .viewsets import ZaakViewSet # noqa

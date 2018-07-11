from django.conf.urls import include, url

from rest_framework_nested import routers

from .schema import schema_view
from .viewsets import (
    BetrokkeneViewSet, KlantContactViewSet, RolViewSet, StatusViewSet,
    ZaakEigenschapViewSet, ZaakObjectViewSet, ZaakViewSet
)

root_router = routers.DefaultRouter(trailing_slash=False)
root_router.register('zaken', ZaakViewSet)
root_router.register('statussen', StatusViewSet)
root_router.register('zaakobjecten', ZaakObjectViewSet)
root_router.register('klantcontacten', KlantContactViewSet)
root_router.register('betrokkenen', BetrokkeneViewSet)
root_router.register('rollen', RolViewSet)

zaak_router = routers.NestedSimpleRouter(
    root_router, r'zaken',
    lookup='zaak', trailing_slash=False,
)
zaak_router.register('zaakeigenschappen', ZaakEigenschapViewSet)


# TODO: the EndpointEnumerator seems to choke on path and re_path

urlpatterns = [
    url(r'^v(?P<version>\d+)/', include([

        # API documentation
        url(r'^schema/openapi(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=None),
            name='schema-json'),
        url(r'^schema/$',
            schema_view.with_ui('redoc', cache_timeout=None),
            name='schema-redoc'),

        # actual API
        url(r'^', include(root_router.urls)),
        url(r'^', include(zaak_router.urls)),
    ])),
]

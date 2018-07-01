from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter

from .schema import schema_view
from .viewsets import (
    BetrokkeneViewSet, DomeinDataViewSet, KlantContactViewSet, RolViewSet,
    StatusViewSet, ZaakObjectViewSet, ZaakViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register('zaken', ZaakViewSet)
router.register('statussen', StatusViewSet)
router.register('zaakobjecten', ZaakObjectViewSet)
router.register('domeindata', DomeinDataViewSet)
router.register('klantcontacten', KlantContactViewSet)
router.register('betrokkenen', BetrokkeneViewSet)
router.register('rollen', RolViewSet)

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
        url(r'^', include(router.urls)),
    ])),
]

from django.conf import settings

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from vng_api_common.permissions import (
    BaseAuthRequired, MainObjAuthScopesRequired, RelatedObjAuthScopesRequired
)


def bypass_permissions(request: Request) -> bool:
    """
    Bypass permission checks in DBEUG when using the browsable API renderer
    """
    return settings.DEBUG and isinstance(request.accepted_renderer, BrowsableAPIRenderer)


class ZaakAuthScopesRequired(MainObjAuthScopesRequired):
    """
    Look at the scopes required for the current action and at zaaktype and vertrouwelijkheidaanduiding
    of current zaak and check that they are present in the AC for this client
    """
    permission_fields = ('zaaktype', 'vertrouwelijkheidaanduiding')


class ZaakRelatedAuthScopesRequired(RelatedObjAuthScopesRequired):
    """
    Look at the scopes required for the current action and at zaaktype and vertrouwelijkheidaanduiding
    of related zaak and check that they are present in the AC for this client
    """
    permission_fields = ('zaaktype', 'vertrouwelijkheidaanduiding')
    obj_path = 'zaak'


class ZaakBaseAuthRequired (BaseAuthRequired):
    permission_fields = ('zaaktype', 'vertrouwelijkheidaanduiding')
    obj_path = 'zaak'

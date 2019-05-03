from urllib.parse import urlparse

from django.conf import settings

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.views import View
from vng_api_common.permissions import AuthScopesRequired, get_required_scopes
from vng_api_common.utils import get_resource_for_path


def bypass_permissions(request: Request) -> bool:
    """
    Bypass permission checks in DBEUG when using the browsable API renderer
    """
    return settings.DEBUG and isinstance(request.accepted_renderer, BrowsableAPIRenderer)


class ZaakAuthScopesRequired(AuthScopesRequired):
    """
    Look at the scopes required for the current action and at zaaktype and vertrouwelijkheidaanduiding
    of current zaak and check that they are present in the AC for this client
    """

    def get_zaaktype(self, obj):
        return obj.zaaktype

    def get_vertrouwelijkheidaanduiding(self, obj):
        return obj.vertrouwelijkheidaanduiding

    def get_zaaktype_from_request(self, request):
        return request.data.get('zaaktype', None)

    def get_vertrouwelijkheidaanduiding_from_request(self, request):
        return request.data.get('vertrouwelijkheidaanduiding', None)


class ZaakRelatedAuthScopesRequired(AuthScopesRequired):
    """
    Look at the scopes required for the current action and at zaaktype and vertrouwelijkheidaanduiding
    of related zaak and check that they are present in the AC for this client
    """
    zaak_getter = None

    def get_zaaktype(self, obj):
        return obj.zaak.zaaktype

    def get_vertrouwelijkheidaanduiding(self, obj):
        return obj.zaak.vertrouwelijkheidaanduiding

    def get_zaaktype_from_request(self, request):
        zaak_url = urlparse(request.data['zaak']).path
        zaak = get_resource_for_path(zaak_url)
        return zaak.zaaktype

    def get_vertrouwelijkheidaanduiding_from_request(self, request):
        zaak_url = urlparse(request.data['zaak']).path
        zaak = get_resource_for_path(zaak_url)
        return zaak.vertrouwelijkheidaanduiding


class RelatedObjectAuthScopesRequired(AuthScopesRequired):
    get_zaak = None
    zaak_from_obj = 'zaak'

    def _get_zaak(self, view: View):
        if not isinstance(self.get_zaak, str):
            raise TypeError("'get_zaak' must be set to a string, representing a view method name")

        method = getattr(view, self.get_zaak)
        return method()

    def has_permission(self, request: Request, view: View) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)

        if view.action == 'list':
            return request.jwt_auth.has_auth(scopes_required, None, None)

        if view.action == 'create':
            zaak = self._get_zaak(view)
            has_auth = request.jwt_auth.has_auth(
                scopes_required,
                zaak.zaaktype,
                zaak.vertrouwelijkheidaanduiding
            )
            return has_auth

        return True

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)
        if not isinstance(self.zaak_from_obj, str):
            raise TypeError("'zaak_from_obj' must be a python dotted path to the zaak FK")

        bits = self.zaak_from_obj.split('.')

        for bit in bits:
            obj = getattr(obj, bit)

        zaak = obj
        has_auth = request.jwt_auth.has_auth(
            scopes_required,
            zaak.zaaktype,
            zaak.vertrouwelijkheidaanduiding
        )
        return has_auth


def permission_class_factory(base=RelatedObjectAuthScopesRequired, **attrs) -> type:
    """
    Build a view-specific permission class

    This is just a small wrapper around ``type`` intended to keep the code readable.
    """
    name = base.__name__
    return type(name, (base,), attrs)

import logging

from django.shortcuts import get_object_or_404

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from zds_schema.geo import GeoMixin
from zds_schema.permissions import ActionScopesRequired
from zds_schema.search import SearchMixin
from zds_schema.utils import lookup_kwargs_to_filters
from zds_schema.viewsets import CheckQueryParamsMixin, NestedViewSetMixin

from zrc.datamodel.models import (
    KlantContact, Rol, Status, Zaak, ZaakEigenschap, ZaakInformatieObject,
    ZaakObject
)

from .filters import RolFilter, StatusFilter, ZaakFilter
from .permissions import ZaaktypePermission
from .scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN, SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_CREATE
)
from .serializers import (
    KlantContactSerializer, RolSerializer, StatusSerializer,
    ZaakEigenschapSerializer, ZaakInformatieObjectSerializer,
    ZaakObjectSerializer, ZaakSerializer, ZaakZoekSerializer
)

logger = logging.getLogger(__name__)


class ZaakViewSet(GeoMixin,
                  SearchMixin,
                  CheckQueryParamsMixin,
                  mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKen.

    create:
    Maak een ZAAK aan.

    Indien geen identificatie gegeven is, dan wordt deze automatisch
    gegenereerd. De identificatie moet uniek zijn binnen de bronorganisatie.

    De URL naar het zaaktype wordt gevalideerd op geldigheid.

    list:
    Geef een lijst van ZAAKen.

    Optioneel kan je de queryparameters gebruiken om zaken te filteren.

    Opmerkingen:
    - je krijgt enkel zaken terug van de zaaktypes die in het
      autorisatie-JWT vervat zitten.

    update:
    Werk een zaak bij.

    Er wordt gevalideerd op:
    - geldigheid URL naar zaaktype

    Opmerkingen:
    - je krijgt enkel zaken terug van de zaaktypes die in het autorisatie-JWT
      vervat zitten
    - zaaktype zal in de toekomst niet-wijzigbaar gemaakt worden.

    partial_update:
    Werk een zaak bij.

    Er wordt gevalideerd op:
    - geldigheid URL naar zaaktype

    Opmerkingen:
    - je krijgt enkel zaken terug van de zaaktypes die in het autorisatie-JWT
      vervat zitten
    - zaaktype zal in de toekomst niet-wijzigbaar gemaakt worden.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer
    search_input_serializer_class = ZaakZoekSerializer
    filterset_class = ZaakFilter
    lookup_field = 'uuid'

    permission_classes = (ActionScopesRequired, ZaaktypePermission)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        '_zoek': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE,
    }

    def get_queryset(self):
        base = super().get_queryset()

        # drf-yasg introspection
        if not hasattr(self.request, 'jwt_payload'):
            return base

        if self.action == 'list':
            zt_whitelist = self.request.jwt_payload.get('zaaktypes', [])
            if zt_whitelist == ['*']:
                return base  # no filtering, wildcard applies
            return base.filter(zaaktype__in=zt_whitelist)

        return base

    @action(methods=('post',), detail=False)
    def _zoek(self, request, *args, **kwargs):
        """
        Voer een (geo)-zoekopdracht uit op ZAAKen.
        """
        search_input = self.get_search_input()

        within = search_input['zaakgeometrie']['within']
        queryset = (
            self
            .filter_queryset(self.get_queryset())
            .filter(zaakgeometrie__within=within)
        )

        output_data = self.get_search_output(queryset)
        return Response(output_data)
    _zoek.is_search_action = True


class StatusViewSet(CheckQueryParamsMixin,
                    mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    filterset_class = StatusFilter
    lookup_field = 'uuid'

    permission_classes = (ActionScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE | SCOPE_STATUSSEN_TOEVOEGEN,
    }

    def perform_create(self, serializer):
        """
        Perform the create of the Status.

        After input validation and before DB persistance we need to check
        scope-related permissions. Two scopes are allowed to create new
        Status objects, however one is more limited in that only the
        initial status may be created.

        :raises: PermissionDenied if attempting to create another Status with
          insufficient permissions
        """
        zaak = serializer.validated_data['zaak']
        if not self.request.jwt_payload.has_scopes(SCOPE_STATUSSEN_TOEVOEGEN):
            if zaak.status_set.exists():
                msg = f"Met de '{SCOPE_ZAKEN_CREATE}' scope mag je slechts 1 status zetten"
                raise PermissionDenied(detail=msg)

        super().perform_create(serializer)


class ZaakObjectViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKOBJECTen.

    create:
    Registreer een ZAAKOBJECT relatie.

    list:
    Geef een lijst van ZAAKOBJECTrelaties terug.

    retrieve:
    Geef de details van een ZAAKOBJECT relatie.
    """
    queryset = ZaakObject.objects.all()
    serializer_class = ZaakObjectSerializer
    lookup_field = 'uuid'

    permission_classes = (ActionScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE,
    }


class ZaakInformatieObjectViewSet(NestedViewSetMixin,
                                  mixins.ListModelMixin,
                                  mixins.CreateModelMixin,
                                  viewsets.GenericViewSet):
    """
    Opvragen en bwerken van Zaak-Informatieobject relaties.

    create:
    OPGELET: dit endpoint hoor je als client NIET zelf aan te spreken.

    DRCs gebruiken deze endpoint bij het synchroniseren van relaties. De
    endpoint dient dus bij ZRC providers geimplementeerd te worden, maar voor
    clients is die niet relevant.

    Registreer welk(e) INFORMATIEOBJECT(en) een ZAAK kent.

    Er wordt gevalideerd op:
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT
    - bestaan van relatie ZAAK-INFORMATIEOBJECT in het DRC waar het
      informatieobject leeft

    list:
    Geef een lijst van relaties tussen ZAAKen en INFORMATIEOBJECTen.
    """
    queryset = ZaakInformatieObject.objects.all()
    serializer_class = ZaakInformatieObjectSerializer
    lookup_field = 'uuid'

    parent_retrieve_kwargs = {
        'zaak_uuid': 'uuid',
    }

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # DRF introspection
        if not self.kwargs:
            return context

        filters = lookup_kwargs_to_filters(self.parent_retrieve_kwargs, self.kwargs)
        context['parent_object'] = get_object_or_404(Zaak, **filters)
        return context


class ZaakEigenschapViewSet(NestedViewSetMixin,
                            mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKEIGENSCHAPpen

    create:
    Registreer een eigenschap van een ZAAK.

    list:
    Geef een collectie van eigenschappen behorend bij een ZAAK.

    retrieve:
    Geef de details van ZaakEigenschap voor een ZAAK.
    """
    queryset = ZaakEigenschap.objects.all()
    serializer_class = ZaakEigenschapSerializer
    lookup_field = 'uuid'


class KlantContactViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    """
    Opvragen en bewerken van KLANTCONTACTen.

    create:
    Registreer een klantcontact bij een ZAAK.

    Indien geen identificatie gegeven is, dan wordt deze automatisch
    gegenereerd.

    list:
    Geef een lijst van KLANTCONTACTen.

    detail:
    Geef de details van een klantcontact voor een ZAAK.
    """
    queryset = KlantContact.objects.all()
    serializer_class = KlantContactSerializer
    lookup_field = 'uuid'


class RolViewSet(CheckQueryParamsMixin,
                 mixins.CreateModelMixin,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ROLrelatie tussen een ZAAK en een BETROKKENE.

    create:
    Koppel een BETROKKENE aan een ZAAK.
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    filterset_class = RolFilter
    lookup_field = 'uuid'

    permission_classes = (ActionScopesRequired,)
    required_scopes = {
        'create': SCOPE_ZAKEN_CREATE
    }

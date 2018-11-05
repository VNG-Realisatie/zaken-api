from django.shortcuts import get_object_or_404

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from zds_schema.geo import GeoMixin
from zds_schema.search import SearchMixin
from zds_schema.utils import lookup_kwargs_to_filters
from zds_schema.viewsets import NestedViewSetMixin

from zrc.datamodel.models import (
    KlantContact, Rol, Status, Zaak, ZaakEigenschap, ZaakInformatieObject,
    ZaakObject
)

from .filters import RolFilter, StatusFilter, ZaakFilter
from .permissions import ActionScopesRequired
from .scopes import SCOPE_ZAKEN_CREATE
from .serializers import (
    KlantContactSerializer, RolSerializer, StatusSerializer,
    ZaakEigenschapSerializer, ZaakInformatieObjectSerializer,
    ZaakObjectSerializer, ZaakSerializer, ZaakZoekSerializer
)


class ZaakViewSet(GeoMixin,
                  SearchMixin,
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
    gegenereerd.

    De URL naar het zaaktype wordt gevalideerd op geldigheid.

    list:
    Geef een lijst van ZAAKen.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer
    search_input_serializer_class = ZaakZoekSerializer
    filter_class = ZaakFilter
    lookup_field = 'uuid'

    permission_classes = (ActionScopesRequired,)
    required_scopes = {
        'create': [SCOPE_ZAKEN_CREATE]
    }

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


class StatusViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    filter_class = StatusFilter
    lookup_field = 'uuid'


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


class ZaakInformatieObjectViewSet(NestedViewSetMixin,
                                  mixins.ListModelMixin,
                                  mixins.CreateModelMixin,
                                  viewsets.GenericViewSet):
    """
    Opvragen en bwerken van Zaak-Informatieobject relaties.

    create:
    Registreer welk(e) INFORMATIEOBJECT(en) een ZAAK kent.

    Er wordt gevalideerd op:
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT
    - bestaan van relatie ZAAK-INFORMATIEOBJECT in het DRC waar het
      informatieobject leeft

    list:
    Geef een lijst van relaties tussen ZAAKen en INFORMATIEOBJECTen.

    update:
    Werk de relatie tussen een ZAAK en INFORMATIEOBJECT bij.

    Er wordt gevalideerd op:
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT
    - bestaan van relatie ZAAK-INFORMATIEOBJECT in het DRC waar het
      informatieobject leeft

    partial_update:
    Werk de relatie tussen een ZAAK en INFORMATIEOBJECT bij.

    Er wordt gevalideerd op:
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT
    - bestaan van relatie ZAAK-INFORMATIEOBJECT in het DRC waar het
      informatieobject leeft
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


class RolViewSet(mixins.CreateModelMixin,
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
    filter_class = RolFilter
    lookup_field = 'uuid'

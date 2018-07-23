from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from zds_schema.decorators import action_description
from zds_schema.geojson import GeoMixin
from zds_schema.search import SearchMixin
from zds_schema.viewsets import NestedViewSetMixin

from zrc.datamodel.models import (
    KlantContact, OrganisatorischeEenheid, Rol, Status, Zaak, ZaakEigenschap,
    ZaakObject
)

from .filters import ZaakFilter
from .serializers import (
    KlantContactSerializer, OrganisatorischeEenheidSerializer, RolSerializer,
    StatusSerializer, ZaakEigenschapSerializer, ZaakObjectSerializer,
    ZaakSerializer, ZaakZoekSerializer
)


class ZaakViewSet(GeoMixin,
                  SearchMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKen.

    create:
    Maak een ZAAK aan.

    Indien geen zaakidentificatie gegeven is, dan wordt deze automatisch
    gegenereerd.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer
    search_input_serializer_class = ZaakZoekSerializer
    filter_class = ZaakFilter

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
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer


@action_description('create', "Registreer een ZAAKOBJECT relatie.")
@action_description('retrieve', "Geef de details van een ZAAKOBJECT relatie.")
class ZaakObjectViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = ZaakObject.objects.all()
    serializer_class = ZaakObjectSerializer


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


@action_description('create', "Registreer een klantcontact bij een ZAAK.\n\nIndien geen identificatie "
                              "gegeven is, dan wordt deze automatisch gegenereerd.")
@action_description('retrieve', "Geef de details van een klantcontact voor een ZAAK.")
class KlantContactViewSet(mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = KlantContact.objects.all()
    serializer_class = KlantContactSerializer


class BetrokkeneViewSet(mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = OrganisatorischeEenheid.objects.all()
    serializer_class = OrganisatorischeEenheidSerializer


@action_description('create', "Koppel een BETROKKENE aan een ZAAK.")
class RolViewSet(mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

from rest_framework import mixins, viewsets
from zds_schema.decorators import action_description

from zrc.datamodel.models import DomeinData, Status, Zaak, ZaakObject

from .serializers import (
    DomeinDataSerializer, StatusSerializer, ZaakObjectSerializer,
    ZaakSerializer
)


@action_description('create', "Maak een ZAAK aan.\n\nIndien geen zaakidentificatie gegeven is, "
                              "dan wordt deze automatisch gegenereerd.")
class ZaakViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKen.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer


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


@action_description('create', "Registreer DOMEINDATA bij een zaak.")
@action_description('retrieve', "Geef de details van DOMEINDATA voor een ZAAK.")
class DomeinDataViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = DomeinData.objects.all()
    serializer_class = DomeinDataSerializer

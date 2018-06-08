from rest_framework import mixins, viewsets
from zds_schema.decorators import action_description

from zrc.datamodel.models import Zaak, Status

from .serializers import ZaakSerializer, StatusSerializer


@action_description('create', "Maak een ZAAK aan.\n\nIndien geen zaakidentificatie gegeven is, "
                              "dan wordt deze automatisch gegenereerd.")
class ZaakViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Opvragen en bewerken van ZAAKen.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer


class StatusViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer

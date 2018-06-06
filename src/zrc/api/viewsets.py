from rest_framework import viewsets

from zrc.datamodel.models import Zaak, Status

from .serializers import ZaakSerializer, StatusSerializer


class ZaakViewSet(viewsets.ModelViewSet):
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer


class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer

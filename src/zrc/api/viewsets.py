from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from zrc.datamodel.models import Zaak, Status

from .serializers import ZaakSerializer, StatusSerializer


@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_description=(
        "Registreer een ZAAK.\n\nIndien geen zaakidentificatie gegeven is, "
        "dan wordt deze automatisch gegenereerd."
    )
))
class ZaakViewSet(viewsets.ModelViewSet):
    """
    Opvragen en bewerken van ZAAKen.
    """
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer


class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer

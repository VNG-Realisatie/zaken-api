from vng_api_common.validators import ResourceValidator

from ..core import StatusSerializer
from zrc.datamodel.models import Status
from ...auth import get_auth
from ...validators import DateNotInFutureValidator
from django.conf import settings


class StatusCreateSerializer(StatusSerializer):
    """Identical to StatusSerializer, but removed `zaakinformatieobjecten` from response. This serializer is used only
    for AOS generation."""

    class Meta:
        model = Status
        fields = (
            "url",
            "uuid",
            "zaak",
            "statustype",
            "datum_status_gezet",
            "statustoelichting",
            "indicatie_laatst_gezette_status",
            "gezetdoor",
        )
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "statustype": {
                "validators": [
                    ResourceValidator(
                        "StatusType", settings.ZTC_API_SPEC, get_auth=get_auth
                    )
                ]
            },
            "datum_status_gezet": {"validators": [DateNotInFutureValidator()]},
            "indicatie_laatst_gezette_status": {"read_only": True},
        }

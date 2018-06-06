from rest_framework import serializers

from zrc.datamodel.models import Zaak, Status


class ZaakSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.HyperlinkedRelatedField(
        source='current_status.pk', read_only=True,
        view_name='status-detail'
    )

    class Meta:
        model = Zaak
        fields = (
            'url',
            'zaakidentificatie',
            'status'
        )


class StatusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Status
        fields = (
            'url',
            'zaak',
            'status_type',
            'datum_status_gezet',
            'statustoelichting'
        )

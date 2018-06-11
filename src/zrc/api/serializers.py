from rest_framework import serializers

from zrc.datamodel.models import DomeinData, Status, Zaak, ZaakObject


class ZaakSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.HyperlinkedRelatedField(
        source='current_status_pk', read_only=True,
        view_name='status-detail',
        help_text="Indien geen status bekend is, dan is de waarde 'null'"
    )

    class Meta:
        model = Zaak
        fields = (
            'url',
            'zaakidentificatie',
            'zaaktype',
            'registratiedatum',
            'toelichting',

            # read-only veld, on-the-fly opgevraagd
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


class ZaakObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakObject
        fields = (
            'url',
            'zaak',
            'object',
            'relatieomschrijving'
        )


class DomeinDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DomeinData
        fields = (
            'url',
            'zaak',
            'domein_data',
        )

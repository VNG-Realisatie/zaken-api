from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from zrc.datamodel.models import (
    KlantContact, OrganisatorischeEenheid, Rol, Status, Zaak, ZaakEigenschap,
    ZaakObject
)


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
            'zaakgeometrie',

            # read-only veld, on-the-fly opgevraagd
            'status'
        )
        extra_kwargs = {
            'zaakgeometrie': {
                'help_text': 'Punt, lijn of (multi-)vlak geometrie-informatie, in GeoJSON.'
            }
        }


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


class ZaakEigenschapSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'zaak_pk': 'zaak__pk'
    }

    class Meta:
        model = ZaakEigenschap
        fields = (
            'url',
            'zaak',
            'eigenschap',
            'waarde',
        )


class KlantContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = KlantContact
        fields = (
            'url',
            'zaak',
            'identificatie',
            'datumtijd',
            'kanaal',
        )
        extra_kwargs = {
            'identificatie': {'required': False},
        }


class OrganisatorischeEenheidSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OrganisatorischeEenheid
        fields = (
            'url',
            'organisatie_eenheid_identificatie',
            'organisatie_identificatie',
            'datum_ontstaan',
            'naam',
        )


class RolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Rol
        fields = (
            'url',
            'zaak',
            'betrokkene',
            'rolomschrijving',
            'rolomschrijving_generiek',
            'roltoelichting',
        )

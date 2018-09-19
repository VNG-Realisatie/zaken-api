from django.shortcuts import get_object_or_404

from drf_writable_nested import NestedCreateMixin, NestedUpdateMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from zds_schema.constants import RolOmschrijving
from zds_schema.utils import lookup_kwargs_to_filters
from zds_schema.validators import URLValidator

from zrc.datamodel.models import (
    KlantContact, Rol, Status, Zaak, ZaakEigenschap, ZaakInformatieObject,
    ZaakKenmerk, ZaakObject
)

from .validators import RolOccurenceValidator, UniekeIdentificatieValidator


class ZaakKenmerkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakKenmerk
        fields = (
            'kenmerk',
            'bron',
        )


class ZaakSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.HyperlinkedModelSerializer):
    status = serializers.HyperlinkedRelatedField(
        source='current_status_uuid',
        read_only=True,
        view_name='status-detail',
        lookup_url_kwarg='uuid',
        help_text="Indien geen status bekend is, dan is de waarde 'null'"
    )

    kenmerken = ZaakKenmerkSerializer(
        source='zaakkenmerk_set',
        many=True,
        required=False,
        help_text="Lijst van kenmerken"
    )

    class Meta:
        model = Zaak
        fields = (
            'url',
            'identificatie',
            'bronorganisatie',
            'omschrijving',
            'zaaktype',
            'registratiedatum',
            'verantwoordelijke_organisatie',
            'startdatum',
            'einddatum',
            'einddatum_gepland',
            'uiterlijke_einddatum_afdoening',
            'toelichting',
            'zaakgeometrie',

            # read-only veld, on-the-fly opgevraagd
            'status',

            # Writable inline resource, as opposed to eigenschappen for demo
            # purposes. Eventually, we need to choose one form.
            'kenmerken'
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaakgeometrie': {
                'help_text': 'Punt, lijn of (multi-)vlak geometrie-informatie, in GeoJSON.'
            },
            'zaaktype': {
                # TODO: does order matter here with the default validators?
                'validators': [URLValidator()],
            }
        }
        # Replace a default "unique together" constraint.
        validators = [UniekeIdentificatieValidator()]


class GeoWithinSerializer(serializers.Serializer):
    within = GeometryField(required=False)


class ZaakZoekSerializer(serializers.Serializer):
    zaakgeometrie = GeoWithinSerializer(required=True)


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
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            }
        }


class ZaakObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakObject
        fields = (
            'url',
            'zaak',
            'object',
            'relatieomschrijving',
            'type',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            },
            'type': {
                'source': 'object_type',
            }
        }


class ZaakInformatieObjectSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'zaak_uuid': 'zaak__uuid'
    }
    parent_retrieve_kwargs = {
        'zaak_uuid': 'uuid',
    }

    class Meta:
        model = ZaakInformatieObject
        fields = ('url', 'informatieobject',)
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'zaak': {'lookup_field': 'uuid'},
            'informatieobject': {'validators': [URLValidator()]}
        }

    def create(self, validated_data):
        view_kwargs = self.context['view'].kwargs
        filters = lookup_kwargs_to_filters(self.parent_retrieve_kwargs, view_kwargs)
        validated_data['zaak'] = get_object_or_404(Zaak, **filters)
        return super().create(validated_data)


class ZaakEigenschapSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'zaak_uuid': 'zaak__uuid'
    }

    class Meta:
        model = ZaakEigenschap
        fields = (
            'url',
            'zaak',
            'eigenschap',
            'waarde',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            }
        }


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
            'url': {
                'lookup_field': 'uuid',
            },
            'identificatie': {
                'required': False
            },
            'zaak': {
                'lookup_field': 'uuid',
            }
        }


class RolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Rol
        fields = (
            'url',
            'zaak',
            'betrokkene',
            'betrokkene_type',
            'rolomschrijving',
            'roltoelichting',
        )
        validators = [
            RolOccurenceValidator(RolOmschrijving.initiator, max_amount=1),
            RolOccurenceValidator(RolOmschrijving.zaakcoordinator, max_amount=1),
        ]
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            },
        }

from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

import requests
from drf_writable_nested import NestedCreateMixin, NestedUpdateMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from zds_schema.constants import RolOmschrijving
from zds_schema.models import APICredential
from zds_schema.serializers import add_choice_values_help_text
from zds_schema.validators import (
    InformatieObjectUniqueValidator, ObjectInformatieObjectValidator,
    ResourceValidator, URLValidator
)

from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.models import (
    KlantContact, Rol, Status, Zaak, ZaakEigenschap, ZaakInformatieObject,
    ZaakKenmerk, ZaakObject, ZaakProductOfDienst
)

from .auth import get_ztc_auth
from .validators import RolOccurenceValidator, UniekeIdentificatieValidator


class ZaakKenmerkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakKenmerk
        fields = (
            'kenmerk',
            'bron',
        )


class ZaakProductOfDienstSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakProductOfDienst
        fields = ('product_of_dienst',)


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

    producten_en_diensten = ZaakProductOfDienstSerializer(
        source='zaakproductofdienst_set',
        many=True,
        required=False,
        help_text=_("De producten en/of diensten die door de zaak worden voortgebracht. "
                    "De producten/diensten moeten bij het zaaktype vermeld zijn.")
    )

    betalingsindicatie_weergave = serializers.CharField(source='get_betalingsindicatie_display', read_only=True)

    class Meta:
        model = Zaak
        fields = (
            'url',
            'identificatie',
            'bronorganisatie',
            'omschrijving',
            'toelichting',
            'zaaktype',
            'registratiedatum',
            'verantwoordelijke_organisatie',
            'startdatum',
            'einddatum',
            'einddatum_gepland',
            'uiterlijke_einddatum_afdoening',
            'publicatiedatum',
            'communicatiekanaal',
            'producten_en_diensten',
            'vertrouwelijkheidaanduiding',
            'resultaattoelichting',
            'betalingsindicatie',
            'betalingsindicatie_weergave',
            'laatste_betaaldatum',
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
                'validators': [URLValidator(get_auth=get_ztc_auth)],
            },
            'einddatum': {
                'read_only': True
            },
            'communicatiekanaal': {
                'validators': [
                    ResourceValidator('CommunicatieKanaal', settings.REFERENTIELIJSTEN_API_SPEC)
                ]
            },
            'vertrouwelijkheidaanduiding': {
                'required': False,
                'help_text': _("Aanduiding van de mate waarin het zaakdossier van de "
                               "ZAAK voor de openbaarheid bestemd is. Optioneel - indien "
                               "geen waarde gekozen wordt, dan wordt de waarde van het "
                               "ZAAKTYPE overgenomen. Dit betekent dat de API _altijd_ een "
                               "waarde teruggeeft.")
            }
        }
        # Replace a default "unique together" constraint.
        validators = [UniekeIdentificatieValidator()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(BetalingsIndicatie)
        self.fields['betalingsindicatie'].help_text += f"\n\n{value_display_mapping}"

    def create(self, validated_data: dict):
        # set the derived value from ZTC
        if 'vertrouwelijkheidaanduiding' not in validated_data:
            zaaktype_url = validated_data['zaaktype']

            # dynamic so that it can be mocked in tests easily
            Client = import_string(settings.ZDS_CLIENT_CLASS)
            client = Client.from_url(zaaktype_url)
            client.auth = APICredential.get_auth(
                zaaktype_url,
                scopes=['zds.scopes.zaaktypes.lezen']
            )

            zaaktype = client.request(zaaktype_url, 'zaaktype')

            validated_data['vertrouwelijkheidaanduiding'] = zaaktype['vertrouwelijkheidaanduiding']

        return super().create(validated_data)


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

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)
        status_type_url = validated_attrs['status_type']

        # dynamic so that it can be mocked in tests easily
        Client = import_string(settings.ZDS_CLIENT_CLASS)
        client = Client.from_url(status_type_url)
        client.auth = APICredential.get_auth(
            status_type_url,
            scopes=['zds.scopes.zaaktypes.lezen']
        )

        try:
            status_type = client.request(status_type_url, 'statustype')
            validated_attrs['__is_eindstatus'] = status_type['isEindstatus']
        except requests.HTTPError as exc:
            raise serializers.ValidationError(
                exc.args[0],
                code='relation-validation-error'
            ) from exc
        except KeyError as exc:
            raise serializers.ValidationError(
                exc.args[0],
                code='relation-validation-error'
            ) from exc

        # validate that all InformationObjects have indicatieGebruiksrecht set
        if validated_attrs['__is_eindstatus']:
            zios = validated_attrs['zaak'].zaakinformatieobject_set.all()
            for zio in zios:
                io_url = zio.informatieobject
                client = Client.from_url(io_url)
                client.auth = APICredential.get_auth(
                    io_url,
                    scopes=['zds.scopes.zaaktypes.lezen']
                )
                informatieobject = client.request(io_url, 'enkelvoudiginformatieobject')
                if informatieobject['indicatieGebruiksrecht'] is None:
                    raise serializers.ValidationError(
                        "Er zijn gerelateerde informatieobjecten waarvoor `indicatieGebruiksrecht` nog niet "
                        "gespecifieerd is. Je moet deze zetten voor je de zaak kan afsluiten.",
                        code='indicatiegebruiksrecht-unset'
                    )

        return validated_attrs

    def create(self, validated_data):
        is_eindstatus = validated_data.pop('__is_eindstatus')

        with transaction.atomic():
            obj = super().create(validated_data)

            # Save updated information on the ZAAK
            zaak = obj.zaak
            # Implicit conversion from datetime to date
            zaak.einddatum = validated_data['datum_status_gezet'] if is_eindstatus else None
            zaak.save(update_fields=['einddatum'])

        return obj


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

    class Meta:
        model = ZaakInformatieObject
        fields = ('informatieobject',)
        extra_kwargs = {
            'zaak': {'lookup_field': 'uuid'},
            'informatieobject': {
                'validators': [
                    URLValidator(),
                    InformatieObjectUniqueValidator('zaak', 'informatieobject'),
                    ObjectInformatieObjectValidator(),
                ]
            }
        }

    def create(self, validated_data):
        validated_data['zaak'] = self.context['parent_object']
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

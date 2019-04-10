import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

import isodate
import requests
from drf_writable_nested import NestedCreateMixin, NestedUpdateMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from vng_api_common.constants import Archiefstatus, RolOmschrijving
from vng_api_common.models import APICredential
from vng_api_common.serializers import (
    GegevensGroepSerializer, NestedGegevensGroepMixin,
    add_choice_values_help_text
)
from vng_api_common.validators import (
    InformatieObjectUniqueValidator, ObjectInformatieObjectValidator,
    ResourceValidator, UntilNowValidator, URLValidator
)

from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.models import (
    KlantContact, Resultaat, Rol, Status, Zaak, ZaakEigenschap,
    ZaakInformatieObject, ZaakKenmerk, ZaakObject
)
from zrc.utils.exceptions import DetermineProcessEndDateException

from .auth import get_zrc_auth, get_ztc_auth
from .validators import (
    HoofdzaakValidator, NotSelfValidator, RolOccurenceValidator,
    UniekeIdentificatieValidator
)

logger = logging.getLogger(__name__)


class ZaakKenmerkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakKenmerk
        fields = (
            'kenmerk',
            'bron',
        )


class VerlengingSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = 'verlenging'
        extra_kwargs = {
            'reden': {
                'label': _("Reden"),
            },
            'duur': {
                'label': _("Duur"),
            }
        }


class OpschortingSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = 'opschorting'
        extra_kwargs = {
            'indicatie': {
                'label': _("Indicatie"),
            },
            'reden': {
                'label': _("Reden"),
                'allow_blank': True,
            }
        }


class ZaakSerializer(NestedGegevensGroepMixin, NestedCreateMixin, NestedUpdateMixin,
                     serializers.HyperlinkedModelSerializer):
    status = serializers.HyperlinkedRelatedField(
        source='current_status_uuid',
        read_only=True,
        view_name='status-detail',
        lookup_url_kwarg='uuid',
        help_text=_("Indien geen status bekend is, dan is de waarde 'null'")
    )

    kenmerken = ZaakKenmerkSerializer(
        source='zaakkenmerk_set',
        many=True,
        required=False,
        help_text="Lijst van kenmerken. Merk op dat refereren naar gerelateerde objecten "
                  "beter kan via `ZaakObject`."
    )

    betalingsindicatie_weergave = serializers.CharField(source='get_betalingsindicatie_display', read_only=True)

    verlenging = VerlengingSerializer(
        required=False, allow_null=True,
        help_text=_("Gegevens omtrent het verlengen van de doorlooptijd van de behandeling van de ZAAK")
    )

    opschorting = OpschortingSerializer(
        required=False, allow_null=True,
        help_text=_("Gegevens omtrent het tijdelijk opschorten van de behandeling van de ZAAK")
    )

    deelzaken = serializers.HyperlinkedRelatedField(
        read_only=True,
        many=True,
        view_name='zaak-detail',
        lookup_url_kwarg='uuid',
        lookup_field='uuid'
    )

    resultaat = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='resultaat-detail',
        lookup_url_kwarg='uuid',
        lookup_field='uuid',
        help_text=_("Indien geen resultaat bekend is, dan is de waarde 'null'")
    )

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
            # TODO: add shape validator once we know the shape
            'producten_of_diensten',
            'vertrouwelijkheidaanduiding',
            'betalingsindicatie',
            'betalingsindicatie_weergave',
            'laatste_betaaldatum',
            'zaakgeometrie',
            'verlenging',
            'opschorting',
            'selectielijstklasse',
            'hoofdzaak',
            'deelzaken',
            'relevante_andere_zaken',

            # read-only veld, on-the-fly opgevraagd
            'status',

            # Writable inline resource, as opposed to eigenschappen for demo
            # purposes. Eventually, we need to choose one form.
            'kenmerken',

            # Archiving
            'archiefnominatie',
            'archiefstatus',
            'archiefactiedatum',

            'resultaat',
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
            },
            'hoofdzaak': {
                'lookup_field': 'uuid',
                'validators': [NotSelfValidator(), HoofdzaakValidator()],
            },
            'relevante_andere_zaken': {
                'child': serializers.URLField(
                    label=_("URL naar andere zaak"),
                    max_length=255,
                    validators=[URLValidator(get_auth=get_zrc_auth)]
                )
            },
            'laatste_betaaldatum': {
                'validators': [UntilNowValidator()]
            }
        }
        # Replace a default "unique together" constraint.
        validators = [UniekeIdentificatieValidator()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(BetalingsIndicatie)
        self.fields['betalingsindicatie'].help_text += f"\n\n{value_display_mapping}"

    def _get_zaaktype(self, zaaktype_url: str) -> dict:
        if not hasattr(self, '_zaaktype'):
            # dynamic so that it can be mocked in tests easily
            Client = import_string(settings.ZDS_CLIENT_CLASS)
            client = Client.from_url(zaaktype_url)
            client.auth = APICredential.get_auth(
                zaaktype_url,
                scopes=['zds.scopes.zaaktypes.lezen']
            )
            self._zaaktype = client.request(zaaktype_url, 'zaaktype')
        return self._zaaktype

    def _get_information_objects(self) -> list:
        if not hasattr(self, '_information_objects'):
            self._information_objects = []

            if self.instance:
                Client = import_string(settings.ZDS_CLIENT_CLASS)

                zios = self.instance.zaakinformatieobject_set.all()
                for zio in zios:
                    io_url = zio.informatieobject
                    client = Client.from_url(io_url)
                    client.auth = APICredential.get_auth(
                        io_url,
                        scopes=['scopes.documenten.lezen']
                    )
                    informatieobject = client.request(io_url, 'enkelvoudiginformatieobject')
                    self._information_objects.append(informatieobject)

        return self._information_objects

    def validate(self, attrs):
        super().validate(attrs)

        default_betalingsindicatie = self.instance.betalingsindicatie if self.instance else None
        betalingsindicatie = attrs.get('betalingsindicatie', default_betalingsindicatie)
        if betalingsindicatie == BetalingsIndicatie.nvt and attrs.get('laatste_betaaldatum'):
            raise serializers.ValidationError({'laatste_betaaldatum': _(
                "Laatste betaaldatum kan niet gezet worden als de betalingsindicatie \"nvt\" is"
            )}, code='betaling-nvt')

        # check that productenOfDiensten are part of the ones on the zaaktype
        default_zaaktype = self.instance.zaaktype if self.instance else None
        zaaktype = attrs.get('zaaktype', default_zaaktype)
        assert zaaktype, "Should not have passed validation - a zaaktype is needed"
        producten_of_diensten = attrs.get('producten_of_diensten')
        if producten_of_diensten:
            zaaktype = self._get_zaaktype(zaaktype)
            if not set(producten_of_diensten).issubset(set(zaaktype['productenOfDiensten'])):
                raise serializers.ValidationError({
                    'producten_of_diensten': _("Niet alle producten/diensten komen voor in "
                                               "de producten/diensten op het zaaktype")
                }, code='invalid-products-services')

        # Archiving
        default_archiefstatus = self.instance.archiefstatus if self.instance else Archiefstatus.nog_te_archiveren
        archiefstatus = attrs.get('archiefstatus', default_archiefstatus) != Archiefstatus.nog_te_archiveren
        if archiefstatus:
            ios = self._get_information_objects()
            for io in ios:
                if io['status'] != 'gearchiveerd':
                    raise serializers.ValidationError({
                        'archiefstatus',
                        _("Er zijn gerelateerde informatieobjecten waarvan de `status` nog niet gelijk is aan "
                          "`gearchiveerd`. Dit is een voorwaarde voor het zetten van de `archiefstatus` op een andere "
                          "waarde dan `nog_te_archiveren`.")
                    }, code='documents-not-archived')

            for attr in ['archiefnominatie', 'archiefactiedatum']:
                if not attrs.get(attr, getattr(self.instance, attr) if self.instance else None):
                    raise serializers.ValidationError({
                        attr: _("Moet van een waarde voorzien zijn als de 'Archiefstatus' een waarde heeft anders dan "
                                "'nog_te_archiveren'.")
                    }, code=f'{attr}-not-set')
        # End archiving

        return attrs

    def create(self, validated_data: dict):
        # set the derived value from ZTC
        if 'vertrouwelijkheidaanduiding' not in validated_data:
            zaaktype = self._get_zaaktype(validated_data['zaaktype'])
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

    def _get_resultaat_type(self, resultaat_type_url):
        if not hasattr(self, '_resultaat_type'):
            self._resultaat_type = None
            if resultaat_type_url:
                Client = import_string(settings.ZDS_CLIENT_CLASS)
                client = Client.from_url(resultaat_type_url)
                client.auth = APICredential.get_auth(
                    resultaat_type_url,
                    scopes=['zds.scopes.zaaktypes.lezen']
                )
                self._resultaat_type = client.request(resultaat_type_url, 'resultaattype')
        return self._resultaat_type

    def _get_resultaat(self, zaak):
        if not hasattr(self, '_resultaat'):
            self._resultaat = None
            try:
                self._resultaat = zaak.resultaat
            except ObjectDoesNotExist as exc:
                raise serializers.ValidationError(
                    exc.args[0],
                    code='resultaat-error'
                ) from exc
        return self._resultaat

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
            zaak = attrs['zaak']
            zios = zaak.zaakinformatieobject_set.all()
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

            # in case of eindstatus - retrieve archive parameters from resultaattype
            # Archiving: Use default archiefnominatie
            zaak_archiefnominatie = zaak.archiefnominatie
            if not zaak_archiefnominatie:
                resultaat = self._get_resultaat(zaak)
                resultaat_type = self._get_resultaat_type(resultaat.resultaat_type)
                zaak_archiefnominatie = resultaat_type['archiefnominatie']
            attrs['__archiefnominatie'] = zaak_archiefnominatie

            # Archiving: Calculate archiefactiedatum
            zaak_archiefactiedatum = zaak.archiefactiedatum
            if not zaak_archiefactiedatum:
                resultaat = self._get_resultaat(zaak)
                resultaat_type = self._get_resultaat_type(resultaat.resultaat_type)
                archiefactietermijn = resultaat_type['archiefactietermijn']

                if archiefactietermijn:
                    # All fields should be in the response
                    brondatum_archiefprocedure = resultaat_type['brondatumArchiefprocedure']
                    afleidingswijze = brondatum_archiefprocedure['afleidingswijze']
                    datum_kenmerk = brondatum_archiefprocedure['datumkenmerk']
                    objecttype = brondatum_archiefprocedure['objecttype']
                    procestermijn = brondatum_archiefprocedure['procestermijn']

                    try:
                        brondatum = zaak.get_brondatum(afleidingswijze, datum_kenmerk, objecttype, procestermijn)
                        if brondatum:
                            zaak_archiefactiedatum = brondatum + isodate.parse_duration(archiefactietermijn)
                    except DetermineProcessEndDateException as exc:
                        raise serializers.ValidationError(exc.args[0], code='archiefactiedatum-error')

                attrs['__archiefactiedatum'] = zaak_archiefactiedatum

        return validated_attrs

    def create(self, validated_data):
        is_eindstatus = validated_data.pop('__is_eindstatus')
        zaak__archiefnominatie = validated_data.pop('__archiefnominatie', None)
        zaak__archiefactiedatum = validated_data.pop('__archiefactiedatum', None)

        with transaction.atomic():
            obj = super().create(validated_data)

            # Save updated information on the ZAAK
            zaak = obj.zaak
            # Implicit conversion from datetime to date
            zaak.einddatum = validated_data['datum_status_gezet'] if is_eindstatus else None
            zaak.save(update_fields=['einddatum'])

            if is_eindstatus:
                # save archive parameters
                zaak.archiefactiedatum = zaak__archiefactiedatum
                zaak.archiefnominatie = zaak__archiefnominatie
                zaak.save(update_fields=('archiefactiedatum', 'archiefnominatie'))

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
            'naam',
            'waarde',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            },
            'naam': {
                'source': '_naam',
                'read_only': True,
            }
        }

    def _get_eigenschap(self, eigenschap_url):
        if not hasattr(self, '_eigenschap'):
            self._eigenschap = None
            if eigenschap_url:
                Client = import_string(settings.ZDS_CLIENT_CLASS)
                client = Client.from_url(eigenschap_url)
                client.auth = APICredential.get_auth(
                    eigenschap_url,
                    scopes=['zds.scopes.zaaktypes.lezen']
                )
                self._eigenschap = client.request(eigenschap_url, 'eigenschap')
        return self._eigenschap

    def validate(self, attrs):
        super().validate(attrs)

        eigenschap = self._get_eigenschap(attrs['eigenschap'])
        attrs['_naam'] = eigenschap['naam']

        return attrs


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


class ResultaatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Resultaat
        fields = (
            'url',
            'zaak',
            'resultaat_type',
            'toelichting'
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'zaak': {
                'lookup_field': 'uuid',
            },
            'resultaat_type': {
                'validators': [
                    # TODO: Add shape-validator when we know the shape.
                    URLValidator(get_auth=get_ztc_auth),
                ],
            }
        }

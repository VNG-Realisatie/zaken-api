import logging

from django.conf import settings
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
from zrc.datamodel.utils import BrondatumCalculator, get_brondatum
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
            status_type = client.retrieve('statustype', url=status_type_url)
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
            zaak = validated_attrs['zaak']
            zios = zaak.zaakinformatieobject_set.all()
            for zio in zios:
                io_url = zio.informatieobject
                client = Client.from_url(io_url)
                client.auth = APICredential.get_auth(
                    io_url,
                    scopes=['zds.scopes.zaaktypes.lezen']
                )
                informatieobject = client.retrieve('enkelvoudiginformatieobject', url=io_url)
                if informatieobject['indicatieGebruiksrecht'] is None:
                    raise serializers.ValidationError(
                        "Er zijn gerelateerde informatieobjecten waarvoor `indicatieGebruiksrecht` nog niet "
                        "gespecifieerd is. Je moet deze zetten voor je de zaak kan afsluiten.",
                        code='indicatiegebruiksrecht-unset'
                    )

            brondatum_calculator = BrondatumCalculator(zaak, validated_attrs['datum_status_gezet'])
            try:
                brondatum_calculator.calculate()
            except Resultaat.DoesNotExist as exc:
                raise serializers.ValidationError(
                    exc.args[0],
                    code='resultaat-does-not-exist'
                ) from exc
            except DetermineProcessEndDateException as exc:
                # ideally, we'd like to do this in the validate function, but that's unfortunately too
                # early since we don't know the end date yet
                # thought: we _can_ use the datumStatusGezet though!
                raise serializers.ValidationError(exc.args[0], code='archiefactiedatum-error')

            # nasty to pass state around...
            self.context['brondatum_calculator'] = brondatum_calculator

        return validated_attrs

    def create(self, validated_data):
        """
        Perform additional business logic

        Ideally, this would be encapsulated in some utilities for a clear in-output
        system, but for now we need to put a bandage on it.

        NOTE: avoid doing queries outside of the transaction block - we want
        everything or nothing to succeed and no limbo states.
        """
        zaak = validated_data['zaak']
        _zaak_fields_changed = []

        is_eindstatus = validated_data.pop('__is_eindstatus')
        brondatum_calculator = self.context.pop('brondatum_calculator', None)

        # if the eindstatus is being set, we need to calculate some more things:
        # 1. zaak.einddatum, which may be relevant for archiving purposes
        # 2. zaak.archiefactiedatum, if not explicitly filled in
        if is_eindstatus:
            zaak.einddatum = validated_data['datum_status_gezet'].date()
        else:
            zaak.einddatum = None
        _zaak_fields_changed.append('einddatum')

        if is_eindstatus:
            # in case of eindstatus - retrieve archive parameters from resultaattype

            # Archiving: Use default archiefnominatie
            if not zaak.archiefnominatie:
                zaak.archiefnominatie = brondatum_calculator.get_archiefnominatie()
                _zaak_fields_changed.append('archiefnominatie')

            # Archiving: Calculate archiefactiedatum
            if not zaak.archiefactiedatum:
                zaak.archiefactiedatum = brondatum_calculator.calculate()
                if zaak.archiefactiedatum is not None:
                    _zaak_fields_changed.append('archiefactiedatum')

        with transaction.atomic():
            obj = super().create(validated_data)

            # Save updated information on the ZAAK
            zaak.save(update_fields=_zaak_fields_changed)

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
        fields = ('url', 'informatieobject',)
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
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

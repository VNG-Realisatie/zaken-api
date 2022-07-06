import logging

from django.conf import settings
from django.db import transaction
from django.utils.encoding import force_text
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

import requests
from drf_writable_nested import NestedCreateMixin, NestedUpdateMixin
from rest_framework import serializers
from rest_framework.settings import api_settings
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_gis.fields import GeometryField
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from vng_api_common.constants import (
    Archiefnominatie,
    Archiefstatus,
    RelatieAarden,
    RolOmschrijving,
    RolTypes,
    ZaakobjectTypes,
)
from vng_api_common.models import APICredential
from vng_api_common.polymorphism import Discriminator, PolymorphicSerializer
from vng_api_common.serializers import (
    GegevensGroepSerializer,
    NestedGegevensGroepMixin,
    add_choice_values_help_text,
)
from vng_api_common.validators import (
    IsImmutableValidator,
    PublishValidator,
    ResourceValidator,
    UntilNowValidator,
    URLValidator,
)

from zrc.datamodel.constants import (
    AardZaakRelatie,
    BetalingsIndicatie,
    IndicatieMachtiging,
)
from zrc.datamodel.models import (
    KlantContact,
    RelevanteZaakRelatie,
    Resultaat,
    Rol,
    Status,
    Zaak,
    ZaakBesluit,
    ZaakContactMoment,
    ZaakEigenschap,
    ZaakInformatieObject,
    ZaakKenmerk,
    ZaakObject,
)
from zrc.datamodel.models.core import ZaakVerzoek
from zrc.datamodel.utils import BrondatumCalculator
from zrc.sync.signals import SyncError
from zrc.utils.exceptions import DetermineProcessEndDateException

from ..auth import get_auth
from ..validators import (
    CorrectZaaktypeValidator,
    DateNotInFutureValidator,
    EitherFieldRequiredValidator,
    HoofdZaaktypeRelationValidator,
    HoofdzaakValidator,
    JQExpressionValidator,
    NotSelfValidator,
    ObjectTypeOverigeDefinitieValidator,
    RolOccurenceValidator,
    UniekeIdentificatieValidator,
    ZaakArchiefStatusValidator,
    ZaaktypeInformatieobjecttypeRelationValidator,
)
from .address import ObjectAdresSerializer
from .betrokkene import (
    RolMedewerkerSerializer,
    RolNatuurlijkPersoonSerializer,
    RolNietNatuurlijkPersoonSerializer,
    RolOrganisatorischeEenheidSerializer,
    RolVestigingSerializer,
)
from .zaakobjecten import (
    ObjectBuurtSerializer,
    ObjectGemeentelijkeOpenbareRuimteSerializer,
    ObjectGemeenteSerializer,
    ObjectHuishoudenSerializer,
    ObjectInrichtingselementSerializer,
    ObjectKadastraleOnroerendeZaakSerializer,
    ObjectKunstwerkdeelSerializer,
    ObjectMaatschappelijkeActiviteitSerializer,
    ObjectOpenbareRuimteSerializer,
    ObjectOverigeSerializer,
    ObjectPandSerializer,
    ObjectSpoorbaandeelSerializer,
    ObjectTerreindeelSerializer,
    ObjectTerreinGebouwdObjectSerializer,
    ObjectWaterdeelSerializer,
    ObjectWegdeelSerializer,
    ObjectWijkSerializer,
    ObjectWoonplaatsSerializer,
    ObjectWozDeelobjectSerializer,
    ObjectWozObjectSerializer,
    ObjectWozWaardeSerializer,
    ObjectZakelijkRechtSerializer,
)

logger = logging.getLogger(__name__)


# Zaak API
class ZaakKenmerkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakKenmerk
        fields = ("kenmerk", "bron")


class VerlengingSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = "verlenging"
        extra_kwargs = {"reden": {"label": _("Reden")}, "duur": {"label": _("Duur")}}


class OpschortingSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = "opschorting"
        extra_kwargs = {
            "indicatie": {"label": _("Indicatie")},
            "reden": {"label": _("Reden"), "allow_blank": True},
        }


class GerelateerdeExterneZakenSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = "gerelateerde_externe_zaken"


class ProcessobjectSerializer(GegevensGroepSerializer):
    class Meta:
        model = Zaak
        gegevensgroep = "processobject"


class RelevanteZaakSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelevanteZaakRelatie
        fields = ("url", "aard_relatie")
        extra_kwargs = {
            "url": {
                "validators": [
                    ResourceValidator(
                        "Zaak",
                        settings.ZRC_API_SPEC,
                        get_auth=get_auth,
                        headers={"Accept-Crs": "EPSG:4326"},
                    )
                ]
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(AardZaakRelatie)
        self.fields["aard_relatie"].help_text += f"\n\n{value_display_mapping}"


class ZaakSerializer(
    NestedGegevensGroepMixin,
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.HyperlinkedModelSerializer,
):
    eigenschappen = NestedHyperlinkedRelatedField(
        many=True,
        read_only=True,
        lookup_field="uuid",
        view_name="zaakeigenschap-detail",
        parent_lookup_kwargs={"zaak_uuid": "zaak__uuid"},
        source="zaakeigenschap_set",
    )
    status = serializers.HyperlinkedRelatedField(
        source="current_status_uuid",
        read_only=True,
        allow_null=True,
        view_name="status-detail",
        lookup_url_kwarg="uuid",
        help_text=_("Indien geen status bekend is, dan is de waarde 'null'"),
    )

    kenmerken = ZaakKenmerkSerializer(
        source="zaakkenmerk_set",
        many=True,
        required=False,
        help_text="Lijst van kenmerken. Merk op dat refereren naar gerelateerde objecten "
        "beter kan via `ZaakObject`.",
    )

    betalingsindicatie_weergave = serializers.CharField(
        source="get_betalingsindicatie_display",
        read_only=True,
        help_text=_("Uitleg bij `betalingsindicatie`."),
    )

    verlenging = VerlengingSerializer(
        required=False,
        allow_null=True,
        help_text=_(
            "Gegevens omtrent het verlengen van de doorlooptijd van de behandeling van de ZAAK"
        ),
    )

    opschorting = OpschortingSerializer(
        required=False,
        allow_null=True,
        help_text=_(
            "Gegevens omtrent het tijdelijk opschorten van de behandeling van de ZAAK"
        ),
    )

    deelzaken = serializers.HyperlinkedRelatedField(
        read_only=True,
        many=True,
        view_name="zaak-detail",
        lookup_url_kwarg="uuid",
        lookup_field="uuid",
        help_text=_("URL-referenties naar deel ZAAKen."),
    )

    resultaat = serializers.HyperlinkedRelatedField(
        read_only=True,
        allow_null=True,
        view_name="resultaat-detail",
        lookup_url_kwarg="uuid",
        lookup_field="uuid",
        help_text=_(
            "URL-referentie naar het RESULTAAT. Indien geen resultaat bekend is, dan is de waarde 'null'"
        ),
    )

    relevante_andere_zaken = RelevanteZaakSerializer(
        many=True, required=False, help_text=_("Een lijst van relevante andere zaken.")
    )

    gerelateerde_externe_zaken = GerelateerdeExterneZakenSerializer(
        required=False,
        allow_null=True,
        help_text=_(
            "Een ZAAK bij een andere organisatie waarin een bijdrage geleverd wordt "
            "aan het bereiken van de uitkomst van de onderhanden ZAAK."
        ),
    )

    processobject = ProcessobjectSerializer(
        required=False,
        allow_null=True,
        help_text=_(
            "Specificatie van de attribuutsoort van het object, subject of gebeurtenis "
            " waarop, vanuit archiveringsoptiek, de zaak betrekking heeft en dat "
            "bepalend is voor de start van de archiefactietermijn."
        ),
    )

    class Meta:
        model = Zaak
        fields = (
            "url",
            "uuid",
            "identificatie",
            "bronorganisatie",
            "omschrijving",
            "toelichting",
            "zaaktype",
            "registratiedatum",
            "verantwoordelijke_organisatie",
            "startdatum",
            "einddatum",
            "einddatum_gepland",
            "uiterlijke_einddatum_afdoening",
            "publicatiedatum",
            "communicatiekanaal",
            # TODO: add shape validator once we know the shape
            "producten_of_diensten",
            "vertrouwelijkheidaanduiding",
            "betalingsindicatie",
            "betalingsindicatie_weergave",
            "laatste_betaaldatum",
            "zaakgeometrie",
            "verlenging",
            "opschorting",
            "selectielijstklasse",
            "hoofdzaak",
            "deelzaken",
            "relevante_andere_zaken",
            "eigenschappen",
            # read-only veld, on-the-fly opgevraagd
            "status",
            # Writable inline resource, as opposed to eigenschappen for demo
            # purposes. Eventually, we need to choose one form.
            "kenmerken",
            # Archiving
            "archiefnominatie",
            "archiefstatus",
            "archiefactiedatum",
            "resultaat",
            "opdrachtgevende_organisatie",
            "processobjectaard",
            "resultaattoelichting",
            "startdatum_bewaartermijn",
            "gerelateerde_externe_zaken",
            "processobject",
        )
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaakgeometrie": {
                "help_text": "Punt, lijn of (multi-)vlak geometrie-informatie, in GeoJSON."
            },
            "identificatie": {"validators": [IsImmutableValidator()]},
            "zaaktype": {
                # TODO: does order matter here with the default validators?
                "validators": [
                    IsImmutableValidator(),
                    PublishValidator(
                        "ZaakType", settings.ZTC_API_SPEC, get_auth=get_auth
                    ),
                ]
            },
            "einddatum": {"read_only": True, "allow_null": True},
            "communicatiekanaal": {
                "validators": [
                    ResourceValidator(
                        "CommunicatieKanaal", settings.REFERENTIELIJSTEN_API_SPEC
                    )
                ]
            },
            "vertrouwelijkheidaanduiding": {
                "required": False,
                "help_text": _(
                    "Aanduiding van de mate waarin het zaakdossier van de "
                    "ZAAK voor de openbaarheid bestemd is. Optioneel - indien "
                    "geen waarde gekozen wordt, dan wordt de waarde van het "
                    "ZAAKTYPE overgenomen. Dit betekent dat de API _altijd_ een "
                    "waarde teruggeeft."
                ),
            },
            "selectielijstklasse": {
                "validators": [
                    ResourceValidator(
                        "Resultaat",
                        settings.REFERENTIELIJSTEN_API_SPEC,
                        get_auth=get_auth,
                    )
                ]
            },
            "hoofdzaak": {
                "lookup_field": "uuid",
                "queryset": Zaak.objects.all(),
                "validators": [NotSelfValidator(), HoofdzaakValidator()],
            },
            "laatste_betaaldatum": {"validators": [UntilNowValidator()]},
        }
        # Replace a default "unique together" constraint.
        validators = [UniekeIdentificatieValidator(), HoofdZaaktypeRelationValidator()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(BetalingsIndicatie)
        self.fields["betalingsindicatie"].help_text += f"\n\n{value_display_mapping}"

        value_display_mapping = add_choice_values_help_text(Archiefstatus)
        self.fields["archiefstatus"].help_text += f"\n\n{value_display_mapping}"

        value_display_mapping = add_choice_values_help_text(Archiefnominatie)
        self.fields["archiefnominatie"].help_text += f"\n\n{value_display_mapping}"

    def _get_zaaktype(self, zaaktype_url: str) -> dict:
        if not hasattr(self, "_zaaktype"):
            # dynamic so that it can be mocked in tests easily
            Client = import_string(settings.ZDS_CLIENT_CLASS)
            client = Client.from_url(zaaktype_url)
            client.auth = APICredential.get_auth(
                zaaktype_url, scopes=["zds.scopes.zaaktypes.lezen"]
            )
            self._zaaktype = client.request(zaaktype_url, "zaaktype")
        return self._zaaktype

    def _get_information_objects(self) -> list:
        if not hasattr(self, "_information_objects"):
            self._information_objects = []

            if self.instance:
                Client = import_string(settings.ZDS_CLIENT_CLASS)

                zios = self.instance.zaakinformatieobject_set.all()
                for zio in zios:
                    io_url = zio.informatieobject
                    client = Client.from_url(io_url)
                    client.auth = APICredential.get_auth(
                        io_url, scopes=["scopes.documenten.lezen"]
                    )
                    informatieobject = client.request(
                        io_url, "enkelvoudiginformatieobject"
                    )
                    self._information_objects.append(informatieobject)

        return self._information_objects

    def validate(self, attrs):
        super().validate(attrs)

        default_betalingsindicatie = (
            self.instance.betalingsindicatie if self.instance else None
        )
        betalingsindicatie = attrs.get("betalingsindicatie", default_betalingsindicatie)
        if betalingsindicatie == BetalingsIndicatie.nvt and attrs.get(
            "laatste_betaaldatum"
        ):
            raise serializers.ValidationError(
                {
                    "laatste_betaaldatum": _(
                        'Laatste betaaldatum kan niet gezet worden als de betalingsindicatie "nvt" is'
                    )
                },
                code="betaling-nvt",
            )

        # check that productenOfDiensten are part of the ones on the zaaktype
        default_zaaktype = self.instance.zaaktype if self.instance else None
        zaaktype = attrs.get("zaaktype", default_zaaktype)
        assert zaaktype, "Should not have passed validation - a zaaktype is needed"
        producten_of_diensten = attrs.get("producten_of_diensten")
        if producten_of_diensten:
            zaaktype = self._get_zaaktype(zaaktype)
            if not set(producten_of_diensten).issubset(
                set(zaaktype["productenOfDiensten"])
            ):
                raise serializers.ValidationError(
                    {
                        "producten_of_diensten": _(
                            "Niet alle producten/diensten komen voor in "
                            "de producten/diensten op het zaaktype"
                        )
                    },
                    code="invalid-products-services",
                )

        # Archiving
        default_archiefstatus = (
            self.instance.archiefstatus
            if self.instance
            else Archiefstatus.nog_te_archiveren
        )
        archiefstatus = (
            attrs.get("archiefstatus", default_archiefstatus)
            != Archiefstatus.nog_te_archiveren
        )
        if archiefstatus:
            ios = self._get_information_objects()
            for io in ios:
                if io["status"] != "gearchiveerd":
                    raise serializers.ValidationError(
                        {
                            "archiefstatus",
                            _(
                                "Er zijn gerelateerde informatieobjecten waarvan de `status` nog niet gelijk is aan "
                                "`gearchiveerd`. Dit is een voorwaarde voor het zetten van de `archiefstatus` op een andere "
                                "waarde dan `nog_te_archiveren`."
                            ),
                        },
                        code="documents-not-archived",
                    )

            for attr in ["archiefnominatie", "archiefactiedatum"]:
                if not attrs.get(
                    attr, getattr(self.instance, attr) if self.instance else None
                ):
                    raise serializers.ValidationError(
                        {
                            attr: _(
                                "Moet van een waarde voorzien zijn als de 'Archiefstatus' een waarde heeft anders dan "
                                "'nog_te_archiveren'."
                            )
                        },
                        code=f"{attr}-not-set",
                    )
        # End archiving

        return attrs

    def create(self, validated_data: dict):
        # set the derived value from ZTC
        if "vertrouwelijkheidaanduiding" not in validated_data:
            zaaktype = self._get_zaaktype(validated_data["zaaktype"])
            validated_data["vertrouwelijkheidaanduiding"] = zaaktype[
                "vertrouwelijkheidaanduiding"
            ]

        return super().create(validated_data)


class GeoWithinSerializer(serializers.Serializer):
    within = GeometryField(required=False)


class ZaakZoekSerializer(serializers.Serializer):
    zaakgeometrie = GeoWithinSerializer(required=False)
    uuid__in = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_("Array of unieke resource identifiers (UUID4)"),
    )

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)
        if not validated_attrs:
            raise serializers.ValidationError(
                _("Search parameters must be specified"), code="empty_search_body"
            )
        return validated_attrs


class StatusSerializer(serializers.HyperlinkedModelSerializer):
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
            "zaakinformatieobjecten",
        )
        validators = [
            CorrectZaaktypeValidator("statustype"),
            ZaakArchiefStatusValidator(),
            UniqueTogetherValidator(
                queryset=Status.objects.all(), fields=["zaak", "datum_status_gezet"]
            ),
        ]
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
            "indicatie_laatst_gezette_status": {"required": False},
            "zaakinformatieobjecten": {"lookup_field": "uuid", "read_only": True},
        }

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)
        statustype_url = validated_attrs["statustype"]

        # dynamic so that it can be mocked in tests easily
        Client = import_string(settings.ZDS_CLIENT_CLASS)
        client = Client.from_url(statustype_url)
        client.auth = APICredential.get_auth(
            statustype_url, scopes=["zds.scopes.zaaktypes.lezen"]
        )

        try:
            statustype = client.retrieve("statustype", url=statustype_url)
            validated_attrs["__is_eindstatus"] = statustype["isEindstatus"]
        except requests.HTTPError as exc:
            raise serializers.ValidationError(
                exc.args[0], code="relation-validation-error"
            ) from exc
        except KeyError as exc:
            raise serializers.ValidationError(
                exc.args[0], code="relation-validation-error"
            ) from exc

        # validate that all InformationObjects have indicatieGebruiksrecht set
        # and are unlocked
        if validated_attrs["__is_eindstatus"]:
            zaak = validated_attrs["zaak"]
            zios = zaak.zaakinformatieobject_set.all()
            for zio in zios:
                io_url = zio.informatieobject
                client = Client.from_url(io_url)
                client.auth = APICredential.get_auth(
                    io_url, scopes=["zds.scopes.zaaktypes.lezen"]
                )
                informatieobject = client.retrieve(
                    "enkelvoudiginformatieobject", url=io_url
                )
                if informatieobject["locked"]:
                    raise serializers.ValidationError(
                        "Er zijn gerelateerde informatieobjecten die nog gelocked zijn."
                        "Deze informatieobjecten moet eerst unlocked worden voordat de zaak afgesloten kan worden.",
                        code="informatieobject-locked",
                    )
                if informatieobject["indicatieGebruiksrecht"] is None:
                    raise serializers.ValidationError(
                        "Er zijn gerelateerde informatieobjecten waarvoor `indicatieGebruiksrecht` nog niet "
                        "gespecifieerd is. Je moet deze zetten voor je de zaak kan afsluiten.",
                        code="indicatiegebruiksrecht-unset",
                    )

            brondatum_calculator = BrondatumCalculator(
                zaak, validated_attrs["datum_status_gezet"]
            )
            try:
                brondatum_calculator.calculate()
            except Resultaat.DoesNotExist as exc:
                raise serializers.ValidationError(
                    exc.args[0], code="resultaat-does-not-exist"
                ) from exc
            except DetermineProcessEndDateException as exc:
                # ideally, we'd like to do this in the validate function, but that's unfortunately too
                # early since we don't know the end date yet
                # thought: we _can_ use the datumStatusGezet though!
                raise serializers.ValidationError(
                    exc.args[0], code="archiefactiedatum-error"
                )

            # nasty to pass state around...
            self.context["brondatum_calculator"] = brondatum_calculator

        return validated_attrs

    def create(self, validated_data):
        """
        Perform additional business logic

        Ideally, this would be encapsulated in some utilities for a clear in-output
        system, but for now we need to put a bandage on it.

        NOTE: avoid doing queries outside of the transaction block - we want
        everything or nothing to succeed and no limbo states.
        """
        zaak = validated_data["zaak"]
        _zaak_fields_changed = []

        is_eindstatus = validated_data.pop("__is_eindstatus")
        brondatum_calculator = self.context.pop("brondatum_calculator", None)

        # are we re-opening the case?
        is_reopening = zaak.einddatum and not is_eindstatus

        # if the eindstatus is being set, we need to calculate some more things:
        # 1. zaak.einddatum, which may be relevant for archiving purposes
        # 2. zaak.archiefactiedatum, if not explicitly filled in
        if is_eindstatus:
            zaak.einddatum = validated_data["datum_status_gezet"].date()
        else:
            zaak.einddatum = None
        _zaak_fields_changed.append("einddatum")

        if is_eindstatus:
            # in case of eindstatus - retrieve archive parameters from resultaattype

            # Archiving: Use default archiefnominatie
            if not zaak.archiefnominatie:
                zaak.archiefnominatie = brondatum_calculator.get_archiefnominatie()
                _zaak_fields_changed.append("archiefnominatie")

            # Archiving: Calculate archiefactiedatum
            if not zaak.archiefactiedatum:
                zaak.archiefactiedatum = brondatum_calculator.calculate()
                if zaak.archiefactiedatum is not None:
                    _zaak_fields_changed.append("archiefactiedatum")
        elif is_reopening:
            zaak.archiefnominatie = None
            zaak.archiefactiedatum = None
            _zaak_fields_changed += ["archiefnominatie", "archiefactiedatum"]

        with transaction.atomic():
            obj = super().create(validated_data)

            # Save updated information on the ZAAK
            zaak.save(update_fields=_zaak_fields_changed)

        return obj


class ObjectTypeOverigeDefinitieSerializer(serializers.Serializer):
    url = serializers.URLField(
        label="Objecttype-URL",
        max_length=1000,
        help_text=(
            "URL-referentie naar de objecttype resource in een API. Deze resource "
            "moet de [JSON-schema](https://json-schema.org/)-definitie van het objecttype "
            "bevatten."
        ),
    )
    schema = serializers.CharField(
        label="schema-pad",
        max_length=100,
        help_text=(
            "Een geldige [jq](http://stedolan.github.io/jq/) expressie. Dit wordt "
            "gecombineerd met de resource uit het `url`-attribuut om het schema "
            "van het objecttype uit te lezen. Bijvoorbeeld: `.jsonSchema`."
        ),
        validators=[JQExpressionValidator()],
    )
    object_data = serializers.CharField(
        label="objectgegevens-pad",
        max_length=100,
        help_text=(
            "Een geldige [jq](http://stedolan.github.io/jq/) expressie. Dit wordt "
            "gecombineerd met de JSON data uit de OBJECT url om de objectgegevens uit "
            "te lezen en de vorm van de gegevens tegen het schema te valideren. "
            "Bijvoorbeeld: `.record.data`."
        ),
        validators=[JQExpressionValidator()],
    )


class ZaakObjectSerializer(PolymorphicSerializer):
    discriminator = Discriminator(
        discriminator_field="object_type",
        mapping={
            ZaakobjectTypes.adres: ObjectAdresSerializer(),
            ZaakobjectTypes.besluit: None,
            ZaakobjectTypes.buurt: ObjectBuurtSerializer(),
            ZaakobjectTypes.enkelvoudig_document: None,
            ZaakobjectTypes.gemeente: ObjectGemeenteSerializer(),
            ZaakobjectTypes.gemeentelijke_openbare_ruimte: ObjectGemeentelijkeOpenbareRuimteSerializer(),
            ZaakobjectTypes.huishouden: ObjectHuishoudenSerializer(),
            ZaakobjectTypes.inrichtingselement: ObjectInrichtingselementSerializer(),
            ZaakobjectTypes.kadastrale_onroerende_zaak: ObjectKadastraleOnroerendeZaakSerializer(),
            ZaakobjectTypes.kunstwerkdeel: ObjectKunstwerkdeelSerializer(),
            ZaakobjectTypes.maatschappelijke_activiteit: ObjectMaatschappelijkeActiviteitSerializer(),
            ZaakobjectTypes.medewerker: RolMedewerkerSerializer(),
            ZaakobjectTypes.natuurlijk_persoon: RolNatuurlijkPersoonSerializer(),
            ZaakobjectTypes.niet_natuurlijk_persoon: RolNietNatuurlijkPersoonSerializer(),
            ZaakobjectTypes.openbare_ruimte: ObjectOpenbareRuimteSerializer(),
            ZaakobjectTypes.organisatorische_eenheid: RolOrganisatorischeEenheidSerializer(),
            ZaakobjectTypes.pand: ObjectPandSerializer(),
            ZaakobjectTypes.spoorbaandeel: ObjectSpoorbaandeelSerializer(),
            ZaakobjectTypes.status: None,
            ZaakobjectTypes.terreindeel: ObjectTerreindeelSerializer(),
            ZaakobjectTypes.terrein_gebouwd_object: ObjectTerreinGebouwdObjectSerializer(),
            ZaakobjectTypes.vestiging: RolVestigingSerializer(),
            ZaakobjectTypes.waterdeel: ObjectWaterdeelSerializer(),
            ZaakobjectTypes.wegdeel: ObjectWegdeelSerializer(),
            ZaakobjectTypes.wijk: ObjectWijkSerializer(),
            ZaakobjectTypes.woonplaats: ObjectWoonplaatsSerializer(),
            ZaakobjectTypes.woz_deelobject: ObjectWozDeelobjectSerializer(),
            ZaakobjectTypes.woz_object: ObjectWozObjectSerializer(),
            ZaakobjectTypes.woz_waarde: ObjectWozWaardeSerializer(),
            ZaakobjectTypes.zakelijk_recht: ObjectZakelijkRechtSerializer(),
            ZaakobjectTypes.overige: ObjectOverigeSerializer(),
        },
        group_field="object_identificatie",
        same_model=False,
    )

    object_type_overige_definitie = ObjectTypeOverigeDefinitieSerializer(
        label=_("definitie object type overige"),
        required=False,
        allow_null=True,
        help_text=(
            "Verwijzing naar het schema van het type OBJECT als `objectType` de "
            'waarde "overige" heeft.\n\n'
            "* De URL referentie moet naar een JSON endpoint "
            "  wijzen waarin het objecttype gedefinieerd is, inclusief het "
            "  [JSON-schema](https://json-schema.org/).\n"
            "* Gebruik het `schema` attribuut om te verwijzen naar het schema binnen "
            "  de objecttype resource (deze gebruikt het "
            "  [jq](http://stedolan.github.io/jq/) formaat.\n"
            "* Gebruik het `objectData` attribuut om te verwijzen naar de gegevens "
            "  binnen het OBJECT. Deze gebruikt ook het "
            "  [jq](http://stedolan.github.io/jq/) formaat."
            "\n\nIndien je hier gebruikt van maakt, dan moet je een OBJECT url opgeven "
            "en is het gebruik van objectIdentificatie niet mogelijk. "
            "De opgegeven OBJECT url wordt gevalideerd tegen het schema van het "
            "opgegeven objecttype."
        ),
    )

    class Meta:
        model = ZaakObject
        fields = (
            "url",
            "uuid",
            "zaak",
            "object",
            "object_type",
            "object_type_overige",
            "object_type_overige_definitie",
            "relatieomschrijving",
        )
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid", "validators": [IsImmutableValidator()]},
            "object": {
                "required": False,
                "validators": [URLValidator(get_auth=get_auth), IsImmutableValidator()],
            },
            "object_type": {
                "validators": [IsImmutableValidator()],
            },
        }
        validators = [
            EitherFieldRequiredValidator(
                fields=("object", "object_identificatie"),
                message=_("object or objectIdentificatie must be provided"),
                code="invalid-zaakobject",
                skip_for_updates=True,
            ),
            ObjectTypeOverigeDefinitieValidator(),
            ZaakArchiefStatusValidator(),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(ZaakobjectTypes)
        self.fields["object_type"].help_text += f"\n\n{value_display_mapping}"

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)

        # for update don't validate fields, cause most of them are immutable
        if self.instance:
            return validated_attrs

        object_type = validated_attrs.get("object_type", None)
        object_type_overige = validated_attrs.get("object_type_overige", None)
        object_type_overige_definitie = validated_attrs.get(
            "object_type_overige_definitie", None
        )

        if object_type == ZaakobjectTypes.overige and not (
            object_type_overige or object_type_overige_definitie
        ):
            raise serializers.ValidationError(
                _(
                    'Als `objectType` de waarde "overige" heeft, moet '
                    "`objectTypeOverige` of `objectTypeOverigeDefinitie` van een "
                    "waarde voorzien zijn."
                ),
                code="missing-object-type-overige",
            )

        if object_type != ZaakobjectTypes.overige and object_type_overige:
            raise serializers.ValidationError(
                _(
                    'Als `objectType` niet de waarde "overige" heeft, mag '
                    "`objectTypeOverige` niet van een waarde voorzien zijn."
                ),
                code="invalid-object-type-overige-usage",
            )

        return validated_attrs

    def to_internal_value(self, data):
        # add object_type to data for PATCH
        if self.instance and "object_type" not in data:
            data["object_type"] = self.instance.object_type

        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        group_data = validated_data.pop("object_identificatie", None)
        zaakobject = super().create(validated_data)

        if group_data:
            group_serializer = self.discriminator.mapping[validated_data["object_type"]]
            serializer = group_serializer.get_fields()["object_identificatie"]
            group_data["zaakobject"] = zaakobject
            serializer.create(group_data)

        return zaakobject

    @transaction.atomic
    def update(self, instance, validated_data):
        group_data = validated_data.pop("object_identificatie", None)
        zaakobject = super().update(instance, validated_data)

        if group_data:
            group_serializer = self.discriminator.mapping[instance.object_type]
            serializer = group_serializer.get_fields()["object_identificatie"]
            # remove the previous data
            model = serializer.Meta.model
            model.objects.filter(zaakobject=zaakobject).delete()

            group_data["zaakobject"] = zaakobject
            serializer.create(group_data)

        return zaakobject


class ZaakInformatieObjectSerializer(serializers.HyperlinkedModelSerializer):
    aard_relatie_weergave = serializers.ChoiceField(
        source="get_aard_relatie_display",
        read_only=True,
        choices=[(force_text(value), key) for key, value in RelatieAarden.choices],
    )

    class Meta:
        model = ZaakInformatieObject
        fields = (
            "url",
            "uuid",
            "informatieobject",
            "zaak",
            "aard_relatie_weergave",
            "titel",
            "beschrijving",
            "registratiedatum",
            "vernietigingsdatum",
            "status",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=ZaakInformatieObject.objects.all(),
                fields=["zaak", "informatieobject"],
            ),
            ZaakArchiefStatusValidator(),
            ZaaktypeInformatieobjecttypeRelationValidator("informatieobject"),
        ]
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "informatieobject": {
                "validators": [
                    ResourceValidator(
                        "EnkelvoudigInformatieObject",
                        settings.DRC_API_SPEC,
                        get_auth=get_auth,
                    ),
                    IsImmutableValidator(),
                ]
            },
            "zaak": {"lookup_field": "uuid", "validators": [IsImmutableValidator()]},
            "status": {"lookup_field": "uuid"},
        }

    def save(self, **kwargs):
        # can't slap a transaction atomic on this, since DRC queries for the
        # relation!
        try:
            return super().save(**kwargs)
        except SyncError as sync_error:
            # delete the object again
            ZaakInformatieObject.objects.filter(
                informatieobject=self.validated_data["informatieobject"],
                zaak=self.validated_data["zaak"],
            )._raw_delete("default")
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: sync_error.args[0]}
            ) from sync_error


class ZaakEigenschapSerializer(NestedHyperlinkedModelSerializer):
    zaak = serializers.HyperlinkedRelatedField(
        queryset=Zaak.objects.all(),
        view_name="zaak-detail",
        lookup_field="uuid",
        validators=[IsImmutableValidator()],
    )

    parent_lookup_kwargs = {"zaak_uuid": "zaak__uuid"}

    class Meta:
        model = ZaakEigenschap
        fields = ("url", "uuid", "zaak", "eigenschap", "naam", "waarde")
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "eigenschap": {
                "validators": [
                    ResourceValidator(
                        "Eigenschap", settings.ZTC_API_SPEC, get_auth=get_auth
                    ),
                    IsImmutableValidator(),
                ]
            },
            "naam": {"source": "_naam", "read_only": True},
        }
        validators = [CorrectZaaktypeValidator("eigenschap")]

    def _get_eigenschap(self, eigenschap_url):
        if not hasattr(self, "_eigenschap"):
            self._eigenschap = None
            if eigenschap_url:
                Client = import_string(settings.ZDS_CLIENT_CLASS)
                client = Client.from_url(eigenschap_url)
                client.auth = APICredential.get_auth(
                    eigenschap_url, scopes=["zds.scopes.zaaktypes.lezen"]
                )
                self._eigenschap = client.request(eigenschap_url, "eigenschap")
        return self._eigenschap

    def validate(self, attrs):
        super().validate(attrs)

        # assign _naam only when creating zaak eigenschap
        if not self.instance:
            eigenschap = self._get_eigenschap(attrs["eigenschap"])
            attrs["_naam"] = eigenschap["naam"]
        return attrs


class KlantContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = KlantContact
        fields = (
            "url",
            "uuid",
            "zaak",
            "identificatie",
            "datumtijd",
            "kanaal",
            "onderwerp",
            "toelichting",
        )
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "identificatie": {"required": False},
            "zaak": {"lookup_field": "uuid"},
            "datumtijd": {"validators": [DateNotInFutureValidator()]},
        }


class ContactPersoonRolSerializer(GegevensGroepSerializer):
    class Meta:
        model = Rol
        gegevensgroep = "contactpersoon_rol"


class RolSerializer(PolymorphicSerializer):
    discriminator = Discriminator(
        discriminator_field="betrokkene_type",
        mapping={
            RolTypes.natuurlijk_persoon: RolNatuurlijkPersoonSerializer(),
            RolTypes.niet_natuurlijk_persoon: RolNietNatuurlijkPersoonSerializer(),
            RolTypes.vestiging: RolVestigingSerializer(),
            RolTypes.organisatorische_eenheid: RolOrganisatorischeEenheidSerializer(),
            RolTypes.medewerker: RolMedewerkerSerializer(),
        },
        group_field="betrokkene_identificatie",
        same_model=False,
    )

    contactpersoon_rol = ContactPersoonRolSerializer(
        allow_null=True,
        required=False,
        help_text=_(
            "De gegevens van de persoon die anderen desgevraagd in contact brengt "
            "met medewerkers van de BETROKKENE, een NIET-NATUURLIJK PERSOON of "
            "VESTIGING zijnde, of met BETROKKENE zelf, een NATUURLIJK PERSOON zijnde "
            ", vanuit het belang van BETROKKENE in haar ROL bij een ZAAK."
        ),
    )

    class Meta:
        model = Rol
        fields = (
            "url",
            "uuid",
            "zaak",
            "betrokkene",
            "betrokkene_type",
            "afwijkende_naam_betrokkene",
            "roltype",
            "omschrijving",
            "omschrijving_generiek",
            "roltoelichting",
            "registratiedatum",
            "indicatie_machtiging",
            "contactpersoon_rol",
            "statussen",
        )
        validators = [
            RolOccurenceValidator(RolOmschrijving.initiator, max_amount=1),
            RolOccurenceValidator(RolOmschrijving.zaakcoordinator, max_amount=1),
            CorrectZaaktypeValidator("roltype"),
            ZaakArchiefStatusValidator(),
        ]
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "betrokkene": {"required": False},
            "roltype": {
                "validators": [
                    IsImmutableValidator(),
                    ResourceValidator(
                        "RolType", settings.ZTC_API_SPEC, get_auth=get_auth
                    ),
                ]
            },
            "statussen": {"lookup_field": "uuid", "read_only": True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(IndicatieMachtiging)
        self.fields["indicatie_machtiging"].help_text += f"\n\n{value_display_mapping}"

        value_display_mapping = add_choice_values_help_text(RolTypes)
        self.fields["betrokkene_type"].help_text += f"\n\n{value_display_mapping}"

        value_display_mapping = add_choice_values_help_text(RolOmschrijving)
        self.fields["omschrijving_generiek"].help_text += f"\n\n{value_display_mapping}"

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)
        betrokkene = validated_attrs.get("betrokkene", None)
        betrokkene_identificatie = validated_attrs.get("betrokkene_identificatie", None)

        if not betrokkene and not betrokkene_identificatie:
            raise serializers.ValidationError(
                _("betrokkene or betrokkeneIdentificatie must be provided"),
                code="invalid-betrokkene",
            )

        return validated_attrs

    @transaction.atomic
    def create(self, validated_data):
        group_data = validated_data.pop("betrokkene_identificatie", None)
        rol = super().create(validated_data)

        if group_data:
            group_serializer = self.discriminator.mapping[
                validated_data["betrokkene_type"]
            ]
            serializer = group_serializer.get_fields()["betrokkene_identificatie"]
            group_data["rol"] = rol
            serializer.create(group_data)

        return rol


class ResultaatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Resultaat
        fields = ("url", "uuid", "zaak", "resultaattype", "toelichting")
        validators = [
            CorrectZaaktypeValidator("resultaattype"),
            ZaakArchiefStatusValidator(),
        ]
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "resultaattype": {
                "validators": [
                    IsImmutableValidator(),
                    ResourceValidator(
                        "ResultaatType", settings.ZTC_API_SPEC, get_auth=get_auth
                    ),
                ]
            },
        }


class ZaakBesluitSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {"zaak_uuid": "zaak__uuid"}

    class Meta:
        model = ZaakBesluit
        fields = ("url", "uuid", "besluit")
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "besluit": {"validators": [URLValidator(get_auth=get_auth)]},
        }

    def create(self, validated_data):
        validated_data["zaak"] = self.context["parent_object"]
        return super().create(validated_data)


class ZaakContactMomentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakContactMoment
        fields = ("url", "uuid", "zaak", "contactmoment")
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "contactmoment": {
                "validators": [
                    ResourceValidator(
                        "ContactMoment", settings.CMC_API_SPEC, get_auth=get_auth
                    )
                ]
            },
        }
        validators = [ZaakArchiefStatusValidator()]

    def save(self, **kwargs):
        try:
            return super().save(**kwargs)
        except SyncError as sync_error:
            # delete the object again
            ZaakContactMoment.objects.filter(
                contactmoment=self.validated_data["contactmoment"],
                zaak=self.validated_data["zaak"],
            )._raw_delete("default")
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: sync_error.args[0]}
            ) from sync_error


class ZaakVerzoekSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakVerzoek
        fields = ("url", "uuid", "zaak", "verzoek")
        extra_kwargs = {
            "url": {"lookup_field": "uuid"},
            "uuid": {"read_only": True},
            "zaak": {"lookup_field": "uuid"},
            "verzoek": {
                "validators": [
                    ResourceValidator(
                        "Verzoek", settings.VRC_API_SPEC, get_auth=get_auth
                    )
                ]
            },
        }
        validators = [ZaakArchiefStatusValidator()]

    def save(self, **kwargs):
        try:
            return super().save(**kwargs)
        except SyncError as sync_error:
            # delete the object again
            ZaakVerzoek.objects.filter(
                verzoek=self.validated_data["verzoek"],
                zaak=self.validated_data["zaak"],
            )._raw_delete("default")
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: sync_error.args[0]}
            ) from sync_error

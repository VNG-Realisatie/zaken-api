import logging

from django.core.cache import caches
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from notifications_api_common.kanalen import Kanaal
from notifications_api_common.viewsets import (
    NotificationCreateMixin,
    NotificationDestroyMixin,
    NotificationViewSetMixin,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ValidationError
from rest_framework.settings import api_settings
from vng_api_common.audittrails.viewsets import (
    AuditTrailCreateMixin,
    AuditTrailDestroyMixin,
    AuditTrailViewSet,
    AuditTrailViewsetMixin,
)
from vng_api_common.caching import conditional_retrieve
from vng_api_common.filters import Backend
from vng_api_common.geo import GeoMixin
from vng_api_common.permissions import permission_class_factory
from vng_api_common.search import SearchMixin
from vng_api_common.utils import lookup_kwargs_to_filters
from vng_api_common.viewsets import CheckQueryParamsMixin, NestedViewSetMixin

from zrc.datamodel.models import (
    KlantContact,
    Resultaat,
    Rol,
    Status,
    Zaak,
    ZaakBesluit,
    ZaakContactMoment,
    ZaakEigenschap,
    ZaakInformatieObject,
    ZaakObject,
)
from zrc.sync.signals import SyncError

from .audits import AUDIT_ZRC
from .data_filtering import ListFilterByAuthorizationsMixin
from .filters import (
    KlantContactFilter,
    ResultaatFilter,
    RolFilter,
    StatusFilter,
    ZaakContactMomentFilter,
    ZaakFilter,
    ZaakInformatieObjectFilter,
    ZaakObjectFilter,
    ZaakVerzoekFilter,
)
from .kanalen import KANAAL_ZAKEN
from .mixins import ClosedZaakMixin
from .permissions import (
    ZaakAuthScopesRequired,
    ZaakBaseAuthRequired,
    ZaakRelatedAuthScopesRequired,
)
from .scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN,
    SCOPE_ZAKEN_ALLES_LEZEN,
    SCOPE_ZAKEN_ALLES_VERWIJDEREN,
    SCOPE_ZAKEN_BIJWERKEN,
    SCOPE_ZAKEN_CREATE,
    SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    SCOPEN_ZAKEN_HEROPENEN,
)
from .serializers import (
    KlantContactSerializer,
    ResultaatSerializer,
    RolSerializer,
    StatusSerializer,
    ZaakBesluitSerializer,
    ZaakContactMomentSerializer,
    ZaakEigenschapSerializer,
    ZaakInformatieObjectSerializer,
    ZaakObjectSerializer,
    ZaakSerializer,
    ZaakVerzoek,
    ZaakVerzoekSerializer,
    ZaakZoekSerializer,
)
from .serializers.schema.core import StatusCreateSerializer
from .validators import ZaakBesluitValidator

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAKen opvragen."),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ZAAK opvragen."),
        description=_("Een specifieke ZAAK opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAK aan."),
        description=_(
            "Indien geen identificatie gegeven is, dan wordt deze automatisch "
            "gegenereerd. De identificatie moet uniek zijn binnen de bronorganisatie.\n\n"
            "**Er wordt gevalideerd op:**\n"
            "- geldigheid `zaaktype` URL - de resource moet opgevraagd kunnen worden"
            " uit de Catalogi API en de vorm van een ZAAKTYPE hebben.\n"
            "- `zaaktype` is geen concept (`zaaktype.concept = False`)\n"
            "- `laatsteBetaaldatum` mag niet in de toekomst liggen.\n"
            '- `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie "nvt" is.\n'
            '- `barchiefnominatie` moet een waarde hebben indien archiefstatus niet de waarde "nog_te_archiveren" heeft.\n'
            '- `archiefactiedatum` moet een waarde hebben indien archiefstatus niet de waarde "nog_te_archiveren" heeft.\n'
            '- `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren" hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut `status` de waarde "gearchiveerd" heeft.'
        ),
    ),
    partial_update=extend_schema(
        summary=_("Werk een ZAAK deels bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- `zaaktype` mag niet gewijzigd worden.\n"
            "- `identificatie` mag niet gewijzigd worden.\n"
            "- `laatsteBetaaldatum` mag niet in de toekomst liggen.\n"
            "- `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie\n"
            '"nvt" is.\n'
            "- `archiefnominatie` moet een waarde hebben indien `archiefstatus` niet de\n"
            'waarde "nog_te_archiveren" heeft.\n'
            "- `archiefactiedatum` moet een waarde hebben indien `archiefstatus` niet de\n"
            ' waarde "nog_te_archiveren" heeft.\n'
            '- `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren"\n'
            " hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut\n"
            '  `status` de waarde "gearchiveerd" heeft.\n'
            "**Opmerkingen**\n"
            "- er worden enkel zaken getoond van de zaaktypes waar u toe geautoriseerd\n"
            " bent.\n"
            "- indien een zaak heropend moet worden, doe dit dan door een nieuwe status\n"
            " toe te voegen die NIET de eindstatus is. Zie de `Status` resource."
        ),
    ),
    update=extend_schema(
        summary=_("Werk een ZAAK in zijn geheel bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- `zaaktype` mag niet gewijzigd worden.\n"
            "- `identificatie` mag niet gewijzigd worden.\n"
            "- `laatsteBetaaldatum` mag niet in de toekomst liggen.\n"
            "- `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie\n"
            '"nvt" is.\n'
            "- `archiefnominatie` moet een waarde hebben indien `archiefstatus` niet de\n"
            'waarde "nog_te_archiveren" heeft.\n'
            "- `archiefactiedatum` moet een waarde hebben indien `archiefstatus` niet de\n"
            ' waarde "nog_te_archiveren" heeft.\n'
            '- `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren"\n'
            " hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut\n"
            '  `status` de waarde "gearchiveerd" heeft.\n'
            "**Opmerkingen**\n"
            "- er worden enkel zaken getoond van de zaaktypes waar u toe geautoriseerd\n"
            " bent.\n"
            "- indien een zaak heropend moet worden, doe dit dan door een nieuwe status\n"
            " toe te voegen die NIET de eindstatus is. Zie de `Status` resource."
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAK."),
        description=_(
            "***De gerelateerde resources zijn hierbij***\n"
            "- `zaak` - de deelzaken van de verwijderde hoofzaak\n"
            "- `status` - alle statussen van de verwijderde zaak\n"
            "- `resultaat` - het resultaat van de verwijderde zaak\n"
            "- `rol` - alle rollen bij de zaak\n"
            "- `zaakobject` - alle zaakobjecten bij de zaak\n"
            "- `zaakeigenschap` - alle eigenschappen van de zaak\n"
            "- `zaakkenmerk` - alle kenmerken van de zaak\n"
            "- `zaakinformatieobject` - dit moet door-cascaden naar de Documenten"
            " API, zie ook: https://github.com/VNG-Realisatie/gemma-zaken/issues/791 (TODO)\n"
            "- `klantcontact` - alle klantcontacten bij een zaak"
        ),
    ),
    _zoek=extend_schema(
        summary=_("Voer een (geo)-zoekopdracht uit op ZAAKen."),
        description=_(
            "Zoeken/filteren gaat normaal via de `list` operatie, deze is echter"
            " niet geschikt voor geo-zoekopdrachten."
        ),
    ),
)
@conditional_retrieve()
class ZaakViewSet(
    NotificationViewSetMixin,
    AuditTrailViewsetMixin,
    GeoMixin,
    SearchMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    viewsets.ModelViewSet,
):
    queryset = Zaak.objects.prefetch_related(
        "deelzaken",
        "rol_set",
        "zaakobject_set",
        "zaakinformatieobject_set",
    ).order_by("-pk")
    serializer_class = ZaakSerializer
    search_input_serializer_class = ZaakZoekSerializer
    filter_backends = (Backend,)
    filterset_class = ZaakFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination

    permission_classes = (ZaakAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "_zoek": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_CREATE,
        "update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "partial_update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_ALLES_VERWIJDEREN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    global_description = _(
        "Een zaak mag (in principe) niet meer gewijzigd worden als de `archiefstatus`"
        ' een andere status heeft dan "nog_te_archiveren". Voor praktische redenen'
        " is er geen harde validatie regel aan de provider kant."
    )

    @action(methods=("post",), detail=False)
    def _zoek(self, request, *args, **kwargs):
        """
        Voer een (geo)-zoekopdracht uit op ZAAKen.

        Zoeken/filteren gaat normaal via de `list` operatie, deze is echter
        niet geschikt voor geo-zoekopdrachten.
        """
        search_input = self.get_search_input()
        queryset = self.filter_queryset(self.get_queryset())
        for name, value in search_input.items():
            if name == "zaakgeometrie":
                queryset = queryset.filter(zaakgeometrie__within=value["within"])
            else:
                if name == "ordering":
                    queryset = queryset.order_by(value)
                elif self.filterset_class.declared_filters.get(name, None):
                    queryset = self.filterset_class.declared_filters[name].filter(
                        queryset, value
                    )
                else:
                    queryset = queryset.filter(**{name: value})

        return self.get_search_output(queryset)

    _zoek.is_search_action = True

    def perform_update(self, serializer):
        """
        Perform the update of the Case.

        After input validation and before DB persistance we need to check
        scope-related permissions. Only SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN scope
        allows to alter closed cases

        :raises: PermissionDenied if attempting to alter a closed case with
        insufficient permissions

        """
        zaak = self.get_object()

        if not self.request.jwt_auth.has_auth(
            scopes=SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
            zaaktype=zaak.zaaktype,
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding,
        ):

            if zaak.is_closed:
                msg = "Modifying a closed case with current scope is forbidden"
                raise PermissionDenied(detail=msg)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # destroy is only allowed if no Besluiten are related
        validator = ZaakBesluitValidator()
        try:
            validator(instance)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: exc}, code=exc.detail[0].code
            )
        else:
            super().perform_destroy(instance)


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle STATUSsen bij ZAAKen opvragen."),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke STATUS van een ZAAK opvragen."),
        description=_("Een specifieke STATUS van een ZAAK opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een STATUS aan voor een ZAAK."),
        description=_(
            "**Er wordt gevalideerd op**\n"
            "- geldigheid URL naar de ZAAK\n"
            "- geldigheid URL naar het STATUSTYPE\n"
            "- indien het de eindstatus betreft, dan moet het attribuut"
            " `indicatieGebruiksrecht` gezet zijn op alle informatieobjecten die"
            "aan de zaak gerelateerd zijn\n\n"
            "**Opmerkingen**\n"
            "- Indien het statustype de eindstatus is (volgens het ZTC), dan wordt"
            " de zaak afgesloten door de einddatum te zetten."
        ),
    ),
)
@conditional_retrieve()
class StatusViewSet(
    NotificationCreateMixin,
    AuditTrailCreateMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = Status.objects.order_by("-pk")
    serializer_class = StatusSerializer
    filterset_class = StatusFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_CREATE
                  | SCOPE_STATUSSEN_TOEVOEGEN
                  | SCOPEN_ZAKEN_HEROPENEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    @extend_schema(
        responses={201: StatusCreateSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super(StatusViewSet, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Perform the create of the Status.

        After input validation and before DB persistance we need to check
        scope-related permissions. Three scopes are allowed to create new
        Status objects:
        - create initial status
        - create initial status and subsequent statuses until the case is closed
        - create any status before or after the case is closed

        :raises: PermissionDenied if attempting to create another Status with
          insufficient permissions
        """
        zaak = serializer.validated_data["zaak"]
        if not self.request.jwt_auth.has_auth(
            scopes=SCOPE_STATUSSEN_TOEVOEGEN | SCOPEN_ZAKEN_HEROPENEN,
            zaaktype=zaak.zaaktype,
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding,
        ):
            if zaak.status_set.exists():
                msg = f"Met de '{SCOPE_ZAKEN_CREATE}' scope mag je slechts 1 status zetten"
                raise PermissionDenied(detail=msg)

        if not self.request.jwt_auth.has_auth(
            scopes=SCOPEN_ZAKEN_HEROPENEN,
            zaaktype=zaak.zaaktype,
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding,
        ):
            if zaak.is_closed:
                msg = "Reopening a closed case with current scope is forbidden"
                raise PermissionDenied(detail=msg)

        super().perform_create(serializer)


@conditional_retrieve()
@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAKOBJECTen opvragen."),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ZAAKOBJECT opvragen."),
        description=_("Een specifieke ZAAKOBJECT opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAKOBJECT aan."),
        description=_(
            "Maak een ZAAKOBJECT aan.\n\n"
            "**Er wordt gevalideerd op**\n"
            "- Indien de `object` URL opgegeveven is, dan moet deze een geldige "
            " response (HTTP 200) geven.\n"
            "- Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen de `objectType` discriminator."
        ),
    ),
    partial_update=extend_schema(
        summary=_("Werk een ZAAKOBJECT deels bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- De attributen `zaak`, `object` en `objectType` mogen niet"
            " gewijzigd worden.\n"
            "- Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen"
            " de objectType discriminator."
        ),
    ),
    update=extend_schema(
        summary=_("Werk een ZAAKOBJECT zijn geheel bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- De attributen `zaak`, `object` en `objectType` mogen niet"
            " gewijzigd worden.\n"
            "- Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen"
            " de objectType discriminator."
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAKOBJECT."),
        description=_(
            "Verbreek de relatie tussen een ZAAK en een OBJECT door de ZAAKOBJECT"
            " resource te verwijderen."
        ),
    ),
)
class ZaakObjectViewSet(
    NotificationViewSetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    AuditTrailCreateMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    queryset = ZaakObject.objects.order_by("-pk")
    serializer_class = ZaakObjectSerializer
    filterset_class = ZaakObjectFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_CREATE
                  | SCOPE_ZAKEN_BIJWERKEN
                  | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "partial_update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN
                   | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN
                   | SCOPE_ZAKEN_ALLES_VERWIJDEREN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC


@conditional_retrieve()
@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAK-INFORMATIEOBJECT relaties opvragen "),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ZAAK-INFORMATIEOBJECT relatie opvragen."),
        description=_("Een specifieke ZAAK-INFORMATIEOBJECT relatie opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAK-INFORMATIEOBJECT relatie aan."),
        description=_(
            "Maak een ZAAK-INFORMATIEOBJECT relatie aan.\n"
            "\n**Er wordt gevalideerd op**\n"
            "- geldigheid zaak URL\n"
            "- geldigheid informatieobject URL\n"
            "- `zaak.archiefstatus` moet gelijk zijn aan 'nog_te_archiveren' \n"
            "- de combinatie informatieobject en zaak moet uniek zijn\n\n"
            "**Opmerkingen**\n"
            "- De registratiedatum wordt door het systeem op 'NU' gezet. De `aardRelatie`"
            " wordt ook door het systeem gezet.\n"
            "- Bij het aanmaken wordt ook in de Documenten API de gespiegelde relatie"
            " aangemaakt, echter zonder de relatie-informatie.\n"
        ),
    ),
    partial_update=extend_schema(
        summary=_("Werk een ZAAK-INFORMATIEOBJECT relatie deels bij."),
        description=_(
            "Je mag enkel de gegevens van de relatie bewerken, en niet de relatie"
            " zelf aanpassen.\n\n"
            "**Er wordt gevalideerd op** \n"
            "- informatieobject URL en zaak URL mogen niet veranderen"
        ),
    ),
    update=extend_schema(
        summary=_("Werk een ZAAK-INFORMATIEOBJECT relatie in zijn geheel bij."),
        description=_(
            "Je mag enkel de gegevens van de relatie bewerken, en niet de relatie"
            " zelf aanpassen.\n\n"
            "**Er wordt gevalideerd op** \n"
            "- informatieobject URL en zaak URL mogen niet veranderen"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAK-INFORMATIEOBJECT relatie."),
        description=_(
            "De gespiegelde relatie in de Documenten API wordt door de Zaken API"
            " verwijderd. Consumers kunnen dit niet handmatig doen."
        ),
    ),
)
class ZaakInformatieObjectViewSet(
    NotificationCreateMixin,
    AuditTrailViewsetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    queryset = ZaakInformatieObject.objects.all()
    filterset_class = ZaakInformatieObjectFilter
    serializer_class = ZaakInformatieObjectSerializer
    lookup_field = "uuid"
    notifications_kanaal = KANAAL_ZAKEN
    notifications_main_resource_key = "zaak"

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_CREATE
                  | SCOPE_ZAKEN_BIJWERKEN
                  | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "partial_update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN
                   | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN
                   | SCOPE_ZAKEN_ALLES_VERWIJDEREN,
    }
    audit = AUDIT_ZRC

    @property
    def notifications_wrap_in_atomic_block(self):
        # do not wrap the outermost create/destroy in atomic transaction blocks to send
        # notifications. The serializer wraps the actual object creation into a single
        # transaction, and after that, we're in autocommit mode.
        # Once the response has been properly obtained (success), then the notification
        # gets scheduled, and because of the transaction being in autocommit mode at that
        # point, the notification sending will fire immediately.
        if self.action in ["create", "destroy"]:
            return False
        return super().notifications_wrap_in_atomic_block

    def get_queryset(self):
        qs = super().get_queryset()

        # Do not display ZaakInformatieObjecten that are marked to be deleted
        cache = caches["drc_sync"]
        marked_zios = cache.get("zios_marked_for_delete")
        if marked_zios:
            return qs.exclude(uuid__in=marked_zios)
        return qs


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="zaak_uuid",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description=_("Unieke resource identifier (UUID4)"),
            required=True,
        )
    ]
)
@conditional_retrieve()
@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAKEIGENSCHAPpen opvragen. "),
        description=_("Alle ZAAKEIGENSCHAPpen opvragen."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ZAAKEIGENSCHAP opvragen."),
        description=_("Een specifieke ZAAKEIGENSCHAP opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAKEIGENSCHAP aan."),
        description=_(
            "Maak een ZAAKEIGENSCHAP aan.\n\n"
            "**Er wordt gevalideerd op:**\n"
            "- geldigheid `eigenschap` URL - de resource moet opgevraagd kunnen"
            " worden uit de Catalogi API en de vorm van een EIGENSCHAP hebben.\n"
            "- de `eigenschap` moet bij het `ZAAK.zaaktype` horen"
        ),
    ),
    partial_update=extend_schema(
        summary=_("Werk een ZAAKEIGENSCHAP deels bij."),
        description=_(
            "**Er wordt gevalideerd op** \n" "- Alleen de `waarde` mag gewijzigd worden"
        ),
    ),
    update=extend_schema(
        summary=_("Werk een ZAAKEIGENSCHAP in zijn geheel bij."),
        description=_(
            "**Er wordt gevalideerd op** \n" "- Alleen de `waarde` mag gewijzigd worden"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAKEIGENSCHAP."),
        description=_("Verwijder een ZAAKEIGENSCHAP"),
    ),
)
class ZaakEigenschapViewSet(
    NotificationViewSetMixin,
    AuditTrailCreateMixin,
    NestedViewSetMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    queryset = ZaakEigenschap.objects.all()
    serializer_class = ZaakEigenschapSerializer
    permission_classes = (
        permission_class_factory(base=ZaakBaseAuthRequired, get_obj="_get_zaak"),
    )
    lookup_field = "uuid"
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "partial_update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    }
    parent_retrieve_kwargs = {"zaak_uuid": "uuid"}
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def get_queryset(self):
        if not self.kwargs:  # this happens during schema generation, and causes crashes
            return self.queryset.none()
        return super().get_queryset()

    def _get_zaak(self):
        if not hasattr(self, "_zaak"):
            filters = lookup_kwargs_to_filters(self.parent_retrieve_kwargs, self.kwargs)
            self._zaak = get_object_or_404(Zaak, **filters)
        return self._zaak

    def list(self, request, *args, **kwargs):
        zaak = self._get_zaak()
        permission = ZaakAuthScopesRequired()
        if not permission.has_object_permission(self.request, self, zaak):
            raise PermissionDenied
        return super().list(request, *args, **kwargs)

    def initialize_request(self, request, *args, **kwargs):
        # workaround for drf-nested-viewset injecting the URL kwarg into request.data
        return super(viewsets.ModelViewSet, self).initialize_request(
            request, *args, **kwargs
        )


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle KLANTCONTACTen opvragen. "),
        description=_(
            "Alle KLANTCONTACTen opvragen.\n\n"
            "**DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint."
        ),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke KLANTCONTACT opvragen."),
        description=_(
            "Een specifieke KLANTCONTACT opvragen.\n\n"
            "**DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint."
        ),
    ),
    create=extend_schema(
        summary=_("Maak een KLANTCONTACT bij een ZAAK aan."),
        description=_(
            "Indien geen identificatie gegeven is, dan wordt deze automatisch gegenereerd.\n\n"
            "**DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint."
        ),
    ),
)
class KlantContactViewSet(
    NotificationCreateMixin,
    ListFilterByAuthorizationsMixin,
    AuditTrailCreateMixin,
    ClosedZaakMixin,
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = KlantContact.objects.order_by("-pk")
    serializer_class = KlantContactSerializer
    filterset_class = KlantContactFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination
    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    deprecation_message = (
        "Deze endpoint is verouderd en zal binnenkort uit dienst worden genomen. "
        "Maak gebruik van de vervangende contactmomenten API."
    )


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ROLlen bij ZAAKen opvragen."),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ROL bij een ZAAK opvragen."),
        description=_("Een specifieke ROL bij een ZAAK opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ROL aan bij een ZAAK."),
        description=_("Maak een ROL aan bij een ZAAK."),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ROL van een ZAAK."),
        description=_("Verwijder een ROL van een ZAAK."),
    ),
)
@conditional_retrieve()
class RolViewSet(
    NotificationCreateMixin,
    NotificationDestroyMixin,
    AuditTrailCreateMixin,
    AuditTrailDestroyMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = Rol.objects.order_by("-pk")
    serializer_class = RolSerializer
    filterset_class = RolFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle RESULTAATen van ZAAKen opvragen."),
        description=_("Deze lijst kan gefilterd wordt met query-string parameters."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke RESULTAAT opvragen."),
        description=_("Een specifieke RESULTAAT opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een RESULTAAT bij een ZAAK aan."),
        description=_(
            "**Er wordt gevalideerd op:**\n"
            "- geldigheid URL naar de ZAAK\n"
            "- geldigheid URL naar het RESULTAATTYPE"
        ),
    ),
    partial_update=extend_schema(
        summary=_("Werk een RESULTAAT deels bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- geldigheid URL naar de ZAAK\n"
            "- het RESULTAATTYPE mag niet gewijzigd worden"
        ),
    ),
    update=extend_schema(
        summary=_("Werk een RESULTAAT in zijn geheel bij."),
        description=_(
            "**Er wordt gevalideerd op** \n"
            "- geldigheid URL naar de ZAAK\n"
            "- het RESULTAATTYPE mag niet gewijzigd worden"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een RESULTAAT van een ZAAK."),
        description=_("Verwijder een RESULTAAT van een ZAAK."),
    ),
)
@conditional_retrieve()
class ResultaatViewSet(
    NotificationViewSetMixin,
    AuditTrailViewsetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    queryset = Resultaat.objects.order_by("-pk")
    serializer_class = ResultaatSerializer
    filterset_class = ResultaatFilter
    lookup_field = "uuid"
    pagination_class = PageNumberPagination

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        "partial_update": SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="zaak_uuid",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description=_("Unieke resource identifier (UUID4)"),
            required=True,
        )
    ]
)
@extend_schema_view(
    list=extend_schema(
        summary=_("Alle audit trail regels behorend bij de ZAAK."),
        description=_("Alle audit trail regels behorend bij de ZAAK."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke audit trail regel opvragen "),
        description=_("Een specifieke audit trail regel opvragen."),
    ),
)
class ZaakAuditTrailViewSet(AuditTrailViewSet):
    main_resource_lookup_field = "zaak_uuid"

    def initialize_request(self, request, *args, **kwargs):
        # workaround for drf-nested-viewset injecting the URL kwarg into request.data
        return super(viewsets.ReadOnlyModelViewSet, self).initialize_request(
            request, *args, **kwargs
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="zaak_uuid",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description=_("Unieke resource identifier (UUID4)"),
            required=True,
        )
    ]
)
@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAKBESLUITen opvragen."),
        description=_("Alle ZAAKBESLUITen opvragen."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifiek ZAAKBESLUIT opvragen "),
        description=_("Een specifiek ZAAKBESLUIT opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAKBESLUIT aan."),
        description=_(
            "**LET OP: Dit endpoint hoor je als consumer niet zelf aan te spreken.**\n\n"
            "De Besluiten API gebruikt dit endpoint om relaties te synchroniseren, daarom"
            " is dit endpoint in de Zaken API geimplementeerd.\n\n"
            "**Er wordt gevalideerd op:**\n"
            "- geldigheid URL naar de ZAAK"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAKBESLUIT."),
        description=_(
            "***LET OP: Dit endpoint hoor je als consumer niet zelf aan te spreken.***\n\n"
            "De Besluiten API gebruikt dit endpoint om relaties te synchroniseren, daarom"
            " is dit endpoint in de Zaken API geimplementeerd.\n"
        ),
    ),
)
class ZaakBesluitViewSet(
    NotificationCreateMixin,
    AuditTrailCreateMixin,
    AuditTrailDestroyMixin,
    NestedViewSetMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = ZaakBesluit.objects.all()
    serializer_class = ZaakBesluitSerializer
    permission_classes = (
        permission_class_factory(base=ZaakBaseAuthRequired, get_obj="_get_zaak"),
    )
    lookup_field = "uuid"

    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN,
    }

    parent_retrieve_kwargs = {"zaak_uuid": "uuid"}
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def get_queryset(self):
        if not self.kwargs:  # this happens during schema generation, and causes crashes
            return self.queryset.none()
        return super().get_queryset()

    def _get_zaak(self):
        if not hasattr(self, "_zaak"):
            filters = lookup_kwargs_to_filters(self.parent_retrieve_kwargs, self.kwargs)
            self._zaak = get_object_or_404(Zaak, **filters)
        return self._zaak

    def list(self, request, *args, **kwargs):
        zaak = self._get_zaak()
        permission = ZaakAuthScopesRequired()
        if not permission.has_object_permission(self.request, self, zaak):
            raise PermissionDenied
        return super().list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # DRF introspection
        if not self.kwargs:
            return context

        context["parent_object"] = self._get_zaak()
        return context

    def get_notification_main_object_url(self, data: dict, kanaal: Kanaal) -> str:
        zaak = self._get_zaak()
        return zaak.get_absolute_api_url(request=self.request)

    def get_audittrail_main_object_url(self, data: dict, main_resource: str) -> str:
        zaak = self._get_zaak()
        return zaak.get_absolute_api_url(request=self.request)

    def initialize_request(self, request, *args, **kwargs):
        # workaround for drf-nested-viewset injecting the URL kwarg into request.data
        return super(viewsets.ReadOnlyModelViewSet, self).initialize_request(
            request, *args, **kwargs
        )


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAKCONTACTMOMENTen opvragen."),
        description=_("Alle ZAAKCONTACTMOMENTen opvragen."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifiek ZAAKCONTACTMOMENT opvragen "),
        description=_("Een specifiek ZAAKCONTACTMOMENT opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAKCONTACTMOMENT aan."),
        description=_(
            "**Er wordt gevalideerd op:**\n" "- geldigheid URL naar het CONTACTMOMENT"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAKCONTACTMOMENT."),
        description=_("Verwijder een ZAAKCONTACTMOMENT."),
    ),
)
class ZaakContactMomentViewSet(
    NotificationCreateMixin,
    AuditTrailCreateMixin,
    AuditTrailDestroyMixin,
    ListFilterByAuthorizationsMixin,
    CheckQueryParamsMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = ZaakContactMoment.objects.order_by("-pk")
    serializer_class = ZaakContactMomentSerializer
    filterset_class = ZaakContactMomentFilter
    lookup_field = "uuid"
    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def get_queryset(self):
        qs = super().get_queryset()

        # Do not display ZaakContactMomenten that are marked to be deleted
        cache = caches["kcc_sync"]
        marked_zcms = cache.get("zcms_marked_for_delete")
        if marked_zcms:
            return qs.exclude(uuid__in=marked_zcms)
        return qs

    def perform_destroy(self, instance):
        try:
            super().perform_destroy(instance)
        except SyncError as sync_error:
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: sync_error.args[0]}
            ) from sync_error


@extend_schema_view(
    list=extend_schema(
        summary=_("Alle ZAAK-VERZOEKen opvragen."),
        description=_("Alle ZAAK-VERZOEKen opvragen."),
    ),
    retrieve=extend_schema(
        summary=_("Een specifieke ZAAK-VERZOEK opvragen."),
        description=_("Een specifieke ZAAK-VERZOEK opvragen."),
    ),
    create=extend_schema(
        summary=_("Maak een ZAAK-VERZOEK aan."),
        description=_(
            "**Er wordt gevalideerd op**\n" "- geldigheid URL naar de VERZOEK"
        ),
    ),
    destroy=extend_schema(
        summary=_("Verwijder een ZAAK-VERZOEK."),
        description=_("Verwijder een ZAAK-VERZOEK."),
    ),
)
class ZaakVerzoekViewSet(
    NotificationCreateMixin,
    AuditTrailCreateMixin,
    AuditTrailDestroyMixin,
    ListFilterByAuthorizationsMixin,
    CheckQueryParamsMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = ZaakVerzoek.objects.order_by("-pk")
    serializer_class = ZaakVerzoekSerializer
    filterset_class = ZaakVerzoekFilter
    lookup_field = "uuid"
    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        "list": SCOPE_ZAKEN_ALLES_LEZEN,
        "retrieve": SCOPE_ZAKEN_ALLES_LEZEN,
        "create": SCOPE_ZAKEN_BIJWERKEN,
        "destroy": SCOPE_ZAKEN_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def get_queryset(self):
        qs = super().get_queryset()

        # Do not display ZaakVerzoeken that are marked to be deleted
        cache = caches["kcc_sync"]
        marked_zvs = cache.get("zvs_marked_for_delete")
        if marked_zvs:
            return qs.exclude(uuid__in=marked_zvs)
        return qs

    def perform_destroy(self, instance):
        try:
            super().perform_destroy(instance)
        except SyncError as sync_error:
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: sync_error.args[0]}
            ) from sync_error

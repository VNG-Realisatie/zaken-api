import logging

from django.core.cache import caches
from django.shortcuts import get_object_or_404

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
from vng_api_common.notifications.kanalen import Kanaal
from vng_api_common.notifications.viewsets import (
    NotificationCreateMixin,
    NotificationDestroyMixin,
    NotificationViewSetMixin,
)
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
from .validators import ZaakBesluitValidator

logger = logging.getLogger(__name__)


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
    """
    Opvragen en bewerken van ZAAKen.

    Een zaak mag (in principe) niet meer gewijzigd worden als de
    `archiefstatus` een andere status heeft dan "nog_te_archiveren". Voor
    praktische redenen is er geen harde validatie regel aan de provider kant.

    create:
    Maak een ZAAK aan.

    Indien geen identificatie gegeven is, dan wordt deze automatisch
    gegenereerd. De identificatie moet uniek zijn binnen de bronorganisatie.

    **Er wordt gevalideerd op**:
    - geldigheid `zaaktype` URL - de resource moet opgevraagd kunnen
      worden uit de Catalogi API en de vorm van een ZAAKTYPE hebben.
    - `zaaktype` is geen concept (`zaaktype.concept` = False)
    - `laatsteBetaaldatum` mag niet in de toekomst liggen.
    - `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie
      "nvt" is.
    - `archiefnominatie` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefactiedatum` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren"
      hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut
      `status` de waarde "gearchiveerd" heeft.

    list:
    Alle ZAAKen opvragen.

    Deze lijst kan gefilterd wordt met query-string parameters.

    **Opmerking**
    - er worden enkel zaken getoond van de zaaktypes waar u toe geautoriseerd
      bent.

    retrieve:
    Een specifieke ZAAK opvragen.

    Een specifieke ZAAK opvragen.

    update:
    Werk een ZAAK in zijn geheel bij.

    **Er wordt gevalideerd op**
    - `zaaktype` mag niet gewijzigd worden.
    - `identificatie` mag niet gewijzigd worden.
    - `laatsteBetaaldatum` mag niet in de toekomst liggen.
    - `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie
      "nvt" is.
    - `archiefnominatie` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefactiedatum` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren"
      hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut
      `status` de waarde "gearchiveerd" heeft.

    **Opmerkingen**
    - er worden enkel zaken getoond van de zaaktypes waar u toe geautoriseerd
      bent.
    - indien een zaak heropend moet worden, doe dit dan door een nieuwe status
      toe te voegen die NIET de eindstatus is.
      Zie de `Status` resource.

    partial_update:
    Werk een ZAAK deels bij.

    **Er wordt gevalideerd op**
    - `zaaktype` mag niet gewijzigd worden.
    - `identificatie` mag niet gewijzigd worden.
    - `laatsteBetaaldatum` mag niet in de toekomst liggen.
    - `laatsteBetaaldatum` mag niet gezet worden als de betalingsindicatie
      "nvt" is.
    - `archiefnominatie` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefactiedatum` moet een waarde hebben indien `archiefstatus` niet de
      waarde "nog_te_archiveren" heeft.
    - `archiefstatus` kan alleen een waarde anders dan "nog_te_archiveren"
      hebben indien van alle gerelateeerde INFORMATIEOBJECTen het attribuut
      `status` de waarde "gearchiveerd" heeft.

    **Opmerkingen**
    - er worden enkel zaken getoond van de zaaktypes waar u toe geautoriseerd
      bent.
    - indien een zaak heropend moet worden, doe dit dan door een nieuwe status
      toe te voegen die NIET de eindstatus is. Zie de `Status` resource.

    destroy:
    Verwijder een ZAAK.

    **De gerelateerde resources zijn hierbij**
    - `zaak` - de deelzaken van de verwijderde hoofzaak
    - `status` - alle statussen van de verwijderde zaak
    - `resultaat` - het resultaat van de verwijderde zaak
    - `rol` - alle rollen bij de zaak
    - `zaakobject` - alle zaakobjecten bij de zaak
    - `zaakeigenschap` - alle eigenschappen van de zaak
    - `zaakkenmerk` - alle kenmerken van de zaak
    - `zaakinformatieobject` - dit moet door-cascaden naar de Documenten API,
      zie ook: https://github.com/VNG-Realisatie/gemma-zaken/issues/791 (TODO)
    - `klantcontact` - alle klantcontacten bij een zaak
    """

    queryset = Zaak.objects.prefetch_related("deelzaken").order_by("-pk")
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


@conditional_retrieve()
class StatusViewSet(
    NotificationCreateMixin,
    AuditTrailCreateMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    Opvragen en beheren van zaakstatussen.

    list:
    Alle STATUSsen van ZAAKen opvragen.

    Deze lijst kan gefilterd wordt met query-string parameters.

    retrieve:
    Een specifieke STATUS van een ZAAK opvragen.

    Een specifieke STATUS van een ZAAK opvragen.

    create:
    Maak een STATUS aan voor een ZAAK.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - geldigheid URL naar het STATUSTYPE
    - indien het de eindstatus betreft, dan moet het attribuut
      `indicatieGebruiksrecht` gezet zijn op alle informatieobjecten die aan
      de zaak gerelateerd zijn

    **Opmerkingen**
    - Indien het statustype de eindstatus is (volgens het ZTC), dan wordt de
      zaak afgesloten door de einddatum te zetten.

    """

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


class ZaakObjectViewSet(
    NotificationViewSetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    AuditTrailCreateMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    """
    Opvragen en bewerken van ZAAKOBJECTen.

    create:
    Maak een ZAAKOBJECT aan.

    Maak een ZAAKOBJECT aan.

    **Er wordt gevalideerd op**

    - Indien de `object` URL opgegeveven is, dan moet deze een geldige response
      (HTTP 200) geven.
    - Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen de
      `objectType` discriminator.

    list:
    Alle ZAAKOBJECTen opvragen.

    Deze lijst kan gefilterd wordt met query-string parameters.

    retrieve:
    Een specifiek ZAAKOBJECT opvragen.

    Een specifiek ZAAKOBJECT opvragen.

    update:
    Werk een ZAAKOBJECT in zijn geheel bij.

    **Er wordt gevalideerd op**

    - De attributen `zaak`, `object` en `objectType` mogen niet gewijzigd worden.
    - Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen de
      `objectType` discriminator.

    partial_update:
    Werk een ZAAKOBJECT deels bij.

    **Er wordt gevalideerd op**

    - De attributen `zaak`, `object` en `objectType` mogen niet gewijzigd worden.
    - Indien opgegeven, dan wordt `objectIdentificatie` gevalideerd tegen de
      `objectType` discriminator.

    destroy:
    Verwijder een ZAAKOBJECT.

    Verbreek de relatie tussen een ZAAK en een OBJECT door de ZAAKOBJECT resource te
    verwijderen.
    """

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
class ZaakInformatieObjectViewSet(
    NotificationCreateMixin,
    AuditTrailViewsetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):

    """
    Opvragen en bewerken van ZAAK-INFORMATIEOBJECT relaties.

    create:
    Maak een ZAAK-INFORMATIEOBJECT relatie aan.

    Er worden twee types van
    relaties met andere objecten gerealiseerd:

    **Er wordt gevalideerd op**
    - geldigheid zaak URL
    - geldigheid informatieobject URL
    - de combinatie informatieobject en zaak moet uniek zijn

    **Opmerkingen**
    - De registratiedatum wordt door het systeem op 'NU' gezet. De `aardRelatie`
      wordt ook door het systeem gezet.
    - Bij het aanmaken wordt ook in de Documenten API de gespiegelde relatie aangemaakt,
      echter zonder de relatie-informatie.

    Registreer welk(e) INFORMATIEOBJECT(en) een ZAAK kent.

    **Er wordt gevalideerd op**
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT

    list:
    Alle ZAAK-INFORMATIEOBJECT relaties opvragen.

    Deze lijst kan gefilterd wordt met querystringparameters.

    retrieve:
    Een specifieke ZAAK-INFORMATIEOBJECT relatie opvragen.

    Een specifieke ZAAK-INFORMATIEOBJECT relatie opvragen.

    update:
    Werk een ZAAK-INFORMATIEOBJECT relatie in zijn geheel bij.

    Je mag enkel de gegevens
    van de relatie bewerken, en niet de relatie zelf aanpassen.

    **Er wordt gevalideerd op**
    - informatieobject URL en zaak URL mogen niet veranderen

    partial_update:
    Werk een ZAAK-INFORMATIEOBJECT relatie in deels bij.

    Je mag enkel de gegevens
    van de relatie bewerken, en niet de relatie zelf aanpassen.

    **Er wordt gevalideerd op**
    - informatieobject URL en zaak URL mogen niet veranderen

    destroy:
    Verwijder een ZAAK-INFORMATIEOBJECT relatie.

    De gespiegelde relatie in de Documenten API wordt door de Zaken API
    verwijderd. Consumers kunnen dit niet handmatig doen..
    """

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


@conditional_retrieve()
class ZaakEigenschapViewSet(
    NotificationViewSetMixin,
    AuditTrailCreateMixin,
    NestedViewSetMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    """
    Opvragen en bewerken van ZAAKEIGENSCHAPpen

    create:
    Maak een ZAAKEIGENSCHAP aan.

    Maak een ZAAKEIGENSCHAP aan.

    **Er wordt gevalideerd op:**
    - geldigheid `eigenschap` URL - de resource moet opgevraagd kunnen
      worden uit de Catalogi API en de vorm van een EIGENSCHAP hebben.
    - de `eigenschap` moet bij het `ZAAK.zaaktype` horen

    list:
    Alle ZAAKEIGENSCHAPpen opvragen.

    Alle ZAAKEIGENSCHAPpen opvragen.

    retrieve:
    Een specifieke ZAAKEIGENSCHAP opvragen.

    Een specifieke ZAAKEIGENSCHAP opvragen.

    update:
    Werk een ZAAKEIGENSCHAP in zijn geheel bij.

    **Er wordt gevalideerd op**
    - Alleen de WAARDE mag gewijzigd worden

    partial_update:
    Werk een ZAAKEIGENSCHAP deels bij.

    **Er wordt gevalideerd op**
    - Alleen de WAARDE mag gewijzigd worden

    destroy:
    Verwijder een ZAAKEIGENSCHAP.
    """

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


class KlantContactViewSet(
    NotificationCreateMixin,
    ListFilterByAuthorizationsMixin,
    AuditTrailCreateMixin,
    ClosedZaakMixin,
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    Opvragen en bewerken van KLANTCONTACTen.

    create:
    Maak een KLANTCONTACT bij een ZAAK aan.

    Indien geen identificatie gegeven is, dan wordt deze automatisch
    gegenereerd.

    **DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint.

    list:
    Alle KLANTCONTACTen opvragen.

    Alle KLANTCONTACTen opvragen.

    **DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint.

    retrieve:
    Een specifiek KLANTCONTACT bij een ZAAK opvragen.

    Een specifiek KLANTCONTACT bij een ZAAK opvragen.

    **DEPRECATED**: gebruik de contactmomenten API in plaats van deze endpoint.
    """

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
    """
    Opvragen en bewerken van ROL relatie tussen een ZAAK en een BETROKKENE.

    list:
    Alle ROLlen bij ZAAKen opvragen.

    Deze lijst kan gefilterd wordt met query-string parameters.

    retrieve:
    Een specifieke ROL bij een ZAAK opvragen.

    Een specifieke ROL bij een ZAAK opvragen.

    destroy:
    Verwijder een ROL van een ZAAK.

    Verwijder een ROL van een ZAAK.

    create:
    Maak een ROL aan bij een ZAAK.

    Maak een ROL aan bij een ZAAK.

    """

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


@conditional_retrieve()
class ResultaatViewSet(
    NotificationViewSetMixin,
    AuditTrailViewsetMixin,
    CheckQueryParamsMixin,
    ListFilterByAuthorizationsMixin,
    ClosedZaakMixin,
    viewsets.ModelViewSet,
):
    """
    Opvragen en beheren van resultaten.

    list:
    Alle RESULTAATen van ZAAKen opvragen.

    Deze lijst kan gefilterd wordt met query-string parameters.

    retrieve:
    Een specifiek RESULTAAT opvragen.

    Een specifiek RESULTAAT opvragen.

    create:
    Maak een RESULTAAT bij een ZAAK aan.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - geldigheid URL naar het RESULTAATTYPE

    update:
    Werk een RESULTAAT in zijn geheel bij.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - het RESULTAATTYPE mag niet gewijzigd worden

    partial_update:
    Werk een RESULTAAT deels bij.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - het RESULTAATTYPE mag niet gewijzigd worden

    destroy:
    Verwijder een RESULTAAT van een ZAAK.

    Verwijder een RESULTAAT van een ZAAK.

    """

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


class ZaakAuditTrailViewSet(AuditTrailViewSet):
    """
    Opvragen van Audit trails horend bij een ZAAK.

    list:
    Alle audit trail regels behorend bij de ZAAK.

    Alle audit trail regels behorend bij de ZAAK.

    retrieve:
    Een specifieke audit trail regel opvragen.

    Een specifieke audit trail regel opvragen.
    """

    main_resource_lookup_field = "zaak_uuid"


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

    """
    Read and edit Zaak-Besluit relations.

    list:
    Alle ZAAKBESLUITen opvragen.

    Alle ZAAKBESLUITen opvragen.

    retrieve:
    Een specifiek ZAAKBESLUIT opvragen.

    Een specifiek ZAAKBESLUIT opvragen.

    create:
    Maak een ZAAKBESLUIT aan.

    **LET OP: Dit endpoint hoor je als consumer niet zelf aan te spreken.**

    De Besluiten API gebruikt dit endpoint om relaties te synchroniseren,
    daarom is dit endpoint in de Zaken API geimplementeerd.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK

    destroy:
    Verwijder een ZAAKBESLUIT.

    **LET OP: Dit endpoint hoor je als consumer niet zelf aan te spreken.**

    De Besluiten API gebruikt dit endpoint om relaties te synchroniseren,
    daarom is dit endpoint in de Zaken API geimplementeerd.

    """

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
    """
    Opvragen en bewerken van ZAAK-CONTACTMOMENT relaties.

    list:
    Alle ZAAKCONTACTMOMENTen opvragen.

    Alle ZAAKCONTACTMOMENTen opvragen.

    retrieve:
    Een specifiek ZAAKCONTACTMOMENT opvragen.

    Een specifiek ZAAKCONTACTMOMENT opvragen.

    create:
    Maak een ZAAKCONTACTMOMENT aan.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de CONTACTMOMENT

    destroy:
    Verwijder een ZAAKCONTACTMOMENT.

    """

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
    """
    Opvragen en bewerken van ZAAK-VERZOEK relaties.

    list:
    Alle ZAAK-VERZOEK opvragen.

    Alle ZAAK-VERZOEK opvragen.

    retrieve:
    Een specifiek ZAAK-VERZOEK opvragen.

    Een specifiek ZAAK-VERZOEK opvragen.

    create:
    Maak een ZAAK-VERZOEK aan.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de VERZOEK

    destroy:
    Verwijder een ZAAK-VERZOEK.

    """

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

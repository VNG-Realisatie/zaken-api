import logging

from django.shortcuts import get_object_or_404

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from vng_api_common.audittrails.api.serializers import AuditTrailSerializer
from vng_api_common.audittrails.models import AuditTrail
from vng_api_common.audittrails.viewsets import (
    AuditTrailCreateMixin, AuditTrailDestroyMixin, AuditTrailViewSet,
    AuditTrailViewsetMixin
)
from vng_api_common.geo import GeoMixin
from vng_api_common.notifications.kanalen import Kanaal
from vng_api_common.notifications.viewsets import (
    NotificationCreateMixin, NotificationViewSetMixin
)
from vng_api_common.permissions import permission_class_factory
from vng_api_common.search import SearchMixin
from vng_api_common.utils import lookup_kwargs_to_filters
from vng_api_common.viewsets import CheckQueryParamsMixin, NestedViewSetMixin

from zrc.datamodel.models import (
    KlantContact, Resultaat, Rol, Status, Zaak, ZaakEigenschap,
    ZaakInformatieObject, ZaakObject
)

from .audits import AUDIT_ZRC
from .data_filtering import ListFilterByAuthorizationsMixin
from .filters import ResultaatFilter, RolFilter, StatusFilter, ZaakFilter
from .kanalen import KANAAL_ZAKEN
from .permissions import (
    ZaakAuthScopesRequired, ZaakBaseAuthRequired,
    ZaakRelatedAuthScopesRequired
)
from .scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN, SCOPE_ZAKEN_ALLES_LEZEN,
    SCOPE_ZAKEN_ALLES_VERWIJDEREN, SCOPE_ZAKEN_BIJWERKEN, SCOPE_ZAKEN_CREATE,
    SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN, SCOPEN_ZAKEN_HEROPENEN
)
from .serializers import (
    KlantContactSerializer, ResultaatSerializer, RolSerializer,
    StatusSerializer, ZaakEigenschapSerializer, ZaakInformatieObjectSerializer,
    ZaakObjectSerializer, ZaakSerializer, ZaakZoekSerializer
)

logger = logging.getLogger(__name__)


class ZaakViewSet(NotificationViewSetMixin,
                  AuditTrailViewsetMixin,
                  GeoMixin,
                  SearchMixin,
                  CheckQueryParamsMixin,
                  ListFilterByAuthorizationsMixin,
                  viewsets.ModelViewSet):
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
    - `zaaktype` moet een geldige URL zijn.
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
    Geef een lijst van ZAAKen.

    Deze lijst wordt standaard gepagineerd met 100 zaken per pagina.

    Optioneel kan je de queryparameters gebruiken om zaken te filteren.

    **Opmerkingen**
    - je krijgt enkel zaken terug van de zaaktypes die in het autorisatie-JWT
      vervat zitten.

    retrieve:
    Haal de details van een ZAAK op.

    update:
    Werk een zaak bij.

    **Er wordt gevalideerd op**
    - `zaaktype` moet een geldige URL zijn.
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
    - je krijgt enkel zaken terug van de zaaktypes die in het autorisatie-JWT
      vervat zitten.
    - zaaktype zal in de toekomst niet-wijzigbaar gemaakt worden.
    - indien een zaak heropend moet worden, doe dit dan door een nieuwe status
      toe te voegen die NIET de eindstatus is.
      Zie de `Status` resource.

    partial_update:
    Werk een zaak bij.

    **Er wordt gevalideerd op**
    - `zaaktype` moet een geldige URL zijn.
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
    - je krijgt enkel zaken terug van de zaaktypes die in het autorisatie-JWT
      vervat zitten.
    - zaaktype zal in de toekomst niet-wijzigbaar gemaakt worden.
    - indien een zaak heropend moet worden, doe dit dan door een nieuwe status
      toe te voegen die NIET de eindstatus is. Zie de `Status` resource.

    destroy:
    Verwijdert een zaak, samen met alle gerelateerde resources binnen deze API.

    **De gerelateerde resources zijn hierbij**
    - `zaak` - de deelzaken van de verwijderde hoofzaak
    - `status` - alle statussen van de verwijderde zaak
    - `resultaat` - het resultaat van de verwijderde zaak
    - `rol` - alle rollen bij de zaak
    - `zaakobject` - alle zaakobjecten bij de zaak
    - `zaakeigenschap` - alle eigenschappen van de zaak
    - `zaakkenmerk` - alle kenmerken van de zaak
    - `zaakinformatieobject` - dit moet door-cascaden naar DRCs, zie ook
      https://github.com/VNG-Realisatie/gemma-zaken/issues/791 (TODO)
    - `klantcontact` - alle klantcontacten bij een zaak
    """
    queryset = Zaak.objects.prefetch_related('deelzaken').order_by('-pk')
    serializer_class = ZaakSerializer
    search_input_serializer_class = ZaakZoekSerializer
    filterset_class = ZaakFilter
    lookup_field = 'uuid'
    pagination_class = PageNumberPagination

    permission_classes = (ZaakAuthScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        '_zoek': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE,
        'update': SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        'partial_update': SCOPE_ZAKEN_BIJWERKEN | SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
        'destroy': SCOPE_ZAKEN_ALLES_VERWIJDEREN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    @action(methods=('post',), detail=False)
    def _zoek(self, request, *args, **kwargs):
        """
        Voer een (geo)-zoekopdracht uit op ZAAKen.

        Zoeken/filteren gaat normaal via de `list` operatie, deze is echter
        niet geschikt voor geo-zoekopdrachten.
        """
        search_input = self.get_search_input()

        within = search_input['zaakgeometrie']['within']
        queryset = (
            self
            .filter_queryset(self.get_queryset())
            .filter(zaakgeometrie__within=within)
        )

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
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding
        ):
            if zaak.einddatum:
                msg = "Modifying a closed case with current scope is forbidden"
                raise PermissionDenied(detail=msg)
        super().perform_update(serializer)


class StatusViewSet(NotificationCreateMixin,
                    AuditTrailCreateMixin,
                    CheckQueryParamsMixin,
                    ListFilterByAuthorizationsMixin,
                    mixins.CreateModelMixin,
                    viewsets.ReadOnlyModelViewSet):
    """
    Opvragen en beheren van zaakstatussen.

    list:
    Geef een lijst van STATUSsen van ZAAKen.

    Optioneel kan je de queryparameters gebruiken om de resultaten te
    filteren.

    retrieve:
    Haal de details van een zaakstatus op.

    create:
    Voeg een nieuwe STATUS voor een ZAAK toe.

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
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    filterset_class = StatusFilter
    lookup_field = 'uuid'

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE | SCOPE_STATUSSEN_TOEVOEGEN | SCOPEN_ZAKEN_HEROPENEN,
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
        zaak = serializer.validated_data['zaak']
        if not self.request.jwt_auth.has_auth(
            scopes=SCOPE_STATUSSEN_TOEVOEGEN | SCOPEN_ZAKEN_HEROPENEN,
            zaaktype=zaak.zaaktype,
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding
        ):
            if zaak.status_set.exists():
                msg = f"Met de '{SCOPE_ZAKEN_CREATE}' scope mag je slechts 1 status zetten"
                raise PermissionDenied(detail=msg)

        if not self.request.jwt_auth.has_auth(
            scopes=SCOPEN_ZAKEN_HEROPENEN,
            zaaktype=zaak.zaaktype,
            vertrouwelijkheidaanduiding=zaak.vertrouwelijkheidaanduiding
        ):
            if zaak.einddatum:
                msg = "Reopening a closed case with current scope is forbidden"
                raise PermissionDenied(detail=msg)

        super().perform_create(serializer)


class ZaakObjectViewSet(NotificationCreateMixin,
                        ListFilterByAuthorizationsMixin,
                        AuditTrailCreateMixin,
                        mixins.CreateModelMixin,
                        viewsets.ReadOnlyModelViewSet):
    """
    Opvragen en bewerken van ZAAKOBJECTen.

    create:
    Registreer een ZAAKOBJECT relatie.

    list:
    Geef een lijst van ZAAKOBJECTrelaties terug.

    retrieve:
    Geef de details van een ZAAKOBJECT relatie.
    """
    queryset = ZaakObject.objects.all()
    serializer_class = ZaakObjectSerializer
    lookup_field = 'uuid'

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC


class ZaakInformatieObjectViewSet(NotificationCreateMixin,
                                  AuditTrailCreateMixin,
                                  AuditTrailDestroyMixin,
                                  NestedViewSetMixin,
                                  ListFilterByAuthorizationsMixin,
                                  mixins.CreateModelMixin,
                                  mixins.DestroyModelMixin,
                                  viewsets.ReadOnlyModelViewSet):

    """
    Opvragen en bewerken van Zaak-Informatieobject relaties.

    create:
    OPGELET: dit endpoint hoor je als client NIET zelf aan te spreken.

    DRCs gebruiken deze endpoint bij het synchroniseren van relaties. De
    endpoint dient dus bij ZRC providers geimplementeerd te worden, maar voor
    clients is die niet relevant.

    Registreer welk(e) INFORMATIEOBJECT(en) een ZAAK kent.

    **Er wordt gevalideerd op**
    - geldigheid informatieobject URL
    - uniek zijn van relatie ZAAK-INFORMATIEOBJECT
    - bestaan van relatie ZAAK-INFORMATIEOBJECT in het DRC waar het
      informatieobject leeft

    list:
    Geef een lijst van relaties tussen ZAAKen en INFORMATIEOBJECTen.

    retrieve:
    Geef een informatieobject terug wat gekoppeld is aan de huidige zaak

    destroy:
    Verwijder een relatie tussen een zaak en een informatieobject
    """
    queryset = ZaakInformatieObject.objects.all()
    serializer_class = ZaakInformatieObjectSerializer
    permission_classes = (
        permission_class_factory(
            base=ZaakBaseAuthRequired,
            get_obj='_get_zaak',
        ),
    )
    lookup_field = 'uuid'

    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_BIJWERKEN,
        'destroy': SCOPE_ZAKEN_BIJWERKEN,
    }

    parent_retrieve_kwargs = {
        'zaak_uuid': 'uuid',
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def _get_zaak(self):
        if not hasattr(self, '_zaak'):
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

        context['parent_object'] = self._get_zaak()
        return context

    def get_notification_main_object_url(self, data: dict, kanaal: Kanaal) -> str:
        zaak = self._get_zaak()
        return zaak.get_absolute_api_url(request=self.request)

    def get_audittrail_main_object_url(self, data: dict, main_resource: str) -> str:
        zaak = self._get_zaak()
        return zaak.get_absolute_api_url(request=self.request)

class ZaakEigenschapViewSet(NotificationCreateMixin,
                            AuditTrailCreateMixin,
                            NestedViewSetMixin,
                            ListFilterByAuthorizationsMixin,
                            mixins.CreateModelMixin,
                            viewsets.ReadOnlyModelViewSet):
    """
    Opvragen en bewerken van ZAAKEIGENSCHAPpen

    create:
    Registreer een eigenschap van een ZAAK.

    list:
    Geef een collectie van eigenschappen behorend bij een ZAAK.

    retrieve:
    Geef de details van ZaakEigenschap voor een ZAAK.
    """
    queryset = ZaakEigenschap.objects.all()
    serializer_class = ZaakEigenschapSerializer
    permission_classes = (
        permission_class_factory(
            base=ZaakBaseAuthRequired,
            get_obj='_get_zaak',
        ),
    )
    lookup_field = 'uuid'
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_BIJWERKEN,
        'destroy': SCOPE_ZAKEN_BIJWERKEN,
    }
    parent_retrieve_kwargs = {
        'zaak_uuid': 'uuid',
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

    def _get_zaak(self):
        if not hasattr(self, '_zaak'):
            filters = lookup_kwargs_to_filters(self.parent_retrieve_kwargs, self.kwargs)
            self._zaak = get_object_or_404(Zaak, **filters)
        return self._zaak

    def list(self, request, *args, **kwargs):
        zaak = self._get_zaak()
        permission = ZaakAuthScopesRequired()
        if not permission.has_object_permission(self.request, self, zaak):
            raise PermissionDenied
        return super().list(request, *args, **kwargs)


class KlantContactViewSet(NotificationCreateMixin,
                          # ListFilterByAuthorizationsMixin,
                          AuditTrailCreateMixin,
                          mixins.CreateModelMixin,
                          viewsets.ReadOnlyModelViewSet):
    """
    Opvragen en bewerken van KLANTCONTACTen.

    create:
    Registreer een klantcontact bij een ZAAK.

    Indien geen identificatie gegeven is, dan wordt deze automatisch
    gegenereerd.

    list:
    Geef een lijst van KLANTCONTACTen.

    detail:
    Geef de details van een klantcontact voor een ZAAK.
    """
    queryset = KlantContact.objects.all()
    serializer_class = KlantContactSerializer
    lookup_field = 'uuid'
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

class RolViewSet(NotificationCreateMixin,
                 AuditTrailCreateMixin,
                 CheckQueryParamsMixin,
                 ListFilterByAuthorizationsMixin,
                 mixins.CreateModelMixin,
                 viewsets.ReadOnlyModelViewSet):
    """
    Opvragen en bewerken van ROLrelatie tussen een ZAAK en een BETROKKENE.

    create:
    Koppel een BETROKKENE aan een ZAAK.
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    filterset_class = RolFilter
    lookup_field = 'uuid'

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_CREATE,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC


class ResultaatViewSet(NotificationViewSetMixin,
                       AuditTrailViewsetMixin,
                       CheckQueryParamsMixin,
                       ListFilterByAuthorizationsMixin,
                       viewsets.ModelViewSet):
    """
    Opvragen en beheren van resultaten.

    list:
    Geef een lijst van RESULTAATen van ZAAKen.

    Optioneel kan je de queryparameters gebruiken om de resultaten te
    filteren.

    retrieve:
    Haal de details van het RESULTAAT op.

    create:
    Voeg een RESULTAAT voor een ZAAK toe.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - geldigheid URL naar het RESULTAATTYPE

    update:
    Wijzig het RESULTAAT van een ZAAK.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - geldigheid URL naar het RESULTAATTYPE

    partial_update:
    Wijzig het RESULTAAT van een ZAAK.

    **Er wordt gevalideerd op**
    - geldigheid URL naar de ZAAK
    - geldigheid URL naar het RESULTAATTYPE

    destroy:
    Verwijder het RESULTAAT van een ZAAK.

    """
    queryset = Resultaat.objects.all()
    serializer_class = ResultaatSerializer
    filterset_class = ResultaatFilter
    lookup_field = 'uuid'

    permission_classes = (ZaakRelatedAuthScopesRequired,)
    required_scopes = {
        'list': SCOPE_ZAKEN_ALLES_LEZEN,
        'retrieve': SCOPE_ZAKEN_ALLES_LEZEN,
        'create': SCOPE_ZAKEN_BIJWERKEN,
        'destroy': SCOPE_ZAKEN_BIJWERKEN,
        'update': SCOPE_ZAKEN_BIJWERKEN,
        'partial_update': SCOPE_ZAKEN_BIJWERKEN,
    }
    notifications_kanaal = KANAAL_ZAKEN
    audit = AUDIT_ZRC

class ZaakAuditTrailViewSet(AuditTrailViewSet):
    """
    Opvragen van Audit trails horend bij een Zaak.

    list:
    Geef een lijst van AUDITTRAILS die horen bij de huidige Zaak.

    retrieve:
    Haal de details van een AUDITTRAIL op.
    """
    main_resource_lookup_field = 'zaak_uuid'

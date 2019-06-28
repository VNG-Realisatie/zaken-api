import logging
import uuid
from datetime import date

from django.conf import settings
from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from vng_api_common.constants import (
    Archiefnominatie, Archiefstatus, RelatieAarden, RolOmschrijving, RolTypes,
    ZaakobjectTypes
)
from vng_api_common.descriptors import GegevensGroepType
from vng_api_common.fields import (
    BSNField, DaysDurationField, RSINField, VertrouwelijkheidsAanduidingField
)
from vng_api_common.models import APICredential, APIMixin
from vng_api_common.utils import get_uuid_from_path, request_object_attribute
from vng_api_common.validators import alphanumeric_excluding_diacritic

from .constants import (
    AardZaakRelatie, BetalingsIndicatie, GeslachtsAanduiding, SoortRechtsvorm
)
from .query import ZaakQuerySet, ZaakRelatedQuerySet

logger = logging.getLogger(__name__)


class Zaak(APIMixin, models.Model):
    """
    Modelleer de structuur van een ZAAK.

    Een samenhangende hoeveelheid werk met een welgedefinieerde aanleiding
    en een welgedefinieerd eindresultaat, waarvan kwaliteit en doorlooptijd
    bewaakt moeten worden.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )

    # Relate 'is_deelzaak_van'
    # De relatie vanuit een zaak mag niet verwijzen naar
    # dezelfde zaak d.w.z. moet verwijzen naar een andere
    # zaak. Die andere zaak mag geen relatie ?is deelzaak
    # van? hebben (d.w.z. deelzaken van deelzaken worden
    # niet ondersteund).
    hoofdzaak = models.ForeignKey(
        'self', limit_choices_to={'hoofdzaak__isnull': True},
        null=True, blank=True, on_delete=models.CASCADE,
        related_name='deelzaken', verbose_name='is deelzaak van',
        help_text=_("De verwijzing naar de ZAAK, waarom verzocht is door de "
                    "initiator daarvan, die behandeld wordt in twee of meer "
                    "separate ZAAKen waarvan de onderhavige ZAAK er één is.")
    )

    identificatie = models.CharField(
        max_length=40, blank=True,
        help_text='De unieke identificatie van de ZAAK binnen de organisatie '
                  'die verantwoordelijk is voor de behandeling van de ZAAK.',
        validators=[alphanumeric_excluding_diacritic]
    )
    bronorganisatie = RSINField(
        help_text='Het RSIN van de Niet-natuurlijk persoon zijnde de '
                  'organisatie die de zaak heeft gecreeerd. Dit moet een geldig '
                  'RSIN zijn van 9 nummers en voldoen aan '
                  'https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef'
    )
    omschrijving = models.CharField(
        max_length=80, blank=True,
        help_text='Een korte omschrijving van de zaak.')
    toelichting = models.TextField(
        max_length=1000, blank=True,
        help_text='Een toelichting op de zaak.'
    )
    zaaktype = models.URLField(
        _("zaaktype"),
        help_text="URL naar het zaaktype in de CATALOGUS waar deze voorkomt",
        max_length=1000
    )
    registratiedatum = models.DateField(
        help_text='De datum waarop de zaakbehandelende organisatie de ZAAK '
                  'heeft geregistreerd. Indien deze niet opgegeven wordt, '
                  'wordt de datum van vandaag gebruikt.',
        default=date.today
    )
    verantwoordelijke_organisatie = RSINField(
        help_text='Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie '
                  'die eindverantwoordelijk is voor de behandeling van de '
                  'zaak. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan '
                  'https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef'
    )

    startdatum = models.DateField(
        help_text='De datum waarop met de uitvoering van de zaak is gestart')
    einddatum = models.DateField(
        blank=True, null=True,
        help_text='De datum waarop de uitvoering van de zaak afgerond is.',
    )
    einddatum_gepland = models.DateField(
        blank=True, null=True,
        help_text='De datum waarop volgens de planning verwacht wordt dat de '
                  'zaak afgerond wordt.',
    )
    uiterlijke_einddatum_afdoening = models.DateField(
        blank=True, null=True,
        help_text='De laatste datum waarop volgens wet- en regelgeving de zaak '
                  'afgerond dient te zijn.'
    )
    publicatiedatum = models.DateField(
        _("publicatiedatum"), null=True, blank=True,
        help_text=_("Datum waarop (het starten van) de zaak gepubliceerd is of wordt.")
    )

    producten_of_diensten = ArrayField(
        models.URLField(_("URL naar product/dienst"), max_length=1000), default=list,
        help_text=_("De producten en/of diensten die door de zaak worden voortgebracht. "
                    "Dit zijn URLs naar de resources zoals die door de producten- "
                    "en dienstencatalogus-API wordt ontsloten. "
                    "De producten/diensten moeten bij het zaaktype vermeld zijn.")
    )

    communicatiekanaal = models.URLField(
        _("communicatiekanaal"), blank=True, max_length=1000,
        help_text=_("Het medium waarlangs de aanleiding om een zaak te starten is ontvangen. "
                    "URL naar een communicatiekanaal in de VNG-Referentielijst van communicatiekanalen.")
    )

    vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingField(
        _("vertrouwlijkheidaanduiding"),
        help_text=_("Aanduiding van de mate waarin het zaakdossier van de ZAAK voor de openbaarheid bestemd is.")
    )

    betalingsindicatie = models.CharField(
        _("betalingsindicatie"), max_length=20, blank=True,
        choices=BetalingsIndicatie.choices,
        help_text=_("Indicatie of de, met behandeling van de zaak gemoeide, "
                    "kosten betaald zijn door de desbetreffende betrokkene.")
    )
    laatste_betaaldatum = models.DateTimeField(
        _("laatste betaaldatum"), blank=True, null=True,
        help_text=_("De datum waarop de meest recente betaling is verwerkt "
                    "van kosten die gemoeid zijn met behandeling van de zaak.")
    )

    zaakgeometrie = GeometryField(
        blank=True, null=True,
        help_text="Punt, lijn of (multi-)vlak geometrie-informatie."
    )

    verlenging_reden = models.CharField(
        _("reden verlenging"), max_length=200, blank=True,
        help_text=_("Omschrijving van de reden voor het verlengen van de behandeling van de zaak.")
    )
    verlenging_duur = DaysDurationField(
        _("duur verlenging"), blank=True, null=True,
        help_text=_("Het aantal werkbare dagen waarmee de doorlooptijd van de "
                    "behandeling van de ZAAK is verlengd (of verkort) ten opzichte "
                    "van de eerder gecommuniceerde doorlooptijd.")
    )
    verlenging = GegevensGroepType({
        'reden': verlenging_reden,
        'duur': verlenging_duur,
    })

    opschorting_indicatie = models.BooleanField(
        _("indicatie opschorting"), default=False, blank=True,
        help_text=_("Aanduiding of de behandeling van de ZAAK tijdelijk is opgeschort.")
    )
    opschorting_reden = models.CharField(
        _("reden opschorting"), max_length=200, blank=True,
        help_text=_("Omschrijving van de reden voor het opschorten van de behandeling van de zaak.")
    )
    opschorting = GegevensGroepType({
        'indicatie': opschorting_indicatie,
        'reden': opschorting_reden,
    })

    selectielijstklasse = models.URLField(
        _("selectielijstklasse"), blank=True, max_length=1000,
        help_text=_("URL-referentie naar de categorie in de gehanteerde 'Selectielijst Archiefbescheiden' die, gezien "
                    "het zaaktype en het resultaattype van de zaak, bepalend is voor het archiefregime van de zaak.")
    )

    # Archiving
    archiefnominatie = models.CharField(
        _("archiefnominatie"), max_length=40, null=True, blank=True,
        choices=Archiefnominatie.choices,
        help_text=_("Aanduiding of het zaakdossier blijvend bewaard of na een bepaalde termijn vernietigd moet worden.")
    )
    archiefstatus = models.CharField(
        _("archiefstatus"), max_length=40,
        choices=Archiefstatus.choices, default=Archiefstatus.nog_te_archiveren,
        help_text=_("Aanduiding of het zaakdossier blijvend bewaard of na een bepaalde termijn vernietigd moet worden.")
    )
    archiefactiedatum = models.DateField(
        _("archiefactiedatum"), null=True, blank=True,
        help_text=_("De datum waarop het gearchiveerde zaakdossier vernietigd moet worden dan wel overgebracht moet "
                    "worden naar een archiefbewaarplaats. Wordt automatisch berekend bij het aanmaken of wijzigen van "
                    "een RESULTAAT aan deze ZAAK indien nog leeg.")
    )

    objects = ZaakQuerySet.as_manager()

    class Meta:
        verbose_name = 'zaak'
        verbose_name_plural = 'zaken'
        unique_together = ('bronorganisatie', 'identificatie')

    def __str__(self):
        return self.identificatie

    def save(self, *args, **kwargs):
        if not self.identificatie:
            self.identificatie = str(uuid.uuid4())

        if self.betalingsindicatie == BetalingsIndicatie.nvt and self.laatste_betaaldatum:
            self.laatste_betaaldatum = None

        super().save(*args, **kwargs)

    @property
    def current_status_uuid(self):
        status = self.status_set.order_by('-datum_status_gezet').first()
        return status.uuid if status else None

    def unique_representation(self):
        return f"{self.bronorganisatie} - {self.identificatie}"


class RelevanteZaakRelatie(models.Model):
    """
    Registreer een ZAAK als relevant voor een andere ZAAK
    """
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE, related_name='relevante_andere_zaken')
    url = models.URLField(_("URL naar zaak"), max_length=1000)
    aard_relatie = models.CharField(max_length=20, choices=AardZaakRelatie.choices)


class Status(models.Model):
    """
    Modelleer een status van een ZAAK.

    Een aanduiding van de stand van zaken van een ZAAK op basis van
    betekenisvol behaald resultaat voor de initiator van de ZAAK.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    # relaties
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    status_type = models.URLField(
        _("statustype"), max_length=1000,
        help_text=_("URL naar het statustype uit het ZTC.")
    )

    # extra informatie
    datum_status_gezet = models.DateTimeField(
        help_text='De datum waarop de ZAAK de status heeft verkregen.'
    )
    statustoelichting = models.TextField(
        max_length=1000, blank=True,
        help_text='Een, voor de initiator van de zaak relevante, toelichting '
                  'op de status van een zaak.'
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = 'status'
        verbose_name_plural = 'statussen'
        unique_together = ('zaak', 'datum_status_gezet')

    def __str__(self):
        return "Status op {}".format(self.datum_status_gezet)

    def unique_representation(self):
        return f"({self.zaak.unique_representation()}) - {self.datum_status_gezet}"


class Resultaat(models.Model):
    """
    Het behaalde RESULTAAT is een koppeling tussen een RESULTAATTYPE en een
    ZAAK.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    # relaties
    zaak = models.OneToOneField('Zaak', on_delete=models.CASCADE)
    resultaat_type = models.URLField(
        _("resultaattype"), max_length=1000,
        help_text=_("URL naar het resultaattype uit het ZTC.")
    )

    toelichting = models.TextField(
        max_length=1000, blank=True,
        help_text='Een toelichting op wat het resultaat van de zaak inhoudt.'
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = 'resultaat'
        verbose_name_plural = 'resultaten'

    def __str__(self):
        return "Resultaat ({})".format(self.uuid)

    def unique_representation(self):
        if not hasattr(self, '_unique_representation'):
            result_type_desc = request_object_attribute(self.resultaat_type, 'omschrijving', 'resultaattype')
            self._unique_representation = f"({self.zaak.unique_representation()}) - {result_type_desc}"
        return self._unique_representation


class Rol(models.Model):
    """
    Modelleer de rol van een BETROKKENE bij een ZAAK.

    Een of meerdere BETROKKENEn hebben een of meerdere ROL(len) in een ZAAK.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    betrokkene = models.URLField(
        help_text="Een betrokkene gerelateerd aan een zaak",
        max_length=1000, blank=True
    )
    betrokkene_type = models.CharField(
        max_length=100, choices=RolTypes.choices,
        help_text='Soort betrokkene'
    )

    rolomschrijving = models.CharField(
        max_length=80, choices=RolOmschrijving.choices,
        help_text='Algemeen gehanteerde benaming van de aard van de ROL'
    )
    roltoelichting = models.TextField(max_length=1000)

    registratiedatum = models.DateTimeField(
        "registratiedatum", auto_now_add=True,
        help_text="De datum waarop dit object is geregistreerd."
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Rollen"

    def unique_representation(self):
        if self.betrokkene:
            return f"({self.zaak.unique_representation()}) - {get_uuid_from_path(self.betrokkene)}"
        return f"({self.zaak.unique_representation()}) - {self.roltoelichting}"


class ZaakObject(models.Model):
    """
    Modelleer een object behorende bij een ZAAK.

    Het OBJECT in kwestie kan in verschillende andere componenten leven,
    zoals het RSGB.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    object = models.URLField(
        help_text='URL naar de resource die het OBJECT beschrijft.',
        max_length=1000
    )
    relatieomschrijving = models.CharField(
        max_length=80, blank=True,
        help_text='Omschrijving van de betrekking tussen de ZAAK en het OBJECT.'
    )
    object_type = models.CharField(
        max_length=100,
        choices=ZaakobjectTypes.choices,
        help_text="Beschrijft het type object gerelateerd aan de zaak"
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = 'zaakobject'
        verbose_name_plural = 'zaakobjecten'

    def _get_object(self) -> dict:
        """
        Retrieve the `Object` specified as URL in `ZaakObject.object`.

        :return: A `dict` representing the object.
        """
        if not hasattr(self, '_object'):
            object_url = self.object
            self._object = None
            if object_url:
                Client = import_string(settings.ZDS_CLIENT_CLASS)
                client = Client.from_url(object_url)
                client.auth = APICredential.get_auth(object_url)
                self._object = client.retrieve(self.object_type.lower(), url=object_url)
        return self._object

    def unique_representation(self):
        return f"({self.zaak.unique_representation()}) - {get_uuid_from_path(self.object)}"


class ZaakEigenschap(models.Model):
    """
    Een relevant inhoudelijk gegeven waarvan waarden bij
    ZAAKen van eenzelfde ZAAKTYPE geregistreerd moeten
    kunnen worden en dat geen standaard kenmerk is van een
    ZAAK.

    Het RGBZ biedt generieke kenmerken van zaken. Bij zaken van een bepaald zaaktype kan de
    behoefte bestaan om waarden uit te wisselen van gegevens die specifiek zijn voor die zaken. Met
    dit groepattribuutsoort simuleren we de aanwezigheid van dergelijke eigenschappen. Aangezien
    deze eigenschappen specifiek zijn per zaaktype, modelleren we deze eigenschappen hier niet
    specifiek. De eigenschappen worden per zaaktype in een desbetreffende zaaktypecatalogus
    gespecificeerd.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    eigenschap = models.URLField(
        help_text="URL naar de eigenschap in het ZTC",
        max_length=1000
    )
    # TODO - validatie _kan eventueel_ de configuratie van ZTC uitlezen om input
    # te valideren, en per eigenschap een specifiek datatype terug te geven.
    # In eerste instantie laten we het aan de client over om validatie en
    # type-conversie te doen.
    _naam = models.CharField(
        max_length=20,
        help_text=_("De naam van de EIGENSCHAP (overgenomen uit ZTC).")
    )
    waarde = models.TextField()

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = 'zaakeigenschap'
        verbose_name_plural = 'zaakeigenschappen'

    def unique_representation(self):
        return f"({self.zaak.unique_representation()}) - {self._naam}"


class ZaakKenmerk(models.Model):
    """
    Model representatie van de Groepattribuutsoort 'Kenmerk'
    """
    zaak = models.ForeignKey('datamodel.Zaak', on_delete=models.CASCADE)
    kenmerk = models.CharField(
        max_length=40,
        help_text='Identificeert uniek de zaak in een andere administratie.')
    bron = models.CharField(
        max_length=40,
        help_text='De aanduiding van de administratie waar het kenmerk op '
                  'slaat.')

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = 'zaak kenmerk'
        verbose_name_plural = 'zaak kenmerken'


class ZaakInformatieObject(models.Model):
    """
    Modelleer INFORMATIEOBJECTen die bij een ZAAK horen.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey(Zaak, on_delete=models.CASCADE)
    informatieobject = models.URLField(
        "informatieobject",
        help_text="URL-referentie naar het informatieobject in het DRC, waar "
                  "ook de relatieinformatie opgevraagd kan worden.",
        max_length=1000
    )
    aard_relatie = models.CharField(
        "aard relatie", max_length=20,
        choices=RelatieAarden.choices
    )

    # relatiegegevens
    titel = models.CharField(
        "titel", max_length=200, blank=True,
        help_text="De naam waaronder het INFORMATIEOBJECT binnen het OBJECT bekend is."
    )
    beschrijving = models.TextField(
        "beschrijving", blank=True,
        help_text="Een op het object gerichte beschrijving van de inhoud van"
                  "het INFORMATIEOBJECT."
    )
    registratiedatum = models.DateTimeField(
        "registratiedatum", auto_now_add=True,
        help_text="De datum waarop de behandelende organisatie het "
                  "INFORMATIEOBJECT heeft geregistreerd bij het OBJECT. "
                  "Geldige waardes zijn datumtijden gelegen op of voor de "
                  "huidige datum en tijd."
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = "zaakinformatieobject"
        verbose_name_plural = "zaakinformatieobjecten"
        unique_together = ('zaak', 'informatieobject')

    def __str__(self) -> str:
        return f"{self.zaak} - {self.informatieobject}"

    def unique_representation(self):
        if not hasattr(self, '_unique_representation'):
            io_id = request_object_attribute(self.informatieobject, 'identificatie', 'enkelvoudiginformatieobject')
            self._unique_representation = f"({self.zaak.unique_representation()}) - {io_id}"
        return self._unique_representation

    def save(self, *args, **kwargs):
        # override to set aard_relatie
        self.aard_relatie = RelatieAarden.from_object_type('zaak')
        super().save(*args, **kwargs)


class KlantContact(models.Model):
    """
    Modelleer het contact tussen een medewerker en een klant.

    Een uniek en persoonlijk contact van een burger of bedrijfsmedewerker met
    een MEDEWERKER van de zaakbehandelende organisatie over een onderhanden of
    afgesloten ZAAK.
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    identificatie = models.CharField(
        max_length=14, unique=True,
        help_text='De unieke aanduiding van een KLANTCONTACT'
    )
    datumtijd = models.DateTimeField(
        help_text='De datum en het tijdstip waarop het KLANTCONTACT begint'
    )
    kanaal = models.CharField(
        blank=True, max_length=20,
        help_text='Het communicatiekanaal waarlangs het KLANTCONTACT gevoerd wordt'
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = "klantcontact"
        verbose_name_plural = "klantcontacten"

    def __str__(self):
        return self.identificatie

    def save(self, *args, **kwargs):
        if not self.identificatie:
            gen_id = True
            while gen_id:
                identificatie = get_random_string(length=12)
                gen_id = self.__class__.objects.filter(identificatie=identificatie).exists()
            self.identificatie = identificatie
        super().save(*args, **kwargs)

    def unique_representation(self):
        return f'{self.identificatie}'


class ZaakBesluit(models.Model):
    """
    Model Besluit belonged to Zaak
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unieke resource identifier (UUID4)"
    )
    zaak = models.ForeignKey(Zaak, on_delete=models.CASCADE)
    besluit = models.URLField(
        "besluit",
        help_text="URL-referentie naar het informatieobject in het BRC, waar "
                  "ook de relatieinformatie opgevraagd kan worden.",
        max_length=1000
    )

    objects = ZaakRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = "zaakbesluit"
        verbose_name_plural = "zaakbesluiten"
        unique_together = ('zaak', 'besluit')

    def __str__(self) -> str:
        return f"{self.zaak} - {self.besluit}"

    def unique_representation(self):
        return f"{self.zaak} - {self.besluit}"


# models for different betrokkene depend on Rol.betrokkene_type
class NatuurlijkPersoon(models.Model):
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE)

    burgerservicenummer = BSNField(
        blank=True,
        help_text='Het burgerservicenummer, bedoeld in artikel 1.1 van de Wet algemene bepalingen burgerservicenummer.'
    )
    nummer_ander_natuurlijk_persoon = models.CharField(
        max_length=17, blank=True,
        help_text='Het door de gemeente uitgegeven unieke nummer voor een ANDER NATUURLIJK PERSOON'
    )
    a_nummer = models.CharField(
        max_length=10, blank=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9][0-9]{9}$',
                message=_('inp.a-nummer must consist of 10 digits'),
                code='a-nummer-incorrect-format'
            )
        ]
    )
    geslachtsnaam = models.CharField(
        max_length=200, blank=True,
        help_text='De stam van de geslachtsnaam.'
    )
    voorvoegsel_geslachtsnaam = models.CharField(
        max_length=80, blank=True,
    )
    voorletters = models.CharField(
        max_length=20, blank=True,
        help_text='De verzameling letters die gevormd wordt door de eerste letter van '
                  'alle in volgorde voorkomende voornamen.'
    )
    voornamen = models.CharField(
        max_length=200, blank=True,
        help_text='Voornamen bij de naam die de persoon wenst te voeren.'
    )
    geslachtsaanduiding = models.CharField(
        max_length=1, blank=True,
        help_text='Een aanduiding die aangeeft of de persoon een man of een vrouw is, '
                  'of dat het geslacht nog onbekend is.', choices=GeslachtsAanduiding.choices
    )
    geboortedatum = models.CharField(
        max_length=18, blank=True
    )
    verblijfsadres = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het verblijf en adres van de NATUURLIJK PERSOON',
    )
    sub_verblijf_buitenland = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het verblijf in het buitenland'
    )

    class Meta:
        verbose_name = 'natuurlijk persoon'


class NietNatuurlijkPersoon(models.Model):
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE)

    rsin = RSINField(
        blank=True,
        help_text='Het door een kamer toegekend uniek nummer voor de INGESCHREVEN NIET-NATUURLIJK PERSOON',
    )

    nummer_ander_nietnatuurlijk_persoon = models.CharField(
        max_length=17, help_text='Het door de gemeente uitgegeven uniekenummer voor een ANDER NIET-NATUURLIJK PERSOON')

    statutaire_naam = models.TextField(
        max_length=500, blank=True,
        help_text='Naam van de niet-natuurlijke persoon zoals deze is vastgelegd in de statuten (rechtspersoon) of '
                  'in de vennootschapsovereenkomst is overeengekomen (Vennootschap onder firma of Commanditaire '
                  'vennootschap).')

    rechtsvorm = models.CharField(
        max_length=30, choices=SoortRechtsvorm.choices, blank=True,
        help_text='De juridische vorm van de NIET-NATUURLIJK PERSOON.'
    )
    bezoekadres = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het adres van de NIET-NATUURLIJK PERSOON',
    )
    sub_verblijf_buitenland = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het verblijf in het buitenland'
    )

    class Meta:
        verbose_name = 'niet-natuurlijk persoon'


class Vestiging(models.Model):
    """
    Een gebouw of complex van gebouwen waar duurzame uitoefening van de activiteiten
    van een onderneming of rechtspersoon plaatsvindt.
    """
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE)

    vestigings_nummer = models.CharField(
        max_length=24, blank=True,
        help_text='Een korte unieke aanduiding van de Vestiging.'
    )
    handelsnaam = ArrayField(
        models.TextField(max_length=625, blank=True),
        default=list,
        help_text='De naam van de vestiging waaronder gehandeld wordt.')

    verblijfsadres = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het verblijf en adres van de Vestiging',
    )
    sub_verblijf_buitenland = models.CharField(
        max_length=1000, blank=True,
        help_text='De gegevens over het verblijf in het buitenland'
    )

    class Meta:
        verbose_name = 'vestiging'


class OrganisatorischeEenheid(models.Model):
    """
    Het deel van een functioneel afgebakend onderdeel binnen de organisatie
    dat haar activiteiten uitvoert binnen een VESTIGING VAN
    ZAAKBEHANDELENDE ORGANISATIE en die verantwoordelijk is voor de
    behandeling van zaken.
    """
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE)

    identificatie = models.CharField(
        max_length=24, blank=True,
        help_text='Een korte identificatie van de organisatorische eenheid.'
    )
    naam = models.CharField(
        max_length=50, blank=True,
        help_text='De feitelijke naam van de organisatorische eenheid.'
    )
    is_gehuisvest_in = models.CharField(
        max_length=24, blank=True,
    )

    class Meta:
        verbose_name = 'organisatorische eenheid'


class Medewerker(models.Model):
    """
    Een MEDEWERKER van de organisatie die zaken behandelt uit hoofde van
    zijn of haar functie binnen een ORGANISATORISCHE EENHEID.
    """
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE)

    identificatie = models.CharField(
        max_length=24, blank=True,
        help_text='Een korte unieke aanduiding van de MEDEWERKER.')
    achternaam = models.CharField(
        max_length=200, blank=True,
        help_text='De achternaam zoals de MEDEWERKER die in het dagelijkse verkeer gebruikt.'
    )
    voorletters = models.CharField(
        max_length=20, blank=True,
        help_text='De verzameling letters die gevormd wordt door de eerste letter van '
                  'alle in volgorde voorkomende voornamen.')
    voorvoegsel_achternaam = models.CharField(
        max_length=10, blank=True,
        help_text='Dat deel van de geslachtsnaam dat voorkomt in Tabel 36 (GBA), '
                  'voorvoegseltabel, en door een spatie van de geslachtsnaam is')

    class Meta:
        verbose_name = 'medewerker'

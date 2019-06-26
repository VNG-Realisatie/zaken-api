import logging
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.fields import (
    BSNField, RSINField
)
from .base_models import Rol, ZaakObject
from .zaakobjecten import ZakelijkRechtHeeftAlsGerechtigde
from ..constants import (
    GeslachtsAanduiding, SoortRechtsvorm
)

logger = logging.getLogger(__name__)


class RolZaakobjectRelationMixin(models.Model):
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE, null=True)
    zaakobject = models.OneToOneField(ZaakObject, on_delete=models.CASCADE, null=True)

    def clean(self):
        super().clean()
        if self.rol is None and self.zaakobject is None:
            raise ValidationError('Relations to Rol or ZaakObject models should be set')

    class Meta:
        abstract = True


class RolZaakobjectZakelijkRechtRelationMixin(models.Model):
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE, null=True)
    zaakobject = models.OneToOneField(ZaakObject, on_delete=models.CASCADE, null=True)
    zakelijk_rechtHeeft_als_gerechtigde = models.OneToOneField(
        ZakelijkRechtHeeftAlsGerechtigde, on_delete=models.CASCADE, null=True
    )

    def clean(self):
        super().clean()
        if self.rol is None and self.zaakobject is None and self.zakelijk_rechtHeeft_als_gerechtigde is None:
            raise ValidationError('Relations to Rol, ZaakObject or ZakelijkRechtHeeft models should be set')

    class Meta:
        abstract = True


# models for different betrokkene depend on Rol.betrokkene_type
class NatuurlijkPersoon(RolZaakobjectZakelijkRechtRelationMixin):
    inp_bsn = BSNField(
        blank=True,
        help_text='Het burgerservicenummer, bedoeld in artikel 1.1 van de Wet algemene bepalingen burgerservicenummer.'
    )
    anp_identificatie = models.CharField(
        max_length=17, blank=True,
        help_text='Het door de gemeente uitgegeven unieke nummer voor een ANDER NATUURLIJK PERSOON'
    )
    inp_a_nummer = models.CharField(
        max_length=10, blank=True,
        help_text='Het administratienummer van de persoon, bedoeld in de Wet BRP',
        validators=[
            RegexValidator(
                regex=r'^[1-9][0-9]{9}$',
                message=_('inpA_nummer must consist of 10 digits'),
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


class NietNatuurlijkPersoon(RolZaakobjectZakelijkRechtRelationMixin):
    inn_nnp_id = RSINField(
        blank=True,
        help_text='Het door een kamer toegekend uniek nummer voor de INGESCHREVEN NIET-NATUURLIJK PERSOON',
    )

    ann_identificatie = models.CharField(
        max_length=17, blank=True,
        help_text='Het door de gemeente uitgegeven unieke nummer voor een ANDER NIET-NATUURLIJK PERSOON')

    statutaire_naam = models.TextField(
        max_length=500, blank=True,
        help_text='Naam van de niet-natuurlijke persoon zoals deze is vastgelegd in de statuten (rechtspersoon) of '
                  'in de vennootschapsovereenkomst is overeengekomen (Vennootschap onder firma of Commanditaire '
                  'vennootschap).')

    inn_rechtsvorm = models.CharField(
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


class Vestiging(RolZaakobjectRelationMixin):
    """
    Een gebouw of complex van gebouwen waar duurzame uitoefening van de activiteiten
    van een onderneming of rechtspersoon plaatsvindt.
    """
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


class OrganisatorischeEenheid(RolZaakobjectRelationMixin):
    """
    Het deel van een functioneel afgebakend onderdeel binnen de organisatie
    dat haar activiteiten uitvoert binnen een VESTIGING VAN
    ZAAKBEHANDELENDE ORGANISATIE en die verantwoordelijk is voor de
    behandeling van zaken.
    """
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


class Medewerker(RolZaakobjectRelationMixin):
    """
    Een MEDEWERKER van de organisatie die zaken behandelt uit hoofde van
    zijn of haar functie binnen een ORGANISATORISCHE EENHEID.
    """
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

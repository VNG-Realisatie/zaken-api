from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class BetalingsIndicatie(DjangoChoices):
    nvt = ChoiceItem('nvt', _("Er is geen sprake van te betalen, met de zaak gemoeide, kosten."))
    nog_niet = ChoiceItem('nog_niet', _("De met de zaak gemoeide kosten zijn (nog) niet betaald."))
    gedeeltelijk = ChoiceItem('gedeeltelijk', _("De met de zaak gemoeide kosten zijn gedeeltelijk betaald."))
    geheel = ChoiceItem('geheel', _("De met de zaak gemoeide kosten zijn geheel betaald."))


class GeslachtsAanduiding(DjangoChoices):
    man = ChoiceItem('M', 'Man')
    vrouw = ChoiceItem('V', 'Vrouw')
    onbekend = ChoiceItem('O', 'Onbekend')


class SoortRechtsvorm(DjangoChoices):
    besloten_vennootschap = ChoiceItem(
        'Besloten Vennootschap', 'Besloten Vennootschap')
    cooperatie_europees_economische_samenwerking = ChoiceItem(
        'Cooperatie, Europees Economische Samenwerking', 'Cooperatie, Europees Economische Samenwerking')
    europese_cooperatieve_vennootschap = ChoiceItem(
        'Europese Cooperatieve Venootschap', 'Europese Cooperatieve Venootschap')
    europese_naamloze_vennootschap = ChoiceItem(
        'Europese Naamloze Vennootschap', 'Europese Naamloze Vennootschap')
    kerkelijke_organisatie = ChoiceItem(
        'Kerkelijke Organisatie', 'Kerkelijke Organisatie')
    naamloze_vennootschap = ChoiceItem(
        'Naamloze Vennootschap', 'Naamloze Vennootschap')
    onderlinge_waarborg_maatschappij = ChoiceItem(
        'Onderlinge Waarborg Maatschappij', 'Onderlinge Waarborg Maatschappij')
    overig_privaatrechtelijke_rechtspersoon = ChoiceItem(
        'Overig privaatrechtelijke rechtspersoon', 'Overig privaatrechtelijke rechtspersoon')
    stichting = ChoiceItem(
        'Stichting', 'Stichting')
    vereniging = ChoiceItem(
        'Vereniging', 'Vereniging')
    vereniging_van_eigenaars = ChoiceItem(
        'Vereniging van Eigenaars', 'Vereniging van Eigenaars')
    publiekrechtelijke_rechtspersoon = ChoiceItem(
        'Publiekrechtelijke Rechtspersoon', 'Publiekrechtelijke Rechtspersoon')
    vennootschap_onder_firma = ChoiceItem(
        'Vennootschap onder Firma', 'Vennootschap onder Firma')
    maatschap = ChoiceItem(
        'Maatschap', 'Maatschap')
    rederij = ChoiceItem(
        'Rederij', 'Rederij')
    commanditaire_vennootschap = ChoiceItem(
        'Commanditaire vennootschap', 'Commanditaire vennootschap')
    kapitaalvennootschap_binnen_eer = ChoiceItem(
        'Kapitaalvennootschap binnen EER', 'Kapitaalvennootschap binnen EER')
    overige_buitenlandse_rechtspersoon_vennootschap = ChoiceItem(
        'Overige buitenlandse rechtspersoon vennootschap', 'Overige buitenlandse rechtspersoon vennootschap')
    kapitaalvennootschap_buiten_eer = ChoiceItem(
        'Kapitaalvennootschap buiten EER', 'Kapitaalvennootschap buiten EER')


class AardZaakRelatie(DjangoChoices):
    vervolg = ChoiceItem('vervolg', _("De andere zaak gaf aanleiding tot het starten van de onderhanden zaak."))
    onderwerp = ChoiceItem('onderwerp', _("De andere zaak is relevant voor cq. is onderwerp van de onderhanden zaak."))
    bijdrage = ChoiceItem(
        'bijdrage',
        _("Aan het bereiken van de uitkomst van de andere zaak levert de onderhanden zaak een bijdrage.")
    )


# for zaaokbject models
class TyperingInrichtingselement(DjangoChoices):
    bak = ChoiceItem('Bak', 'Bak')
    bord = ChoiceItem('Bord', 'Bord')
    installatie = ChoiceItem('Installatie', 'Installatie')
    kast = ChoiceItem('Kast', 'Kast')
    mast = ChoiceItem('Mast', 'Mast')
    paal = ChoiceItem('Paal', 'Paal')
    sensor = ChoiceItem('Sensor', 'Sensor')
    straatmeubilair = ChoiceItem('Straatmeubilair', 'Straatmeubilair')
    waterinrichtingselement = ChoiceItem('Waterinrichtingselement', 'Waterinrichtingselement')
    weginrichtingselement = ChoiceItem('Weginrichtingselement', 'Weginrichtingselement')


class TyperingKunstwerk(DjangoChoices):
    keermuur = ChoiceItem('Keermuur', 'Keermuur')
    overkluizing = ChoiceItem('Overkluizing', 'Overkluizing')
    duiker = ChoiceItem('Duiker', 'Duiker')
    faunavoorziening = ChoiceItem('Faunavoorziening', 'Faunavoorziening')
    vispassage = ChoiceItem('Vispassage', 'Vispassage')
    bodemval = ChoiceItem('Bodemval', 'Bodemval')
    coupure = ChoiceItem('Coupure', 'Coupure')
    ponton = ChoiceItem('Ponton', 'Ponton')
    voorde = ChoiceItem('Voorde', 'Voorde')
    hoogspanningsmast = ChoiceItem('Hoogspanningsmast', 'Hoogspanningsmast')
    gemaal = ChoiceItem('Gemaal', 'Gemaal')
    perron = ChoiceItem('Perron', 'Perron')
    sluis = ChoiceItem('Sluis', 'Sluis')
    strekdam = ChoiceItem('Strekdam', 'Strekdam')
    steiger = ChoiceItem('Steiger', 'Steiger')
    stuw = ChoiceItem('Stuw', 'Stuw')


class TyperingWater(DjangoChoices):
    zee = ChoiceItem('Zee', 'Zee')
    waterloop = ChoiceItem('Waterloop', 'Waterloop')
    watervlakte = ChoiceItem('Watervlakte', 'Watervlakte')
    greppel_droge_sloot = ChoiceItem('Greppel, droge sloot', 'Greppel, droge sloot')


class TypeSpoorbaan(DjangoChoices):
    breedspoor = ChoiceItem('breedspoor')
    normaalspoor = ChoiceItem('normaalspoor')
    smalspoor = ChoiceItem('smalspoor')
    spoorbaan = ChoiceItem('spoorbaan')


class IndicatieMachtiging(DjangoChoices):
    gemachtigde = ChoiceItem('gemachtigde', _("De betrokkene in de rol bij de zaak is door een andere betrokkene bij "
                                              "dezelfde zaak gemachtigd om namens hem of haar te handelen"))
    machtiginggever = ChoiceItem('machtiginggever', _("De betrokkene in de rol bij de zaak heeft een andere betrokkene "
                                                      "bij dezelfde zaak gemachtigd om namens hem of haar te handelen"))

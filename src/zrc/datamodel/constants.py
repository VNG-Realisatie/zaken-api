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

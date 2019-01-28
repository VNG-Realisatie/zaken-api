from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class ZaakobjectTypes(DjangoChoices):
    verblijfs_object = ChoiceItem('VerblijfsObject', 'Verblijfsobject')
    melding_openbare_ruimte = ChoiceItem('MeldingOpenbareRuimte', "Melding openbare ruimte")
    avg_inzage_verzoek = ChoiceItem('InzageVerzoek', "Inzage verzoek in het kader van de AVG")


class BetalingsIndicatie(DjangoChoices):
    nvt = ChoiceItem('nvt', _("Er is geen sprake van te betalen, met de zaak gemoeide, kosten."))
    nog_niet = ChoiceItem('nog_niet', _("De met de zaak gemoeide kosten zijn (nog) niet betaald."))
    gedeeltelijk = ChoiceItem('gedeeltelijk', _("De met de zaak gemoeide kosten zijn gedeeltelijk betaald."))
    geheel = ChoiceItem('geheel', _("De met de zaak gemoeide kosten zijn geheel betaald."))

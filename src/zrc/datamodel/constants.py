from djchoices import ChoiceItem, DjangoChoices


class ZaakobjectTypes(DjangoChoices):
    verblijfs_object = ChoiceItem('VerblijfsObject', 'Verblijfsobject')
    melding_openbare_ruimte = ChoiceItem('MeldingOpenbareRuimte', "Melding openbare ruimte")
    avg_inzage_verzoek = ChoiceItem('InzageVerzoek', "Inzage verzoek in het kader van de AVG")

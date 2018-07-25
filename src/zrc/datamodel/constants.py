from djchoices import ChoiceItem, DjangoChoices


class RolOmschrijving(DjangoChoices):
    adviseur = ChoiceItem('Adviseur', 'Adviseur')
    behandelaar = ChoiceItem('Behandelaar', 'Behandelaar')
    belanghebbende = ChoiceItem('Belanghebbende', 'Belanghebbende')
    beslisser = ChoiceItem('Beslisser', 'Beslisser')
    initiator = ChoiceItem('Initiator', 'Initiator')
    klantcontacter = ChoiceItem('Klantcontacter', 'Klantcontacter')
    zaakcoordinator = ChoiceItem('Zaakcoördinator', 'Zaakcoördinator')


class RolOmschrijvingGeneriek(RolOmschrijving):
    medeinitiator = ChoiceItem('Mede-initiator', 'Mede-initiator')


class RolTypes(DjangoChoices):
    natuurlijk_persoon = ChoiceItem('Natuurlijk persoon', "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem('Niet-natuurlijk persoon', "Niet-natuurlijk persoon")
    vestiging = ChoiceItem('Vestiging', "Vestiging")
    organisatorische_eenheid = ChoiceItem('Organisatorische eenheid', "Organisatorische eenheid")
    medewerker = ChoiceItem('Medewerker', "Medewerker")


class ZaakobjectTypes(DjangoChoices):
    verblijfs_object = ChoiceItem('VerblijfsObject', 'Verblijfsobject')
    melding_openbare_ruimte = ChoiceItem('MeldingOpenbareRuimte', "Melding openbare ruimte")

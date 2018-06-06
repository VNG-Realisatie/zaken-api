from django.db import models

from zrc.validators import alphanumeric_excluding_diacritic


class Zaak(models.Model):
    """
    Modelleer de structuur van een zaak.

    Een samenhangende hoeveelheid werk met een welgedefinieerde aanleiding
    en een welgedefinieerd eindresultaat, waarvan kwaliteit en doorlooptijd
    bewaakt moeten worden.
    """
    zaakidentificatie = models.CharField(
        max_length=40, unique=True,
        help_text='De unieke identificatie van de ZAAK binnen de organisatie die '
                  'verantwoordelijk is voor de behandeling van de ZAAK.',
        validators=[alphanumeric_excluding_diacritic]
    )

    class Meta:
        verbose_name = 'zaak'
        verbose_name_plural = 'zaken'

    def __str__(self):
        return self.zaakidentificatie


class Status(models.Model):
    """
    Modelleer een status van een zaak.

    Een aanduiding van de stand van zaken van een ZAAK op basis van
    betekenisvol behaald resultaat voor de initiator van de ZAAK.
    """
    # relaties
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    status_type = models.URLField()

    # extra informatie
    datum_status_gezet = models.DateTimeField(
        help_text='De datum waarop de ZAAK de status heeft verkregen.'
    )
    statustoelichting = models.TextField(
        blank=True,
        help_text='Een, voor de initiator van de zaak relevante, toelichting '
                  'op de status van een zaak.'
    )

    class Meta:
        verbose_name = 'status'
        verbose_name_plural = 'statussen'

    def __str__(self):
        return "Status op {}".format(self.datum_status_gezet)

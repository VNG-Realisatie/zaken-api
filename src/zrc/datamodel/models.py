import uuid

from django.db import models

from zrc.validators import alphanumeric_excluding_diacritic


class Zaak(models.Model):
    """
    Modelleer de structuur van een ZAAK.

    Een samenhangende hoeveelheid werk met een welgedefinieerde aanleiding
    en een welgedefinieerd eindresultaat, waarvan kwaliteit en doorlooptijd
    bewaakt moeten worden.
    """
    zaakidentificatie = models.CharField(
        max_length=40, unique=True, blank=True,
        help_text='De unieke identificatie van de ZAAK binnen de organisatie die '
                  'verantwoordelijk is voor de behandeling van de ZAAK.',
        validators=[alphanumeric_excluding_diacritic]
    )
    zaaktype = models.URLField(help_text="URL naar het zaaktype in de CATALOGUS waar deze voorkomt")
    registratiedatum = models.DateField(
        help_text='De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd'
    )
    toelichting = models.TextField(
        max_length=1000, blank=True,
        help_text='Een toelichting op de zaak.'
    )

    class Meta:
        verbose_name = 'zaak'
        verbose_name_plural = 'zaken'

    def __str__(self):
        return self.zaakidentificatie

    def save(self, *args, **kwargs):
        if not self.zaakidentificatie:
            self.zaakidentificatie = str(uuid.uuid4())
        super().save(*args, **kwargs)

    @property
    def current_status_pk(self):
        status = self.status_set.order_by('-datum_status_gezet').first()
        return status.pk if status else None


class Status(models.Model):
    """
    Modelleer een status van een ZAAK.

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
        max_length=1000, blank=True,
        help_text='Een, voor de initiator van de zaak relevante, toelichting '
                  'op de status van een zaak.'
    )

    class Meta:
        verbose_name = 'status'
        verbose_name_plural = 'statussen'

    def __str__(self):
        return "Status op {}".format(self.datum_status_gezet)


class ZaakObject(models.Model):
    """
    Modelleer een object behorende bij een ZAAK.

    Het OBJECT in kwestie kan in verschillende andere componenten leven,
    zoals het RSGB.
    """
    zaak = models.ForeignKey('Zaak', on_delete=models.CASCADE)
    object = models.URLField(help_text='URL naar de resource die het OBJECT beschrijft.')
    relatieomschrijving = models.CharField(
        max_length=80, blank=True,
        help_text='Omschrijving van de betrekking tussen de ZAAK en het OBJECT.'
    )

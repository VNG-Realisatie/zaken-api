# Generated by Django 2.0.10 on 2019-03-11 10:15

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0055_auto_20190226_1254")]

    operations = [
        migrations.AlterField(
            model_name="resultaat",
            name="resultaat_type",
            field=models.URLField(
                help_text="URL naar het resultaattype uit het ZTC.",
                max_length=1000,
                verbose_name="resultaattype",
            ),
        ),
        migrations.AlterField(
            model_name="resultaat",
            name="zaak",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="datamodel.Zaak"
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="betrokkene",
            field=models.URLField(
                help_text="Een betrokkene gerelateerd aan een zaak", max_length=1000
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="status_type",
            field=models.URLField(
                help_text="URL naar het statustype uit het ZTC.",
                max_length=1000,
                verbose_name="statustype",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="communicatiekanaal",
            field=models.URLField(
                blank=True,
                help_text="Het medium waarlangs de aanleiding om een zaak te starten is ontvangen. URL naar een communicatiekanaal in de VNG-Referentielijst van communicatiekanalen.",
                max_length=1000,
                verbose_name="communicatiekanaal",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="hoofdzaak",
            field=models.ForeignKey(
                blank=True,
                help_text="De verwijzing naar de ZAAK, waarom verzocht is door de initiator daarvan, die behandeld wordt in twee of meer separate ZAAKen waarvan de onderhavige ZAAK er één is.",
                limit_choices_to={"hoofdzaak__isnull": True},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deelzaken",
                to="datamodel.Zaak",
                verbose_name="is deelzaak van",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="relevante_andere_zaken",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.URLField(
                    max_length=1000, verbose_name="URL naar andere zaak"
                ),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="selectielijstklasse",
            field=models.URLField(
                blank=True,
                help_text="URL-referentie naar de categorie in de gehanteerde 'Selectielijst Archiefbescheiden' die, gezien het zaaktype en het resultaattype van de zaak, bepalend is voor het archiefregime van de zaak.",
                max_length=1000,
                verbose_name="selectielijstklasse",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="zaaktype",
            field=models.URLField(
                help_text="URL naar het zaaktype in de CATALOGUS waar deze voorkomt",
                max_length=1000,
                verbose_name="zaaktype",
            ),
        ),
        migrations.AlterField(
            model_name="zaakeigenschap",
            name="eigenschap",
            field=models.URLField(
                help_text="URL naar de eigenschap in het ZTC", max_length=1000
            ),
        ),
        migrations.AlterField(
            model_name="zaakinformatieobject",
            name="informatieobject",
            field=models.URLField(
                help_text="URL-referentie naar het informatieobject in het DRC, waar ook de relatieinformatie opgevraagd kan worden.",
                max_length=1000,
                verbose_name="informatieobject",
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="object",
            field=models.URLField(
                help_text="URL naar de resource die het OBJECT beschrijft.",
                max_length=1000,
            ),
        ),
    ]

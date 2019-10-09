# Generated by Django 2.0.9 on 2019-01-07 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0048_auto_20190103_1649")]

    operations = [
        migrations.AddField(
            model_name="zaak",
            name="selectielijstklasse",
            field=models.URLField(
                blank=True,
                help_text="URL-referentie naar de categorie in de gehanteerde 'Selectielijst Archiefbescheiden' die, gezien het zaaktype en het resultaattype van de zaak, bepalend is voor het archiefregime van de zaak.",
                verbose_name="selectielijstklasse",
            ),
        )
    ]

# Generated by Django 2.2.2 on 2019-07-17 15:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0078_auto_20190717_1622")]

    operations = [
        migrations.AddField(
            model_name="rol",
            name="omschrijving",
            field=models.CharField(
                default="",
                editable=False,
                help_text="Omschrijving van de aard van de ROL, afgeleid uit het ROLTYPE.",
                max_length=20,
                verbose_name="omschrijving",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="rol",
            name="roltype",
            field=models.URLField(
                default="",
                help_text="URL-referentie naar een roltype binnen het ZAAKTYPE van de ZAAK.",
                max_length=1000,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rol",
            name="rolomschrijving",
            field=models.CharField(
                choices=[
                    ("adviseur", "Adviseur"),
                    ("behandelaar", "Behandelaar"),
                    ("belanghebbende", "Belanghebbende"),
                    ("beslisser", "Beslisser"),
                    ("initiator", "Initiator"),
                    ("klantcontacter", "Klantcontacter"),
                    ("zaakcoordinator", "Zaakcoördinator"),
                    ("mede_initiator", "Mede-initiator"),
                ],
                editable=False,
                help_text="Algemeen gehanteerde benaming van de aard van de ROL, afgeleid uit het ROLTYPE.",
                max_length=80,
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="object_type_overige",
            field=models.CharField(
                blank=True,
                help_text='Beschrijft het type OBJECT als `objectType` de waarde "overige" heeft.',
                max_length=100,
                validators=[django.core.validators.RegexValidator("[a-z\\_]+")],
            ),
        ),
    ]

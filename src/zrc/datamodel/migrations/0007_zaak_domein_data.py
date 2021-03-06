# Generated by Django 2.0.6 on 2018-06-11 11:13

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0006_zaak_toelichting")]

    operations = [
        migrations.AddField(
            model_name="zaak",
            name="domein_data",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True,
                help_text="Domeinspecifieke data die niet in het RGBZ past.",
                null=True,
            ),
        )
    ]

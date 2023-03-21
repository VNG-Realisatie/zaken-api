# Generated by Django 2.0.6 on 2018-06-11 09:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0005_zaak_registratiedatum")]

    operations = [
        migrations.AddField(
            model_name="zaak",
            name="toelichting",
            field=models.TextField(
                blank=True, help_text="Een toelichting op de zaak.", max_length=1000
            ),
        )
    ]

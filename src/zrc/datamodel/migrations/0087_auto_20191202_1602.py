# Generated by Django 2.2.4 on 2019-12-02 15:02

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("datamodel", "0086_zaakcontactmoment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="zaakcontactmoment",
            name="_objectcontactmoment",
            field=models.URLField(
                blank=True,
                help_text="Link to the related object in the Klantinteractie API",
                verbose_name="objectcontactmoment",
            ),
        ),
        migrations.AlterField(
            model_name="zaakcontactmoment",
            name="contactmoment",
            field=models.URLField(
                help_text="URL-referentie naar het CONTACTMOMENT (in de Klantinteractie API)",
                max_length=1000,
                verbose_name="contactmoment",
            ),
        ),
        migrations.CreateModel(
            name="ZaakVerzoek",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Unieke resource identifier (UUID4)",
                        unique=True,
                    ),
                ),
                (
                    "verzoek",
                    models.URLField(
                        help_text="URL-referentie naar het VERZOEK (in de Klantinteractie API)",
                        max_length=1000,
                        verbose_name="verzoek",
                    ),
                ),
                (
                    "_objectverzoek",
                    models.URLField(
                        blank=True,
                        help_text="Link to the related object in the Klantinteractie API",
                        verbose_name="objectverzoek",
                    ),
                ),
                (
                    "zaak",
                    models.ForeignKey(
                        help_text="URL-referentie naar de ZAAK.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datamodel.Zaak",
                    ),
                ),
            ],
            options={
                "verbose_name": "verzoek",
                "verbose_name_plural": "verzoeken",
                "unique_together": {("zaak", "verzoek")},
            },
        ),
    ]
# Generated by Django 2.0.9 on 2018-12-24 16:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0038_auto_20181219_1027")]

    operations = [
        migrations.CreateModel(
            name="ZaakProductOfDienst",
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
                    "product_of_dienst",
                    models.URLField(
                        help_text="Het product of de dienst die door de zaak wordt voortgebracht.",
                        verbose_name="product of dienst",
                    ),
                ),
            ],
            options={
                "verbose_name": "product of dienst",
                "verbose_name_plural": "producten of diensten",
            },
        ),
        migrations.AddField(
            model_name="zaak",
            name="publicatiedatum",
            field=models.DateField(
                blank=True,
                help_text="Datum waarop (het starten van) de zaak gepubliceerd is of wordt.",
                null=True,
                verbose_name="publicatiedatum",
            ),
        ),
        migrations.AddField(
            model_name="zaakproductofdienst",
            name="zaak",
            field=models.ForeignKey(
                help_text="hoort bij",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
    ]

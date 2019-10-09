# Generated by Django 2.0.13 on 2019-05-31 15:12

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0058_merge_20190531_1435")]

    operations = [
        migrations.AddField(
            model_name="zaakinformatieobject",
            name="aard_relatie",
            field=models.CharField(
                choices=[
                    ("hoort_bij", "Hoort bij, omgekeerd: kent"),
                    ("legt_vast", "Legt vast, omgekeerd: kan vastgelegd zijn als"),
                ],
                default="",
                max_length=20,
                verbose_name="aard relatie",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="zaakinformatieobject",
            name="beschrijving",
            field=models.TextField(
                blank=True,
                help_text="Een op het object gerichte beschrijving van de inhoud vanhet INFORMATIEOBJECT.",
                verbose_name="beschrijving",
            ),
        ),
        migrations.AddField(
            model_name="zaakinformatieobject",
            name="registratiedatum",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                help_text="De datum waarop de behandelende organisatie het INFORMATIEOBJECT heeft geregistreerd bij het OBJECT. Geldige waardes zijn datumtijden gelegen op of voor de huidige datum en tijd.",
                verbose_name="registratiedatum",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="zaakinformatieobject",
            name="titel",
            field=models.CharField(
                blank=True,
                help_text="De naam waaronder het INFORMATIEOBJECT binnen het OBJECT bekend is.",
                max_length=200,
                verbose_name="titel",
            ),
        ),
    ]

# Generated by Django 2.2.2 on 2019-06-17 14:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0061_auto_20190617_1101")]

    operations = [
        migrations.AddField(
            model_name="rol",
            name="registratiedatum",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                help_text="De datum waarop dit object is geregistreerd.",
                verbose_name="registratiedatum",
            ),
            preserve_default=False,
        )
    ]

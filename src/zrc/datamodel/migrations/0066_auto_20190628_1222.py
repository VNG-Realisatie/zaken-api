# Generated by Django 2.2.2 on 2019-06-28 12:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0065_merge_20190628_1222")]

    operations = [
        migrations.RemoveField(model_name="zaak", name="relevante_andere_zaken"),
        migrations.AlterField(
            model_name="relevantezaakrelatie",
            name="zaak",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="relevante_andere_zaken",
                to="datamodel.Zaak",
            ),
        ),
    ]

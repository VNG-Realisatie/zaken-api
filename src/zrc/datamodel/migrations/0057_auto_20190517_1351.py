# Generated by Django 2.0.13 on 2019-05-17 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0056_auto_20190311_1015")]

    operations = [
        migrations.AlterUniqueTogether(
            name="status", unique_together={("zaak", "datum_status_gezet")}
        )
    ]

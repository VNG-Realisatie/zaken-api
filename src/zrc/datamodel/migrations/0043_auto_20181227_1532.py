# Generated by Django 2.0.9 on 2018-12-27 15:32

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0042_zet_vertrouwelijkheidaanduiding")]

    operations = [
        migrations.RenameField(
            model_name="zaak",
            old_name="vertrouwlijkheidaanduiding",
            new_name="vertrouwelijkheidaanduiding",
        )
    ]

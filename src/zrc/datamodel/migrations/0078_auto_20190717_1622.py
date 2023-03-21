# Generated by Django 2.2.2 on 2019-07-17 14:22

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0077_auto_20190717_1433")]

    operations = [
        migrations.RenameField(
            model_name="zaakobject", old_name="type", new_name="object_type"
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("adres", "Adres"),
                    ("besluit", "Besluit"),
                    ("buurt", "Buurt"),
                    ("enkelvoudig_document", "Enkelvoudig document"),
                    ("gemeente", "Gemeente"),
                    ("gemeentelijke_openbare_ruimte", "Gemeentelijke openbare ruimte"),
                    ("huishouden", "Huishouden"),
                    ("inrichtingselement", "Inrichtingselement"),
                    ("kadastrale_onroerende_zaak", "Kadastrale onroerende zaak"),
                    ("kunstwerkdeel", "Kunstwerkdeel"),
                    ("maatschappelijke_activiteit", "Maatschappelijke activiteit"),
                    ("medewerker", "Medewerker"),
                    ("natuurlijk_persoon", "Natuurlijk persoon"),
                    ("niet_natuurlijk_persoon", "Niet-natuurlijk persoon"),
                    ("openbare_ruimte", "Openbare ruimte"),
                    ("organisatorische_eenheid", "Organisatorische eenheid"),
                    ("pand", "Pand"),
                    ("spoorbaandeel", "Spoorbaandeel"),
                    ("status", "Status"),
                    ("terreindeel", "Terreindeel"),
                    ("terrein_gebouwd_object", "Terrein gebouwd object"),
                    ("vestiging", "Vestiging"),
                    ("waterdeel", "Waterdeel"),
                    ("wegdeel", "Wegdeel"),
                    ("wijk", "Wijk"),
                    ("woonplaats", "Woonplaats"),
                    ("woz_deelobject", "Woz deel object"),
                    ("woz_object", "Woz object"),
                    ("woz_waarde", "Woz waarde"),
                    ("zakelijk_recht", "Zakelijk recht"),
                    ("overige", "Overige"),
                ],
                help_text="Beschrijft het type OBJECT gerelateerd aan de ZAAK. Als er geen passend type is, dan moet het type worden opgegeven onder `objectTypeOverige`.",
                max_length=100,
            ),
        ),
    ]

# Generated by Django 2.2.2 on 2019-07-17 08:51

from django.db import migrations, models
import django.db.models.deletion
import vng_api_common.fields


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0075_auto_20190711_1403")]

    operations = [
        migrations.RenameField(
            model_name="resultaat", old_name="resultaat_type", new_name="resultaattype"
        ),
        migrations.RenameField(
            model_name="status", old_name="status_type", new_name="statustype"
        ),
        migrations.AlterField(
            model_name="resultaat",
            name="resultaattype",
            field=models.URLField(
                help_text="URL-referentie naar het RESULTAATTYPE (in de Catalogi API).",
                max_length=1000,
                verbose_name="resultaattype",
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="statustype",
            field=models.URLField(
                help_text="URL-referentie naar het STATUSTYPE (in de Catalogi API).",
                max_length=1000,
                verbose_name="statustype",
            ),
        ),
        migrations.AlterField(
            model_name="klantcontact",
            name="zaak",
            field=models.ForeignKey(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
        migrations.AlterField(
            model_name="relevantezaakrelatie",
            name="aard_relatie",
            field=models.CharField(
                choices=[
                    (
                        "vervolg",
                        "De andere zaak gaf aanleiding tot het starten van de onderhanden zaak.",
                    ),
                    (
                        "onderwerp",
                        "De andere zaak is relevant voor cq. is onderwerp van de onderhanden zaak.",
                    ),
                    (
                        "bijdrage",
                        "Aan het bereiken van de uitkomst van de andere zaak levert de onderhanden zaak een bijdrage.",
                    ),
                ],
                help_text="Benamingen van de aard van de relaties van andere zaken tot (onderhanden) zaken.",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="relevantezaakrelatie",
            name="url",
            field=models.URLField(
                max_length=1000, verbose_name="URL-referentie naar de ZAAK."
            ),
        ),
        migrations.AlterField(
            model_name="resultaat",
            name="zaak",
            field=models.OneToOneField(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="betrokkene",
            field=models.URLField(
                blank=True,
                help_text="URL-referentie naar een betrokkene gerelateerd aan de ZAAK.",
                max_length=1000,
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="betrokkene_type",
            field=models.CharField(
                choices=[
                    ("natuurlijk_persoon", "Natuurlijk persoon"),
                    ("niet_natuurlijk_persoon", "Niet-natuurlijk persoon"),
                    ("vestiging", "Vestiging"),
                    ("organisatorische_eenheid", "Organisatorische eenheid"),
                    ("medewerker", "Medewerker"),
                ],
                help_text="Type van de `betrokkene`.",
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="indicatie_machtiging",
            field=models.CharField(
                blank=True,
                choices=[
                    (
                        "gemachtigde",
                        "De betrokkene in de rol bij de zaak is door een andere betrokkene bij dezelfde zaak gemachtigd om namens hem of haar te handelen",
                    ),
                    (
                        "machtiginggever",
                        "De betrokkene in de rol bij de zaak heeft een andere betrokkene bij dezelfde zaak gemachtigd om namens hem of haar te handelen",
                    ),
                ],
                help_text="Indicatie machtiging",
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="rolomschrijving",
            field=models.CharField(
                choices=[
                    ("adviseur", "Adviseur"),
                    ("behandelaar", "Behandelaar"),
                    ("belanghebbende", "Belanghebbende"),
                    ("beslisser", "Beslisser"),
                    ("initiator", "Initiator"),
                    ("klantcontacter", "Klantcontacter"),
                    ("zaakcoordinator", "Zaakcoördinator"),
                    ("mede_initiator", "Mede-initiator"),
                ],
                help_text="Algemeen gehanteerde benaming van de aard van de ROL",
                max_length=80,
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="zaak",
            field=models.ForeignKey(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="zaak",
            field=models.ForeignKey(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="hoofdzaak",
            field=models.ForeignKey(
                blank=True,
                help_text="URL-referentie naar de ZAAK, waarom verzocht is door de initiator daarvan, die behandeld wordt in twee of meer separate ZAAKen waarvan de onderhavige ZAAK er één is.",
                limit_choices_to={"hoofdzaak__isnull": True},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deelzaken",
                to="datamodel.Zaak",
                verbose_name="is deelzaak van",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="vertrouwelijkheidaanduiding",
            field=vng_api_common.fields.VertrouwelijkheidsAanduidingField(
                choices=[
                    ("openbaar", "Openbaar"),
                    ("beperkt_openbaar", "Beperkt openbaar"),
                    ("intern", "Intern"),
                    ("zaakvertrouwelijk", "Zaakvertrouwelijk"),
                    ("vertrouwelijk", "Vertrouwelijk"),
                    ("confidentieel", "Confidentieel"),
                    ("geheim", "Geheim"),
                    ("zeer_geheim", "Zeer geheim"),
                ],
                help_text="Aanduiding van de mate waarin het zaakdossier van de ZAAK voor de openbaarheid bestemd is.",
                max_length=20,
                verbose_name="vertrouwlijkheidaanduiding",
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="zaaktype",
            field=models.URLField(
                help_text="URL-referentie naar het ZAAKTYPE (in de Catalogi API) in de CATALOGUS waar deze voorkomt",
                max_length=1000,
                verbose_name="zaaktype",
            ),
        ),
        migrations.AlterField(
            model_name="zaakbesluit",
            name="besluit",
            field=models.URLField(
                help_text="URL-referentie naar het BESLUIT (in de Besluiten API), waar ook de relatieinformatie opgevraagd kan worden.",
                max_length=1000,
                verbose_name="besluit",
            ),
        ),
        migrations.AlterField(
            model_name="zaakeigenschap",
            name="_naam",
            field=models.CharField(
                help_text="De naam van de EIGENSCHAP (overgenomen uit de Catalogi API).",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="zaakeigenschap",
            name="eigenschap",
            field=models.URLField(
                help_text="URL-referentie naar de EIGENSCHAP (in de Catalogi API).",
                max_length=1000,
            ),
        ),
        migrations.AlterField(
            model_name="zaakinformatieobject",
            name="informatieobject",
            field=models.URLField(
                help_text="URL-referentie naar het INFORMATIEOBJECT (in de Documenten API), waar ook de relatieinformatie opgevraagd kan worden.",
                max_length=1000,
                verbose_name="informatieobject",
            ),
        ),
        migrations.AlterField(
            model_name="zaakinformatieobject",
            name="zaak",
            field=models.ForeignKey(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="object",
            field=models.URLField(
                blank=True,
                help_text="URL-referentie naar de resource die het OBJECT beschrijft.",
                max_length=1000,
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="type",
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
                help_text="Beschrijft het type `object` gerelateerd aan de ZAAK.",
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="zaak",
            field=models.ForeignKey(
                help_text="URL-referentie naar de ZAAK.",
                on_delete=django.db.models.deletion.CASCADE,
                to="datamodel.Zaak",
            ),
        ),
    ]

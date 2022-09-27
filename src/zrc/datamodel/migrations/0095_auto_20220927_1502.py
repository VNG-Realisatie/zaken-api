# Generated by Django 3.2.14 on 2022-09-27 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datamodel", "0094_auto_20220718_0923"),
    ]

    operations = [
        migrations.AlterField(
            model_name="overige",
            name="overige_data",
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="object_type_overige_definitie",
            field=models.JSONField(
                blank=True,
                help_text='Verwijzing naar het schema van het type OBJECT als `objectType` de waarde "overige" heeft.',
                null=True,
                verbose_name="definitie object type overige",
            ),
        ),
    ]
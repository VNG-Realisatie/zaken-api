# Generated by Django 2.2.2 on 2019-06-13 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datamodel', '0061_medewerker_natuurlijkpersoon_nietnatuurlijkpersoon_organisatorischeeenheid_vestiging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rol',
            name='betrokkene',
            field=models.URLField(blank=True, help_text='Een betrokkene gerelateerd aan een zaak', max_length=1000),
        ),
    ]

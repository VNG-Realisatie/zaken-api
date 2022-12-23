# Generated by Django 3.2.14 on 2022-12-15 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datamodel", "0096_remove_status_indicatie_laatst_gezette_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="vestiging",
            name="kvk_nummer",
            field=models.CharField(
                blank=True,
                help_text="Een uniek nummer gekoppeld aan de onderneming.",
                max_length=8,
            ),
        ),
    ]
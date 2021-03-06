# Generated by Django 2.0.6 on 2018-07-24 09:41
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0020_auto_20180724_0941")]

    operations = [
        migrations.AlterField(
            model_name="klantcontact",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="organisatorischeeenheid",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="rol",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="zaak",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="zaakeigenschap",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="zaakobject",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, help_text="Unieke resource identifier", unique=True
            ),
        ),
    ]

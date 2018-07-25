# Generated by Django 2.0.6 on 2018-07-24 09:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('datamodel', '0018_auto_20180716_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='klantcontact',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='organisatorischeeenheid',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='rol',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='status',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='zaak',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='zaakeigenschap',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
        migrations.AddField(
            model_name='zaakobject',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Unieke resource identifier', null=True),
        ),
    ]
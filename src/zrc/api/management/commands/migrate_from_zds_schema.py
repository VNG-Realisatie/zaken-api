from django.core.management import BaseCommand

from vng_api_common.models import APICredential, JWTSecret
from zds_schema.models import (
    APICredential as OldAPICredential, JWTSecret as OldJWTSecret
)


class Command(BaseCommand):
    help = "Migrate from zds_schema to vng_api_common"

    def handle(self, **options):
        new_secrets = [
            JWTSecret(id=old.id, identifier=old.identifier, secret=old.secret)
            for old in OldJWTSecret.objects.all()
        ]
        JWTSecret.objects.bulk_create(new_secrets)

        new_credentials = [
            APICredential(id=old.id, api_root=old.api_root, client_id=old.client_id, secret=old.secret)
            for old in OldAPICredential.objects.all()
        ]
        APICredential.objects.bulk_create(new_credentials)

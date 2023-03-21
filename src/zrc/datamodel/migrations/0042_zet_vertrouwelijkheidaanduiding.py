# Generated by Django 2.0.9 on 2018-12-27 15:18
import json
import logging

from django.db import migrations

import requests
from vng_api_common.constants import VertrouwelijkheidsAanduiding

from zrc.api.auth import get_auth

logger = logging.getLogger(__name__)

zt_cache = {}


def _get_zaaktype(zaak) -> dict:
    if zaak.zaaktype in zt_cache:
        return zt_cache[zaak.zaaktype]

    auth = get_auth(zaak.zaaktype)
    response = requests.get(zaak.zaaktype, headers=auth)
    response.raise_for_status()

    try:
        zt_cache[zaak.zaaktype] = response.json()
    except json.JSONDecodeError:  # invalid reply from ZTC?
        logger.exception("Invalid JSON for ZaakType %s", zaak.zaaktype)
        zt_cache[zaak.zaaktype] = {}
    return zt_cache[zaak.zaaktype]


def zet_aanduiding(apps, _):
    Zaak = apps.get_model("datamodel", "Zaak")

    default = VertrouwelijkheidsAanduiding.openbaar

    for zaak in Zaak.objects.all():
        try:
            zt = _get_zaaktype(zaak)
        except requests.RequestException:
            logger.exception("Couldn't fetch zaaktype...")
            zt = {}

        if "vertrouwelijkheidaanduiding" not in zt:
            logger.warning(
                "No VertrouwelijkheidsAanduiding set on ZT %s! Using default", zt
            )

        zaak.vertrouwlijkheidaanduiding = zt.get("vertrouwelijkheidaanduiding", default)
        zaak.save()


class Migration(migrations.Migration):
    dependencies = [("datamodel", "0041_zaak_vertrouwlijkheidaanduiding")]

    operations = [migrations.RunPython(zet_aanduiding, migrations.RunPython.noop)]

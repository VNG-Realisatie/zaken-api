import logging

from django.core.cache import caches
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from vng_api_common.models import APICredential
from zds_client import Client

from zrc.api.utils import get_absolute_url
from zrc.datamodel.models import ZaakContactMoment, ZaakInformatieObject

logger = logging.getLogger(__name__)


class SyncError(Exception):
    pass


def sync_create_zio(relation: ZaakInformatieObject):
    zaak_url = get_absolute_url("zaak-detail", relation.zaak.uuid)

    logger.info("Zaak: %s", zaak_url)
    logger.info("Informatieobject: %s", relation.informatieobject)

    # Define the remote resource with which we need to interact
    resource = "objectinformatieobject"
    client = Client.from_url(relation.informatieobject)
    client.auth = APICredential.get_auth(relation.informatieobject)

    try:
        client.create(
            resource,
            {
                "object": zaak_url,
                "informatieobject": relation.informatieobject,
                "objectType": "zaak",
            },
        )
    except Exception as exc:
        logger.error(f"Could not create remote relation", exc_info=1)
        raise SyncError(f"Could not create remote relation") from exc


def sync_delete_zio(relation: ZaakInformatieObject):
    zaak_url = get_absolute_url("zaak-detail", relation.zaak.uuid)

    logger.info("Zaak: %s", zaak_url)
    logger.info("Informatieobject: %s", relation.informatieobject)

    # Define the remote resource with which we need to interact
    resource = "objectinformatieobject"
    client = Client.from_url(relation.informatieobject)
    client.auth = APICredential.get_auth(relation.informatieobject)

    # Retrieve the url of the relation between the object and
    # the informatieobject
    response = client.list(
        resource,
        query_params={
            "object": zaak_url,
            "informatieobject": relation.informatieobject,
        },
    )
    try:
        relation_url = response[0]["url"]
    except IndexError as exc:
        msg = "No relations found in DRC for this Zaak"
        logger.error(msg, exc_info=1)
        raise IndexError(msg) from exc

    try:
        client.delete(resource, url=relation_url)
    except Exception as exc:
        logger.error(f"Could not delete remote relation", exc_info=1)
        raise SyncError(f"Could not delete remote relation") from exc


def sync_create_zaakcontactmoment(relation: ZaakContactMoment):
    zaak_url = get_absolute_url("zaak-detail", relation.zaak.uuid)

    logger.info("Zaak: %s", zaak_url)
    logger.info("Contactmoment: %s", relation.contactmoment)

    # Define the remote resource with which we need to interact
    resource = "objectcontactmoment"
    client = Client.from_url(relation.contactmoment)
    client.auth = APICredential.get_auth(relation.contactmoment)

    try:
        response = client.create(
            resource,
            {
                "object": zaak_url,
                "contactmoment": relation.contactmoment,
                "objectType": "zaak",
            },
        )
    except Exception as exc:
        logger.error(f"Could not create remote relation", exc_info=1)
        raise SyncError(f"Could not create remote relation") from exc

    # save ZaakBesluit url for delete signal
    relation._objectcontactmoment = response["url"]
    relation.save()


def sync_delete_zaakcontactmoment(relation: ZaakContactMoment):
    resource = "objectinformatieobject"
    client = Client.from_url(relation.contactmoment)
    client.auth = APICredential.get_auth(relation.contactmoment)

    try:
        client.delete(resource, url=relation._objectcontactmoment)
    except Exception as exc:
        logger.error(f"Could not delete remote relation", exc_info=1)
        raise SyncError(f"Could not delete remote relation") from exc


@receiver(
    [post_save, pre_delete],
    sender=ZaakInformatieObject,
    dispatch_uid="sync.sync_informatieobject_relation",
)
def sync_informatieobject_relation(
    sender, instance: ZaakInformatieObject = None, **kwargs
):
    signal = kwargs["signal"]
    if signal is post_save and kwargs.get("created", False):
        sync_create_zio(instance)
    elif signal is pre_delete:
        # Add the uuid of the ZaakInformatieObject to the list of ZIOs that are
        # marked for delete, causing them not to show up when performing
        # GET requests on the ZRC, allowing the validation in the DRC to pass
        cache = caches["drc_sync"]
        marked_zios = cache.get("zios_marked_for_delete")
        if marked_zios:
            cache.set("zios_marked_for_delete", marked_zios + [instance.uuid])
        else:
            cache.set("zios_marked_for_delete", [instance.uuid])

        try:
            sync_delete_zio(instance)
        finally:
            marked_zios = cache.get("zios_marked_for_delete")
            marked_zios.remove(instance.uuid)
            cache.set("zios_marked_for_delete", marked_zios)


@receiver(
    [post_save, pre_delete],
    sender=ZaakContactMoment,
    dispatch_uid="sync.sync_contactmoment_relation",
)
def sync_contactmoment_relation(sender, instance: ZaakContactMoment = None, **kwargs):
    signal = kwargs["signal"]
    if signal is post_save and not instance._objectcontactmoment:
        sync_create_zaakcontactmoment(instance)
    elif signal is pre_delete and instance._objectcontactmoment:
        cache = caches["kcc_sync"]
        marked_zcms = cache.get("zcms_marked_for_delete")
        if marked_zcms:
            cache.set("zcms_marked_for_delete", marked_zcms + [instance.uuid])
        else:
            cache.set("zcms_marked_for_delete", [instance.uuid])

        try:
            sync_delete_zaakcontactmoment(instance)
        finally:
            marked_zcms = cache.get("zcms_marked_for_delete")
            marked_zcms.remove(instance.uuid)
            cache.set("zcms_marked_for_delete", marked_zcms)

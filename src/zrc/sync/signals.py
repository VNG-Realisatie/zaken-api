import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse

import requests
from vng_api_common.models import APICredential
from vng_api_common.utils import get_uuid_from_path
from zds_client import Client, extract_params, get_operation_url

from zrc.datamodel.models import ZaakInformatieObject

logger = logging.getLogger(__name__)


class SyncError(Exception):
    pass


def sync_create(relation: ZaakInformatieObject):
    operation = 'create'

    # build the URL of the Zaak
    path = reverse('zaak-detail', kwargs={
        'version': settings.REST_FRAMEWORK['DEFAULT_VERSION'],
        'uuid': relation.zaak.uuid,
    })
    domain = Site.objects.get_current().domain
    protocol = 'https' if settings.IS_HTTPS else 'http'
    zaak_url = f'{protocol}://{domain}{path}'

    logger.info("Zaak: %s", zaak_url)
    logger.info("Informatieobject: %s", relation.informatieobject)

    # Define the remote resource with which we need to interact
    resource = 'objectinformatieobject'
    client = Client.from_url(relation.informatieobject)
    client.auth = APICredential.get_auth(relation.informatieobject)

    try:
        client.create(
            resource,
            {'object': zaak_url, 'informatieobject': relation.informatieobject, 'objectType': 'zaak'}
        )
    except Exception as exc:
        logger.error(f"Could not {operation} remote relation", exc_info=1)
        raise SyncError(f"Could not {operation} remote relation") from exc


def sync_delete(relation: ZaakInformatieObject):
    operation = 'delete'

    # build the URL of the Zaak
    path = reverse('zaak-detail', kwargs={
        'version': settings.REST_FRAMEWORK['DEFAULT_VERSION'],
        'uuid': relation.zaak.uuid,
    })
    domain = Site.objects.get_current().domain
    protocol = 'https' if settings.IS_HTTPS else 'http'
    zaak_url = f'{protocol}://{domain}{path}'

    logger.info("Zaak: %s", zaak_url)
    logger.info("Informatieobject: %s", relation.informatieobject)

    # Define the remote resource with which we need to interact
    resource = 'objectinformatieobject'
    client = Client.from_url(relation.informatieobject)
    client.auth = APICredential.get_auth(relation.informatieobject)

    # Retrieve the url of the relation between the object and
    # the informatieobject
    response = client.list(resource, query_params={
        'object': zaak_url,
        'informatieobject': relation.informatieobject
    })
    try:
        relation_url = response[0]['url']
    except IndexError as exc:
        msg = "No relations found in DRC for this Zaak"
        logger.error(msg, exc_info=1)
        raise IndexError(msg) from exc

    try:
        client.delete(resource, url=relation_url)
    except Exception as exc:
        logger.error(f"Could not {operation} remote relation", exc_info=1)
        raise SyncError(f"Could not {operation} remote relation") from exc


@receiver([post_save, post_delete], sender=ZaakInformatieObject, dispatch_uid='sync.sync_informatieobject_relation')
def sync_informatieobject_relation(sender, instance: ZaakInformatieObject=None, **kwargs):
    signal = kwargs['signal']
    if signal is post_save and kwargs.get('created', False):
        sync_create(instance)
    elif signal is post_delete:
        sync_delete(instance)

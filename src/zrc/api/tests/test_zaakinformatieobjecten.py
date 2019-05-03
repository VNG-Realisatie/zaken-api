from unittest import skip

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin

from zrc.datamodel.tests.factories import (
    ZaakFactory, ZaakInformatieObjectFactory
)

from .utils import reverse

INFORMATIE_OBJECT = 'https://drc.nl/api/v1/enkelvoudiginformatieobjecten/1234'


@override_settings(
    LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
    ZDS_CLIENT_CLASS='vng_api_common.mocks.ObjectInformatieObjectClient'
)
class ZaakInformatieObjectTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_create(self):
        zaak = ZaakFactory.create()
        url = reverse('zaakinformatieobject-list', kwargs={'zaak_uuid': zaak.uuid})

        response = self.client.post(url, {
            'informatieobject': INFORMATIE_OBJECT,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        zio = zaak.zaakinformatieobject_set.get()
        self.assertEqual(zio.informatieobject, INFORMATIE_OBJECT)

    @skip('HTTP DELETE is currently not supported')
    def test_delete(self):
        zio = ZaakInformatieObjectFactory.create()
        zaak = zio.zaak
        url = reverse('zaakinformatieobject-detail', kwargs={
            'zaak_uuid': zaak.uuid,
            'uuid': zio.uuid
        })

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(zaak.zaakinformatieobject_set.exists())

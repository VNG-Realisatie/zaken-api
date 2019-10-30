from django.test import override_settings
from django.db import transaction

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse, get_validation_errors

from zrc.datamodel.tests.factories import ZaakContactMomentFactory, ZaakFactory
from zrc.datamodel.models import ZaakContactMoment
from zrc.sync.signals import SyncError
from .mixins import ZaakContactMomentSyncMixin

CONTACTMOMENT = "https://kcc.nl/api/v1/contactmomenten/1234"


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakContactMomentTests(ZaakContactMomentSyncMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_create(self):
        zaak = ZaakFactory.create()
        url = reverse("zaakcontactmoment-list")

        response = self.client.post(
            url, {"contactmoment": CONTACTMOMENT, "zaak": reverse(zaak)}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        zaak_contactmoment = zaak.zaakcontactmoment_set.get()
        self.assertEqual(zaak_contactmoment.contactmoment, CONTACTMOMENT)

    def test_create_fail_sync(self):
        self.mocked_sync_create_zcm.side_effect = SyncError("Sync failed")

        zaak = ZaakFactory.create()
        url = reverse("zaakcontactmoment-list")

        response = self.client.post(
            url, {"contactmoment": CONTACTMOMENT, "zaak": reverse(zaak)}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, 'nonFieldErrors')
        self.assertEqual(error['reason'], 'Sync failed')

        self.assertEqual(ZaakContactMoment.objects.count(), 0)

    def test_delete(self):
        zaak_contactmoment = ZaakContactMomentFactory.create(
            _objectcontactmoment='http://example.com/api/v1/_objectcontactmomenten/1'
        )
        zaak = zaak_contactmoment.zaak
        url = reverse(zaak_contactmoment)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(zaak.zaakcontactmoment_set.exists())

    def test_detele_fail_sync(self):
        self.mocked_sync_delete_zcm.side_effect = SyncError("Sync failed")

        zaak_contactmoment = ZaakContactMomentFactory.create(
            _objectcontactmoment='http://example.com/api/v1/_objectcontactmomenten/1'
        )
        url = reverse(zaak_contactmoment)

        with transaction.atomic():
            response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, 'nonFieldErrors')
        self.assertEqual(error['reason'], 'Sync failed')

        self.assertEqual(ZaakContactMoment.objects.get(), zaak_contactmoment)


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakContactMomentFilterTests(ZaakContactMomentSyncMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    list_url = reverse(ZaakContactMoment)

    def test_filter_zaak(self):
        zaak = ZaakFactory.create()
        zaak_url = reverse(zaak)
        ZaakContactMomentFactory.create(zaak=zaak)

        response = self.client.get(self.list_url, {"zaak": f"http://testserver{zaak_url}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["zaak"], f"http://testserver{zaak_url}")

    def test_filter_contactmoment(self):
        ZaakContactMomentFactory.create(contactmoment=CONTACTMOMENT)

        response = self.client.get(self.list_url, {"contactmoment": CONTACTMOMENT})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["contactmoment"], CONTACTMOMENT)

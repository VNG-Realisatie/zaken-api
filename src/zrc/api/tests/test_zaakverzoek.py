from django.db import transaction
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, get_validation_errors, reverse

from zrc.datamodel.models import ZaakVerzoek
from zrc.datamodel.tests.factories import ZaakFactory, ZaakVerzoekFactory
from zrc.sync.signals import SyncError

from .mixins import ZaakVerzoekSyncMixin

VERZOEK = "https://kic.nl/api/v1/verzoeken/1234"


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakVerzoekTests(ZaakVerzoekSyncMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_create(self):
        zaak = ZaakFactory.create()
        url = reverse("zaakverzoek-list")

        response = self.client.post(url, {"verzoek": VERZOEK, "zaak": reverse(zaak)})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        zaak_verzoek = zaak.zaakverzoek_set.get()
        self.assertEqual(zaak_verzoek.verzoek, VERZOEK)

    def test_create_fail_sync(self):
        self.mocked_sync_create_zv.side_effect = SyncError("Sync failed")

        zaak = ZaakFactory.create()
        url = reverse("zaakverzoek-list")

        response = self.client.post(url, {"verzoek": VERZOEK, "zaak": reverse(zaak)})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["reason"], "Sync failed")

        self.assertEqual(ZaakVerzoek.objects.count(), 0)

    def test_delete(self):
        zaak_verzoek = ZaakVerzoekFactory.create(
            _objectverzoek="http://example.com/api/v1/_objectverzoeken/1"
        )
        zaak = zaak_verzoek.zaak
        url = reverse(zaak_verzoek)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(zaak.zaakverzoek_set.exists())

    def test_detele_fail_sync(self):
        self.mocked_sync_delete_zv.side_effect = SyncError("Sync failed")

        zaak_verzoek = ZaakVerzoekFactory.create(
            _objectverzoek="http://example.com/api/v1/_objectverzoeken/1"
        )
        url = reverse(zaak_verzoek)

        with transaction.atomic():
            response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["reason"], "Sync failed")

        self.assertEqual(ZaakVerzoek.objects.get(), zaak_verzoek)


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakVerzoekFilterTests(ZaakVerzoekSyncMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    list_url = reverse(ZaakVerzoek)

    def test_filter_zaak(self):
        zaak = ZaakFactory.create()
        zaak_url = reverse(zaak)
        ZaakVerzoekFactory.create(zaak=zaak)

        response = self.client.get(
            self.list_url,
            {"zaak": f"http://testserver.com{zaak_url}"},
            HTTP_HOST="testserver.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["zaak"], f"http://testserver.com{zaak_url}")

    def test_filter_verzoek(self):
        ZaakVerzoekFactory.create(verzoek=VERZOEK)

        response = self.client.get(self.list_url, {"verzoek": VERZOEK})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["verzoek"], VERZOEK)

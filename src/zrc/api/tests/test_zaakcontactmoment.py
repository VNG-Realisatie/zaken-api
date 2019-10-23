from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse

from zrc.datamodel.tests.factories import ZaakContactMomentFactory, ZaakFactory


CONTACTMOMENT = "https://kcc.nl/api/v1/contactmomenten/1234"


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakContactMomentTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_create(self):
        zaak = ZaakFactory.create()
        url = reverse("zaakcontactmoment-list")

        response = self.client.post(url, {"contactmoment": CONTACTMOMENT, "zaak": reverse(zaak)})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        zaak_contactmoment = zaak.zaakcontactmoment_set.get()
        self.assertEqual(zaak_contactmoment.contactmoment, CONTACTMOMENT)

    def test_delete(self):
        zaak_contactmoment = ZaakContactMomentFactory.create()
        zaak = zaak_contactmoment.zaak
        url = reverse(zaak_contactmoment)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(zaak.zaakcontactmoment_set.exists())

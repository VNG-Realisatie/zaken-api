from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, get_operation_url

from zrc.datamodel.tests.factories import KlantContactFactory


class ZaakObjectFilterTestCase(JWTAuthMixin, APITestCase):

    heeft_alle_autorisaties = True

    def test_filter_zaak(self):
        klantcontact1 = KlantContactFactory.create()
        KlantContactFactory.create()
        zaak = klantcontact1.zaak
        zaak_url = get_operation_url("zaak_retrieve", uuid=zaak.uuid)
        klantcontact1_url = get_operation_url(
            "klantcontact_retrieve", uuid=klantcontact1.uuid
        )
        url = get_operation_url("klantcontact_list")

        response = self.client.get(
            url,
            {"zaak": f"http://testserver.com{zaak_url}"},
            HTTP_HOST="testserver.com",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["url"], f"http://testserver.com{klantcontact1_url}")

    def test_list_page(self):
        KlantContactFactory.create_batch(2)
        url = get_operation_url("klantcontact_list")

        response = self.client.get(url, {"page": 1}, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]
        self.assertEqual(len(data), 2)

    def test_deprecated(self):
        url = get_operation_url("klantcontact_list")

        response = self.client.get(url)

        self.assertIn("Warning", response)
        msg = (
            "Deze endpoint is verouderd en zal binnenkort uit dienst worden genomen. "
            "Maak gebruik van de vervangende contactmomenten API."
        )
        self.assertEqual(response["Warning"], f'299 "http://testserver{url}" "{msg}"')

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, get_operation_url

from zrc.datamodel.tests.factories import KlantContactFactory


class ZaakObjectFilterTestCase(JWTAuthMixin, APITestCase):

    heeft_alle_autorisaties = True

    def test_filter_zaak(self):
        klantcontact1 = KlantContactFactory.create()
        klantcontact2 = KlantContactFactory.create()
        zaak = klantcontact1.zaak
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        klantcontact1_url = get_operation_url(
            "klantcontact_read", uuid=klantcontact1.uuid
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

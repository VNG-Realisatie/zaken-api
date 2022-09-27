from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import (
    JWTAuthMixin,
    TypeCheckMixin,
    get_operation_url,
    get_validation_errors,
    reverse,
)

from zrc.datamodel.tests.factories import ZaakFactory
from zrc.tests.utils import ZAAK_WRITE_KWARGS


class ZaakZoekTests(JWTAuthMixin, TypeCheckMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_zoek_uuid_in(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak_zoek")
        data = {"uuid__in": [zaak1.uuid, zaak2.uuid]}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]
        data = sorted(data, key=lambda zaak: zaak["identificatie"])

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["url"], f"http://testserver{reverse(zaak1)}")
        self.assertEqual(data[1]["url"], f"http://testserver{reverse(zaak2)}")

    def test_zoek_without_params(self):
        url = get_operation_url("zaak_zoek")

        response = self.client.post(url, {}, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["code"], "empty_search_body")

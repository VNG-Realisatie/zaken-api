from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse

from zrc.datamodel.tests.factories import StatusFactory


class StatusTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    @override_settings(
        LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
        ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
    )
    def test_filter_statussen_op_zaak(self):
        status1, status2 = StatusFactory.create_batch(2)
        assert status1.zaak != status2.zaak
        status1_url = reverse("status-detail", kwargs={"uuid": status1.uuid})
        status2_url = reverse("status-detail", kwargs={"uuid": status2.uuid})

        list_url = reverse("status-list")
        zaak_path = reverse(status1.zaak)

        response = self.client.get(
            list_url,
            {"zaak": f"http://testserver.com{zaak_path}"},
            HTTP_HOST="testserver.com",
        )

        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["url"], f"http://testserver.com{status1_url}")
        self.assertNotEqual(
            response_data[0]["url"], f"http://testserver.com{status2_url}"
        )

    def test_filter_statussen_on_zaak_external_url(self):
        StatusFactory.create()
        list_url = reverse("status-list")

        bad_urls = [
            "https://google.nl",
            "https://example.com/",
            "https://example.com/404",
        ]

        for bad_url in bad_urls:
            with self.subTest(bad_url=bad_url):
                response = self.client.get(list_url, {"zaak": bad_url})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["count"], 0)

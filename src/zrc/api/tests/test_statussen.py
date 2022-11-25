import datetime

from django.test import override_settings
from django.utils import timezone

from rest_framework import status as rest_framework_status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse

from zrc.api.tests.test_zaakinformatieobjecten import dt_to_api
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

        self.assertEqual(response.status_code, rest_framework_status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["url"], f"http://testserver.com{status1_url}")
        self.assertNotEqual(
            response_data[0]["url"], f"http://testserver.com{status2_url}"
        )

    @override_settings(
        LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
        ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
    )
    def test_filter_statussen_op_indicatie_laatst_gezette_status(self):
        status1, status2 = StatusFactory.create_batch(2)
        assert status1.zaak != status2.zaak
        status1.datum_status_gezet = dt_to_api(
            datetime.datetime(1900, 11, 15, 20, 20, 58, tzinfo=timezone.utc)
        )
        status2.datum_status_gezet = dt_to_api(
            datetime.datetime(2000, 11, 15, 20, 20, 58, tzinfo=timezone.utc)
        )

        status1.save()
        status2.save()

        status1_url = reverse("status-detail", kwargs={"uuid": status1.uuid})
        status2_url = reverse("status-detail", kwargs={"uuid": status2.uuid})

        list_url = reverse("status-list")

        response = self.client.get(
            list_url,
            {"indicatieLaatstGezetteStatus": True},
            HTTP_HOST="testserver.com",
        )

        response_data = response.json()["results"]

        self.assertEqual(response.status_code, rest_framework_status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["url"], f"http://testserver.com{status2_url}")
        self.assertNotEqual(
            response_data[0]["url"], f"http://testserver.com{status1_url}"
        )

    @override_settings(
        LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
        ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
    )
    def test_status_detail(self):
        status = StatusFactory()
        url = reverse("status-detail", kwargs={"uuid": status.uuid})
        zaak_url = reverse("zaak-detail", kwargs={"uuid": status.zaak.uuid})

        response = self.client.get(url, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, rest_framework_status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            {
                "url": f"http://testserver.com{url}",
                "uuid": str(status.uuid),
                "zaak": f"http://testserver.com{zaak_url}",
                "statustype": status.statustype,
                "datumStatusGezet": dt_to_api(status.datum_status_gezet),
                "statustoelichting": status.statustoelichting,
                "indicatieLaatstGezetteStatus": (True),
                "gezetdoor": status.gezetdoor,
                "zaakinformatieobjecten": [],
            },
        )

    def test_status_indicatie_laatst_gezette_status(self):
        status_latest = StatusFactory()
        status_old = StatusFactory(
            datum_status_gezet=dt_to_api(
                datetime.datetime(1900, 11, 15, 20, 20, 58, tzinfo=timezone.utc)
            )
        )
        url_latest = reverse("status-detail", kwargs={"uuid": status_latest.uuid})
        url_old = reverse("status-detail", kwargs={"uuid": status_old.uuid})

        zaak_url_latest = reverse(
            "zaak-detail", kwargs={"uuid": status_latest.zaak.uuid}
        )
        zaak_url_old = reverse("zaak-detail", kwargs={"uuid": status_old.zaak.uuid})

        response_latest = self.client.get(url_latest, HTTP_HOST="testserver.com")
        response_old = self.client.get(url_old, HTTP_HOST="testserver.com")

        self.assertEqual(response_latest.status_code, rest_framework_status.HTTP_200_OK)
        self.assertEqual(response_old.status_code, rest_framework_status.HTTP_200_OK)

        self.assertEqual(
            response_latest.json(),
            {
                "url": f"http://testserver.com{url_latest}",
                "uuid": str(status_latest.uuid),
                "zaak": f"http://testserver.com{zaak_url_latest}",
                "statustype": status_latest.statustype,
                "datumStatusGezet": dt_to_api(status_latest.datum_status_gezet),
                "statustoelichting": status_latest.statustoelichting,
                "indicatieLaatstGezetteStatus": (True),
                "gezetdoor": status_latest.gezetdoor,
                "zaakinformatieobjecten": [],
            },
        )
        self.assertEqual(
            response_old.json(),
            {
                "url": f"http://testserver.com{url_old}",
                "uuid": str(status_old.uuid),
                "zaak": f"http://testserver.com{zaak_url_old}",
                "statustype": status_old.statustype,
                "datumStatusGezet": status_old.datum_status_gezet,
                "statustoelichting": status_old.statustoelichting,
                "indicatieLaatstGezetteStatus": (False),
                "gezetdoor": status_old.gezetdoor,
                "zaakinformatieobjecten": [],
            },
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

                self.assertEqual(
                    response.status_code, rest_framework_status.HTTP_200_OK
                )
                self.assertEqual(response.data["count"], 0)

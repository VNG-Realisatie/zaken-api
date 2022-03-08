import concurrent.futures
import uuid
from datetime import datetime
from unittest.mock import patch

from django.db import close_old_connections
from django.test import override_settings
from django.utils import timezone

from freezegun import freeze_time
from rest_framework import status as rest_framework_status
from rest_framework.test import APITestCase, APITransactionTestCase
from vng_api_common.constants import RelatieAarden
from vng_api_common.tests import JWTAuthMixin, get_validation_errors, reverse
from vng_api_common.validators import IsImmutableValidator
from zds_client.tests.mocks import mock_client

from zrc.datamodel.models import Zaak, ZaakInformatieObject
from zrc.datamodel.tests.factories import StatusFactory, ZaakFactory, ZaakInformatieObjectFactory
from zrc.sync.signals import SyncError

from .mixins import ZaakInformatieObjectSyncMixin

ZAAKTYPE = f"http://example.com/ztc/api/v1/zaaktypen/{uuid.uuid4().hex}"
INFORMATIEOBJECT = (
    f"http://example.com/drc/api/v1/enkelvoudiginformatieobjecten/{uuid.uuid4().hex}"
)
INFORMATIEOBJECT_TYPE = (
    f"http://example.com/ztc/api/v1/informatieobjecttypen/{uuid.uuid4().hex}"
)

RESPONSES = {
    INFORMATIEOBJECT: {
        "url": INFORMATIEOBJECT,
        "informatieobjecttype": INFORMATIEOBJECT_TYPE,
    },
    ZAAKTYPE: {"url": ZAAKTYPE, "informatieobjecttypen": [INFORMATIEOBJECT_TYPE]},
}


def dt_to_api(dt: datetime):
    formatted = dt.isoformat()
    if formatted.endswith("+00:00"):
        return formatted[:-6] + "Z"
    return formatted


@override_settings(
    LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
    ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
)
class ZaakInformatieObjectAPITests(
    ZaakInformatieObjectSyncMixin, JWTAuthMixin, APITestCase
):

    list_url = reverse(ZaakInformatieObject)

    heeft_alle_autorisaties = True

    @freeze_time("2018-09-19T12:25:19+0200")
    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_create(self, *mocks):
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE)
        status = StatusFactory(zaak=zaak)
        zaak_url = reverse("zaak-detail", kwargs={"version": "1", "uuid": zaak.uuid})
        status_url = reverse("status-detail", kwargs={"uuid": status.uuid})

        titel = "some titel"
        beschrijving = "some beschrijving"
        content = {
            "informatieobject": INFORMATIEOBJECT,
            "zaak": f"http://testserver{zaak_url}",
            "titel": titel,
            "beschrijving": beschrijving,
            "aardRelatieWeergave": "bla",  # Should be ignored by the API
            "status": f"http://testserver{status_url}",
        }

        # Send to the API
        with mock_client(RESPONSES):
            response = self.client.post(self.list_url, content)

        # Test response
        self.assertEqual(response.status_code, rest_framework_status.HTTP_201_CREATED, response.data)

        # Test database
        self.assertEqual(ZaakInformatieObject.objects.count(), 1)
        stored_object = ZaakInformatieObject.objects.get()
        self.assertEqual(stored_object.zaak, zaak)
        self.assertEqual(stored_object.aard_relatie, RelatieAarden.hoort_bij)

        expected_url = reverse(stored_object)

        expected_response = content.copy()
        expected_response.update(
            {
                "url": f"http://testserver{expected_url}",
                "uuid": str(stored_object.uuid),
                "titel": titel,
                "beschrijving": beschrijving,
                "registratiedatum": "2018-09-19T10:25:19Z",
                "aardRelatieWeergave": RelatieAarden.labels[RelatieAarden.hoort_bij],
                "vernietigingsdatum": None,
                "status": f"http://testserver{status_url}",
            }
        )
        self.assertEqual(response.json(), expected_response)

    @freeze_time("2018-09-20 12:00:00")
    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_registratiedatum_ignored(self, *mocks):
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE)
        zaak_url = reverse("zaak-detail", kwargs={"version": "1", "uuid": zaak.uuid})

        content = {
            "informatieobject": INFORMATIEOBJECT,
            "zaak": "http://testserver" + zaak_url,
            "registratiedatum": "2018-09-19T12:25:20+0200",
        }

        # Send to the API
        with mock_client(RESPONSES):
            self.client.post(self.list_url, content)

        oio = ZaakInformatieObject.objects.get()

        self.assertEqual(
            oio.registratiedatum,
            datetime(2018, 9, 20, 12, 0, 0).replace(tzinfo=timezone.utc),
        )

    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_duplicate_object(self, *mocks):
        """
        Test the (informatieobject, object) unique together validation.
        """
        zio = ZaakInformatieObjectFactory.create(
            informatieobject=INFORMATIEOBJECT, zaak__zaaktype=ZAAKTYPE
        )
        zaak_url = reverse(
            "zaak-detail", kwargs={"version": "1", "uuid": zio.zaak.uuid}
        )

        content = {
            "informatieobject": zio.informatieobject,
            "zaak": f"http://testserver{zaak_url}",
        }

        # Send to the API
        with mock_client(RESPONSES):
            response = self.client.post(self.list_url, content)

        self.assertEqual(
            response.status_code, rest_framework_status.HTTP_400_BAD_REQUEST, response.data
        )
        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["code"], "unique")

    @freeze_time("2018-09-20 12:00:00")
    def test_read_zaak(self):
        zio = ZaakInformatieObjectFactory.create(informatieobject=INFORMATIEOBJECT)
        # Retrieve from the API

        zio_detail_url = reverse(
            "zaakinformatieobject-detail", kwargs={"version": "1", "uuid": zio.uuid}
        )
        response = self.client.get(zio_detail_url)

        # Test response
        self.assertEqual(response.status_code, rest_framework_status.HTTP_200_OK)

        zaak_url = reverse(
            "zaak-detail", kwargs={"version": "1", "uuid": zio.zaak.uuid}
        )

        expected = {
            "url": f"http://testserver{zio_detail_url}",
            "uuid": str(zio.uuid),
            "informatieobject": zio.informatieobject,
            "zaak": f"http://testserver{zaak_url}",
            "aardRelatieWeergave": RelatieAarden.labels[RelatieAarden.hoort_bij],
            "titel": "",
            "beschrijving": "",
            "registratiedatum": "2018-09-20T12:00:00Z",
            "vernietigingsdatum": None,
            "status": None,
        }

        self.assertEqual(response.json(), expected)

    def test_filter(self):
        zio = ZaakInformatieObjectFactory.create(informatieobject=INFORMATIEOBJECT)
        zaak_url = reverse(
            "zaak-detail", kwargs={"version": "1", "uuid": zio.zaak.uuid}
        )
        zio_list_url = reverse("zaakinformatieobject-list", kwargs={"version": "1"})

        response = self.client.get(
            zio_list_url,
            {"zaak": f"http://testserver.com{zaak_url}"},
            HTTP_HOST="testserver.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["zaak"], f"http://testserver.com{zaak_url}")

    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_update_zaak(self, *mocks):
        zaak = ZaakFactory.create()
        zaak_url = reverse("zaak-detail", kwargs={"version": "1", "uuid": zaak.uuid})

        zio = ZaakInformatieObjectFactory.create(informatieobject=INFORMATIEOBJECT)
        zio_detail_url = reverse(
            "zaakinformatieobject-detail", kwargs={"version": "1", "uuid": zio.uuid}
        )

        response = self.client.patch(
            zio_detail_url,
            {
                "zaak": f"http://testserver{zaak_url}",
                "informatieobject": "https://bla.com",
            },
        )

        self.assertEqual(
            response.status_code, rest_framework_status.HTTP_400_BAD_REQUEST, response.data
        )

        for field in ["zaak", "informatieobject"]:
            with self.subTest(field=field):
                error = get_validation_errors(response, field)
                self.assertEqual(error["code"], IsImmutableValidator.code)

    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    def test_sync_create_fails(self):
        self.mocked_sync_create.side_effect = SyncError("Sync failed")

        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE)
        zaak_url = reverse("zaak-detail", kwargs={"version": "1", "uuid": zaak.uuid})

        content = {
            "informatieobject": INFORMATIEOBJECT,
            "zaak": f"http://testserver{zaak_url}",
        }

        # Send to the API
        with mock_client(RESPONSES):
            response = self.client.post(self.list_url, content)

        # Test response
        self.assertEqual(
            response.status_code, rest_framework_status.HTTP_400_BAD_REQUEST, response.data
        )

        # transaction must be rolled back
        self.assertFalse(ZaakInformatieObject.objects.exists())

    @freeze_time("2018-09-19T12:25:19+0200")
    def test_delete(self):
        zio = ZaakInformatieObjectFactory.create(informatieobject=INFORMATIEOBJECT)
        zio_url = reverse(
            "zaakinformatieobject-detail", kwargs={"version": "1", "uuid": zio.uuid}
        )

        self.assertEqual(self.mocked_sync_delete.call_count, 0)

        response = self.client.delete(zio_url)
        self.assertEqual(
            response.status_code, rest_framework_status.HTTP_204_NO_CONTENT, response.data
        )

        self.assertEqual(self.mocked_sync_delete.call_count, 1)

        # Relation is gone, zaak still exists.
        self.assertFalse(ZaakInformatieObject.objects.exists())
        self.assertTrue(Zaak.objects.exists())


@override_settings(
    LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
    ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
)
class ExternalDocumentsAPITransactionTests(JWTAuthMixin, APITransactionTestCase):
    heeft_alle_autorisaties = True
    base = "https://external.documenten.nl/api/v1/"
    list_url = reverse(ZaakInformatieObject)

    def setUp(self):
        applicatie, autorisatie = self._create_credentials(
            self.client_id,
            self.secret,
            heeft_alle_autorisaties=self.heeft_alle_autorisaties,
            scopes=self.scopes,
            zaaktype=self.zaaktype,
            informatieobjecttype=self.informatieobjecttype,
            besluittype=self.besluittype,
            max_vertrouwelijkheidaanduiding=self.max_vertrouwelijkheidaanduiding,
        )
        self.applicatie = applicatie
        self.autorisatie = autorisatie

        super().setUp()

    @freeze_time("2018-09-19T12:25:19+0200")
    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_create(self, *mocks):
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE)
        zaak_url = reverse("zaak-detail", kwargs={"version": "1", "uuid": zaak.uuid})

        titel = "some titel"
        beschrijving = "some beschrijving"
        content = {
            "informatieobject": INFORMATIEOBJECT,
            "zaak": f"http://testserver{zaak_url}",
            "titel": titel,
            "beschrijving": beschrijving,
            "aardRelatieWeergave": "bla",  # Should be ignored by the API
        }

        def worker(zaak_id: int):
            """
            Worker to run in a thread.
            When this worker runs, there should be one ZIO visible in the database - it
            must have been committed so that the remote DRC can view this record too.
            """
            zios = ZaakInformatieObject.objects.filter(zaak__id=zaak_id)
            self.assertEqual(zios.count(), 1)
            close_old_connections()

        def mock_create_remote_oio(*args, **kwargs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(worker, zaak.id)
                future.result()  # raises any exceptions, such as assertionerrors
            return {"url": f"http://testserver/objectinformatieobjecten/{uuid.uuid4()}"}

        with patch(
            "zrc.sync.signals.sync_create_zio",
            side_effect=mock_create_remote_oio,
        ):
            # Send to the API
            with mock_client(RESPONSES):
                response = self.client.post(self.list_url, content)

        # Test response
        self.assertEqual(response.status_code, rest_framework_status.HTTP_201_CREATED, response.data)

        # Test database
        self.assertEqual(ZaakInformatieObject.objects.count(), 1)
        stored_object = ZaakInformatieObject.objects.get()
        self.assertEqual(stored_object.zaak, zaak)
        self.assertEqual(stored_object.aard_relatie, RelatieAarden.hoort_bij)

        expected_url = reverse(stored_object)

        expected_response = content.copy()
        expected_response.update(
            {
                "url": f"http://testserver{expected_url}",
                "uuid": str(stored_object.uuid),
                "titel": titel,
                "beschrijving": beschrijving,
                "registratiedatum": "2018-09-19T10:25:19Z",
                "aardRelatieWeergave": RelatieAarden.labels[RelatieAarden.hoort_bij],
                "vernietigingsdatum": None,
                "status": None,
            }
        )
        self.assertEqual(response.json(), expected_response)

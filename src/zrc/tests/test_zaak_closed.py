import datetime
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import Archiefnominatie, ComponentTypes, RolOmschrijving
from vng_api_common.tests import JWTAuthMixin, get_operation_url, reverse
from zds_client.tests.mocks import mock_client

from zrc.api.scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN,
    SCOPE_ZAKEN_ALLES_LEZEN,
    SCOPE_ZAKEN_BIJWERKEN,
    SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN,
    SCOPEN_ZAKEN_HEROPENEN,
)
from zrc.api.tests.mixins import ZaakInformatieObjectSyncMixin
from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.models import (
    KlantContact,
    Resultaat,
    Rol,
    Status,
    ZaakEigenschap,
    ZaakInformatieObject,
    ZaakObject,
)
from zrc.datamodel.tests.factories import (
    ResultaatFactory,
    RolFactory,
    ZaakEigenschapFactory,
    ZaakFactory,
    ZaakInformatieObjectFactory,
)
from zrc.tests.utils import ZAAK_WRITE_KWARGS

ZTC_ROOT = "https://example.com/ztc/api/v1"

CATALOGUS = f"{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04"
ZAAKTYPE = f"{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f"
RESULTAATTYPE = f"{ZTC_ROOT}/resultaattypen/5b348dbf-9301-410b-be9e-83723e288785"
STATUS_TYPE = f"{ZAAKTYPE}/statustypen/1"
EIGENSCHAP = f"{ZTC_ROOT}/eigenschappen/f420c3e0-8345-44d9-a981-0f424538b9e9"
ROLTYPE = "https://ztc.nl/roltypen/123"
IO_TYPE = f"{ZTC_ROOT}informatieobjecttypen/31442352-5645-42d9-aca2-6064a94d4dfb"
EIO = (
    "https://example.com/drc/api/v1/"
    "enkelvoudiginformatieobjecten/215d8355-0ba8-40ed-9380-f2479440829c"
)

RESPONSES = {
    ZAAKTYPE: {"url": ZAAKTYPE, "informatieobjecttypen": [IO_TYPE]},
    STATUS_TYPE: {"url": STATUS_TYPE, "zaaktype": ZAAKTYPE, "isEindstatus": False},
    ROLTYPE: {
        "url": ROLTYPE,
        "zaaktype": ZAAKTYPE,
        "omschrijving": RolOmschrijving.adviseur,
        "omschrijvingGeneriek": RolOmschrijving.adviseur,
    },
    RESULTAATTYPE: {"url": RESULTAATTYPE, "zaaktype": ZAAKTYPE},
    EIGENSCHAP: {"url": EIGENSCHAP, "zaaktype": ZAAKTYPE, "naam": "foo"},
    EIO: {"url": EIO, "informatieobjecttype": IO_TYPE},
}


@override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
class ZaakClosedTests(JWTAuthMixin, APITestCase):
    scopes = [SCOPE_ZAKEN_BIJWERKEN]
    zaaktype = ZAAKTYPE

    def test_update_zaak_open(self):
        zaak = ZaakFactory.create(
            betalingsindicatie=BetalingsIndicatie.geheel, zaaktype=ZAAKTYPE
        )
        url = reverse(zaak)

        response = self.client.patch(
            url, {"betalingsindicatie": BetalingsIndicatie.nvt}, **ZAAK_WRITE_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.json()["betalingsindicatie"], BetalingsIndicatie.nvt)
        zaak.refresh_from_db()
        self.assertEqual(zaak.betalingsindicatie, BetalingsIndicatie.nvt)

    def test_update_zaak_closed_not_allowed(self):
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE, closed=True)
        url = reverse(zaak)

        response = self.client.patch(
            url, {"betalingsindicatie": BetalingsIndicatie.nvt}, **ZAAK_WRITE_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_zaak_closed_allowed(self):
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE, closed=True)
        url = reverse(zaak)

        self.autorisatie.scopes = [SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN]
        self.autorisatie.save()

        response = self.client.patch(
            url, {"betalingsindicatie": BetalingsIndicatie.nvt}, **ZAAK_WRITE_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    def test_reopen_zaak_allowed(self, *mocks):
        zaak = ZaakFactory.create(
            einddatum=timezone.now().date(),
            archiefactiedatum="2020-01-01",
            archiefnominatie=Archiefnominatie.blijvend_bewaren,
            zaaktype=ZAAKTYPE,
        )
        status_create_url = get_operation_url("status_create")
        self.autorisatie.scopes = [SCOPEN_ZAKEN_HEROPENEN]
        self.autorisatie.save()

        data = {
            "zaak": reverse(zaak),
            "statustype": STATUS_TYPE,
            "datumStatusGezet": datetime.datetime.now().isoformat(),
        }
        with mock_client(RESPONSES):
            response = self.client.post(status_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        zaak.refresh_from_db()
        self.assertIsNone(zaak.einddatum)
        self.assertIsNone(zaak.archiefactiedatum)
        self.assertIsNone(zaak.archiefnominatie)

    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    @override_settings(ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient")
    def test_reopen_zaak_not_allowed(self, *mocks):
        zaak = ZaakFactory.create(einddatum=timezone.now().date(), zaaktype=ZAAKTYPE)
        status_create_url = get_operation_url("status_create")
        self.autorisatie.scopes = [SCOPE_STATUSSEN_TOEVOEGEN]
        self.autorisatie.save()

        data = {
            "zaak": reverse(zaak),
            "statustype": STATUS_TYPE,
            "datumStatusGezet": datetime.datetime.now().isoformat(),
        }
        with mock_client(RESPONSES):
            response = self.client.post(status_create_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = response.json()
        self.assertEqual(
            data["detail"], "Reopening a closed case with current scope is forbidden"
        )


class MocksMixin(ZaakInformatieObjectSyncMixin):
    def setUp(self):
        super().setUp()

        mock_fetcher = patch("vng_api_common.validators.fetcher")
        mock_fetcher.start()
        self.addCleanup(mock_fetcher.stop)

        mock_has_shape = patch(
            "vng_api_common.validators.obj_has_shape", return_value=True
        )
        mock_has_shape.start()
        self.addCleanup(mock_has_shape.stop)

        def _fetch_obj(resource: str, url: str):
            return RESPONSES[url]

        mock_fetch_object = patch(
            "zrc.api.validators.fetch_object", side_effect=_fetch_obj
        )
        mock_fetch_object.start()
        self.addCleanup(mock_fetch_object.stop)

        mock_fetch_schema = patch(
            "zds_client.client.schema_fetcher.fetch", return_value={"paths": {},}
        )
        mock_fetch_schema.start()
        self.addCleanup(mock_fetch_schema.stop)

        m = requests_mock.Mocker()
        m.start()
        m.get("https://example.com", status_code=200)
        m.get(ROLTYPE, json=RESPONSES[ROLTYPE])
        m.get(STATUS_TYPE, json=RESPONSES[STATUS_TYPE])
        m.get(RESULTAATTYPE, json=RESPONSES[RESULTAATTYPE])
        m.get(EIGENSCHAP, json=RESPONSES[EIGENSCHAP])
        m.get(EIO, json=RESPONSES[EIO])
        m.get(ZAAKTYPE, json=RESPONSES[ZAAKTYPE])
        self.addCleanup(m.stop)


class ClosedZaakRelatedDataNotAllowedTests(MocksMixin, JWTAuthMixin, APITestCase):
    """
    Test that updating/adding related data of a Zaak is not allowed when the Zaak is
    closed.
    """

    component = ComponentTypes.zrc
    scopes = [SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_BIJWERKEN]
    zaaktype = ZAAKTYPE

    @classmethod
    def setUpTestData(cls):
        cls.zaak = ZaakFactory.create(
            zaaktype=ZAAKTYPE, closed=True, closed__status_set__statustype=STATUS_TYPE
        )
        super().setUpTestData()

    def assertCreateBlocked(self, url: str, data: dict):
        with self.subTest(action="create"):
            response = self.client.post(url, data)

            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN, response.data
            )

    def assertUpdateBlocked(self, url: str):
        with self.subTest(action="update"):
            detail = self.client.get(url).data

            response = self.client.put(url, detail)

            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN, response.data
            )

    def assertPartialUpdateBlocked(self, url: str):
        with self.subTest(action="partial_update"):
            response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def assertDestroyBlocked(self, url: str):
        with self.subTest(action="destroy"):
            response = self.client.delete(url)

            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN, response.data
            )

    def test_zaakinformatieobjecten(self):
        zio = ZaakInformatieObjectFactory(zaak=self.zaak, informatieobject=EIO,)
        zio_url = reverse(zio)

        self.assertUpdateBlocked(zio_url)
        self.assertPartialUpdateBlocked(zio_url)
        self.assertDestroyBlocked(zio_url)

        zio.delete()
        self.assertCreateBlocked(
            reverse(ZaakInformatieObject),
            {"zaak": reverse(self.zaak), "informatieobject": EIO,},
        )

    def test_zaakobjecten(self):
        self.assertCreateBlocked(
            reverse(ZaakObject),
            {
                "zaak": reverse(self.zaak),
                "object": "https://example.com",
                "objectType": "overige",
                "objectTypeOverige": "website",
            },
        )

    def test_zaakeigenschappen(self):
        self.assertCreateBlocked(
            reverse(ZaakEigenschap, kwargs={"zaak_uuid": self.zaak.uuid}),
            {"zaak": reverse(self.zaak), "eigenschap": EIGENSCHAP, "waarde": "123",},
        )

    def test_klantcontacten(self):
        url = reverse(KlantContact)
        data = {
            "zaak": reverse(self.zaak),
            "datumtijd": "2020-01-30T15:08:00Z",
        }

        self.assertCreateBlocked(url, data)

    def test_rollen(self):
        rol = RolFactory.create(zaak=self.zaak, roltype=ROLTYPE)
        rol_url = reverse(rol)

        create_url = reverse(Rol)
        data = {
            "zaak": reverse(self.zaak),
            "roltype": ROLTYPE,
            "betrokkeneType": "vestiging",
            "betrokkene": "https://example.com",
            "roltoelichting": "foo",
        }

        self.assertCreateBlocked(create_url, data)
        self.assertDestroyBlocked(rol_url)

    def test_resultaten(self):
        resultaat = ResultaatFactory.create(zaak=self.zaak, resultaattype=RESULTAATTYPE)
        resultaat_url = reverse(resultaat)

        self.assertUpdateBlocked(resultaat_url)
        self.assertPartialUpdateBlocked(resultaat_url)
        self.assertDestroyBlocked(resultaat_url)

        resultaat.delete()

        data = {
            "zaak": reverse(self.zaak),
            "resultaattype": resultaat.resultaattype,
        }
        self.assertCreateBlocked(reverse(Resultaat), data)

    def test_statussen(self):
        self.assertCreateBlocked(
            reverse(Status), {"zaak": reverse(self.zaak), "statustype": STATUS_TYPE,},
        )


class ClosedZaakRelatedDataAllowedTests(MocksMixin, JWTAuthMixin, APITestCase):
    """
    Test that updating/adding related data of a Zaak is not allowed when the Zaak is
    closed.
    """

    scopes = [SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN]
    component = ComponentTypes.zrc
    zaaktype = ZAAKTYPE

    @classmethod
    def setUpTestData(cls):
        cls.zaak = ZaakFactory.create(
            zaaktype=ZAAKTYPE, closed=True, closed__status_set__statustype=STATUS_TYPE
        )
        super().setUpTestData()

    def assertCreateAllowed(self, url: str, data: dict):
        with self.subTest(action="create"):
            response = self.client.post(url, data)

            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )

    def assertUpdateAllowed(self, url: str):
        with self.subTest(action="update"):
            detail = self.client.get(url).data

            response = self.client.put(url, detail)

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def assertPartialUpdateAllowed(self, url: str):
        with self.subTest(action="partial_update"):
            response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def assertDestroyAllowed(self, url: str):
        with self.subTest(action="destroy"):
            response = self.client.delete(url)

            self.assertEqual(
                response.status_code, status.HTTP_204_NO_CONTENT, response.data
            )

    def test_zaakinformatieobjecten(self):
        zio = ZaakInformatieObjectFactory(zaak=self.zaak, informatieobject=EIO)
        zio_url = reverse(zio)

        self.assertUpdateAllowed(zio_url)
        self.assertPartialUpdateAllowed(zio_url)
        self.assertDestroyAllowed(zio_url)

        self.assertCreateAllowed(
            reverse(ZaakInformatieObject),
            {"zaak": reverse(self.zaak), "informatieobject": EIO,},
        )

    def test_zaakobjecten(self):
        self.assertCreateAllowed(
            reverse(ZaakObject),
            {
                "zaak": reverse(self.zaak),
                "object": "https://example.com",
                "objectType": "overige",
                "objectTypeOverige": "website",
            },
        )

    def test_zaakeigenschappen(self):
        self.assertCreateAllowed(
            reverse(ZaakEigenschap, kwargs={"zaak_uuid": self.zaak.uuid}),
            {"zaak": reverse(self.zaak), "eigenschap": EIGENSCHAP, "waarde": "123",},
        )

    def test_klantcontacten(self):
        url = reverse(KlantContact)
        data = {
            "zaak": reverse(self.zaak),
            "datumtijd": "2020-01-30T15:08:00Z",
        }

        self.assertCreateAllowed(url, data)

    def test_rollen(self):
        rol = RolFactory.create(zaak=self.zaak, roltype=ROLTYPE)
        rol_url = reverse(rol)

        create_url = reverse(Rol)
        data = {
            "zaak": reverse(self.zaak),
            "roltype": ROLTYPE,
            "betrokkeneType": "vestiging",
            "betrokkene": "https://example.com",
            "roltoelichting": "foo",
        }

        self.assertCreateAllowed(create_url, data)
        self.assertDestroyAllowed(rol_url)

    def test_resultaten(self):
        resultaat = ResultaatFactory.create(zaak=self.zaak, resultaattype=RESULTAATTYPE)
        resultaat_url = reverse(resultaat)

        self.assertUpdateAllowed(resultaat_url)
        self.assertPartialUpdateAllowed(resultaat_url)
        self.assertDestroyAllowed(resultaat_url)

        resultaat.delete()

        data = {
            "zaak": reverse(self.zaak),
            "resultaattype": resultaat.resultaattype,
        }
        self.assertCreateAllowed(reverse(Resultaat), data)

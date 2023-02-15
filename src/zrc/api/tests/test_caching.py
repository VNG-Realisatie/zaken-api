"""
Test that the caching mechanisms are in place.
"""
from unittest.mock import patch

from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase, override_settings
from vng_api_common.constants import (
    Archiefnominatie,
    BrondatumArchiefprocedureAfleidingswijze,
)
from vng_api_common.tests import CacheMixin, JWTAuthMixin, get_operation_url, reverse
from vng_api_common.tests.schema import get_spec
from zds_client.tests.mocks import mock_client

from zrc.datamodel.tests.factories import (
    ResultaatFactory,
    RolFactory,
    StatusFactory,
    ZaakEigenschapFactory,
    ZaakFactory,
    ZaakInformatieObjectFactory,
)
from zrc.tests.utils import ZAAK_READ_KWARGS

from .mixins import ZaakInformatieObjectSyncMixin

ZTC_ROOT = "https://example.com/ztc/api/v1"
CATALOGUS = f"{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04"
ZAAKTYPE = f"{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f"
STATUSTYPE = f"{ZAAKTYPE}/statustypen/5b348dbf-9301-410b-be9e-83723e288785"
RESULTAATTYPE = f"{ZAAKTYPE}/resultaattypen/5b348dbf-9301-410b-be9e-83723e288785"

EIND_STATUSTYPE_RESPONSE = {
    "url": STATUSTYPE,
    "zaaktype": ZAAKTYPE,
    "volgnummer": 2,
    "isEindstatus": True,
}


class ZaakCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_zaak_get_cache_header(self):
        zaak = ZaakFactory.create()

        response = self.client.get(reverse(zaak), **ZAAK_READ_KWARGS)

        self.assertHasETag(response)

    def test_zaak_head_cache_header(self):
        zaak = ZaakFactory.create()

        self.assertHeadHasETag(reverse(zaak), **ZAAK_READ_KWARGS)

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/zaken/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        zaak = ZaakFactory.create(with_etag=True)

        response = self.client.get(
            reverse(zaak), HTTP_IF_NONE_MATCH=f'"{zaak._etag}"', **ZAAK_READ_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        zaak = ZaakFactory.create(with_etag=True)

        response = self.client.get(
            reverse(zaak), HTTP_IF_NONE_MATCH=f'"not-an-md5"', **ZAAK_READ_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ZaakCacheTransactionTests(JWTAuthMixin, APITransactionTestCase):
    heeft_alle_autorisaties = True

    def setUp(self):
        super().setUp()

        self._create_credentials(
            self.client_id,
            self.secret,
            self.heeft_alle_autorisaties,
            self.max_vertrouwelijkheidaanduiding,
        )

    @override_settings(
        LINK_FETCHER="vng_api_common.mocks.link_fetcher_200",
        ZDS_CLIENT_CLASS="vng_api_common.mocks.MockClient",
    )
    @patch("vng_api_common.validators.fetcher")
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_invalidate_new_status(self, *mocks):
        """
        Status URL is part of the resource, so new status invalidates the ETag.
        """
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE, with_etag=True)
        zaak_url = get_operation_url("zaak_retrieve", uuid=zaak.uuid)

        ResultaatFactory(zaak=zaak, resultaattype=RESULTAATTYPE)

        responses = {
            RESULTAATTYPE: {
                "url": RESULTAATTYPE,
                "zaaktype": ZAAKTYPE,
                "archiefactietermijn": "P10Y",
                "archiefnominatie": Archiefnominatie.blijvend_bewaren,
                "brondatumArchiefprocedure": {
                    "afleidingswijze": BrondatumArchiefprocedureAfleidingswijze.afgehandeld,
                    "datumkenmerk": None,
                    "objecttype": None,
                    "procestermijn": None,
                },
            },
            STATUSTYPE: EIND_STATUSTYPE_RESPONSE,
        }

        status_create_url = get_operation_url("status_create")
        data = {
            "zaak": zaak_url,
            "statustype": STATUSTYPE,
            "datumStatusGezet": "2018-10-18T20:00:00Z",
        }

        with mock_client(responses):
            resp = self.client.post(status_create_url, data)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        response = self.client.get(
            reverse(zaak), HTTP_IF_NONE_MATCH=f'"{zaak._etag}"', **ZAAK_READ_KWARGS
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StatusCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_status_get_cache_header(self):
        status_ = StatusFactory.create()

        response = self.client.get(reverse(status_))

        self.assertHasETag(response)

    def test_status_head_cache_header(self):
        status_ = StatusFactory.create()

        self.assertHeadHasETag(reverse(status_))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/statussen/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        """
        Test that, if I have a cached copy, the API returns an HTTP 304.
        """
        status_ = StatusFactory.create(with_etag=True)

        response = self.client.get(
            reverse(status_), HTTP_IF_NONE_MATCH=f'"{status_._etag}"'
        )

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        status_ = StatusFactory.create(with_etag=True)

        response = self.client.get(reverse(status_), HTTP_IF_NONE_MATCH='"not-an-md5"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ZaakInformatieObjectCacheTests(
    CacheMixin, ZaakInformatieObjectSyncMixin, JWTAuthMixin, APITestCase
):
    heeft_alle_autorisaties = True

    def test_zaakinformatieobject_get_cache_header(self):
        zaakinformatieobject = ZaakInformatieObjectFactory.create()

        response = self.client.get(reverse(zaakinformatieobject))

        self.assertHasETag(response)

    def test_zaakinformatieobject_head_cache_header(self):
        zaakinformatieobject = ZaakInformatieObjectFactory.create()

        self.assertHeadHasETag(reverse(zaakinformatieobject))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/zaakinformatieobjecten/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        zio = ZaakInformatieObjectFactory.create(with_etag=True)

        response = self.client.get(reverse(zio), HTTP_IF_NONE_MATCH=f'"{zio._etag}"')

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        zio = ZaakInformatieObjectFactory.create(with_etag=True)

        response = self.client.get(reverse(zio), HTTP_IF_NONE_MATCH='"old"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ZaakEigenschapCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_zaakeigenschap_get_cache_header(self):
        zaakeigenschap = ZaakEigenschapFactory.create()

        response = self.client.get(
            reverse(zaakeigenschap, kwargs={"zaak_uuid": zaakeigenschap.zaak.uuid})
        )

        self.assertHasETag(response)

    def test_zaakeigenschap_head_cache_header(self):
        zaakeigenschap = ZaakEigenschapFactory.create()

        self.assertHeadHasETag(
            reverse(zaakeigenschap, kwargs={"zaak_uuid": zaakeigenschap.zaak.uuid})
        )

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/zaken/{{zaak_uuid}}/zaakeigenschappen/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        zaak_eigenschap = ZaakEigenschapFactory.create(with_etag=True)

        response = self.client.get(
            reverse(zaak_eigenschap, kwargs={"zaak_uuid": zaak_eigenschap.zaak.uuid}),
            HTTP_IF_NONE_MATCH=f'"{zaak_eigenschap._etag}"',
        )

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        zaak_eigenschap = ZaakEigenschapFactory.create(with_etag=True)

        response = self.client.get(
            reverse(zaak_eigenschap, kwargs={"zaak_uuid": zaak_eigenschap.zaak.uuid}),
            HTTP_IF_NONE_MATCH='"old"',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RolCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_rol_get_cache_header(self):
        rol = RolFactory.create()

        response = self.client.get(reverse(rol))

        self.assertHasETag(response)

    def test_rol_head_cache_header(self):
        rol = RolFactory.create()

        self.assertHeadHasETag(reverse(rol))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/rollen/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        rol = RolFactory.create(with_etag=True)

        response = self.client.get(reverse(rol), HTTP_IF_NONE_MATCH=f'"{rol._etag}"')

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        rol = RolFactory.create(with_etag=True)

        response = self.client.get(reverse(rol), HTTP_IF_NONE_MATCH='"old"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ResultaatCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_resultaat_get_cache_header(self):
        resultaat = ResultaatFactory.create()

        response = self.client.get(reverse(resultaat))

        self.assertHasETag(response)

    def test_resultaat_head_cache_header(self):
        resultaat = ResultaatFactory.create()

        self.assertHeadHasETag(reverse(resultaat))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"][f"/resultaten/{{uuid}}"]

        self.assertIn("head", endpoint)

    def test_conditional_get_304(self):
        resultaat = ResultaatFactory.create(with_etag=True)

        response = self.client.get(
            reverse(resultaat), HTTP_IF_NONE_MATCH=f'"{resultaat._etag}"'
        )

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_conditional_get_stale(self):
        resultaat = ResultaatFactory.create(with_etag=True)

        response = self.client.get(reverse(resultaat), HTTP_IF_NONE_MATCH='"old"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

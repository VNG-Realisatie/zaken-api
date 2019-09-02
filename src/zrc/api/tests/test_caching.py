"""
Test that the caching mechanisms are in place.
"""
from rest_framework.test import APITestCase
from vng_api_common.tests import CacheMixin, JWTAuthMixin, reverse
from vng_api_common.tests.schema import get_spec

from zrc.datamodel.tests.factories import (
    ResultaatFactory, RolFactory, StatusFactory, ZaakEigenschapFactory,
    ZaakFactory, ZaakInformatieObjectFactory
)
from zrc.tests.utils import ZAAK_READ_KWARGS

from .mixins import ZaakInformatieObjectSyncMixin


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

        endpoint = spec["paths"]["/zaken/{uuid}"]

        self.assertIn("head", endpoint)


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

        endpoint = spec["paths"]["/statussen/{uuid}"]

        self.assertIn("head", endpoint)


class ZaakInformatieObjectCacheTests(
        CacheMixin,
        ZaakInformatieObjectSyncMixin,
        JWTAuthMixin,
        APITestCase):
    heeft_alle_autorisaties = True

    def test_ZaakInformatieObject_get_cache_header(self):
        zaakinformatieobject = ZaakInformatieObjectFactory.create()

        response = self.client.get(reverse(zaakinformatieobject))

        self.assertHasETag(response)

    def test_ZaakInformatieObject_head_cache_header(self):
        zaakinformatieobject = ZaakInformatieObjectFactory.create()

        self.assertHeadHasETag(reverse(zaakinformatieobject))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"]["/zaakinformatieobjecten/{uuid}"]

        self.assertIn("head", endpoint)


class ZaakEigenschapCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_ZaakEigenschap_get_cache_header(self):
        zaakeigenschap = ZaakEigenschapFactory.create()

        response = self.client.get(
            reverse(zaakeigenschap, kwargs={"zaak_uuid": zaakeigenschap.zaak.uuid})
        )

        self.assertHasETag(response)

    def test_ZaakEigenschap_head_cache_header(self):
        zaakeigenschap = ZaakEigenschapFactory.create()

        self.assertHeadHasETag(
            reverse(zaakeigenschap, kwargs={"zaak_uuid": zaakeigenschap.zaak.uuid})
        )

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"]["/zaken/{zaak_uuid}/zaakeigenschappen/{uuid}"]

        self.assertIn("head", endpoint)


class RolCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_Rol_get_cache_header(self):
        rol = RolFactory.create()

        response = self.client.get(reverse(rol))

        self.assertHasETag(response)

    def test_Rol_head_cache_header(self):
        rol = RolFactory.create()

        self.assertHeadHasETag(reverse(rol))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"]["/rollen/{uuid}"]

        self.assertIn("head", endpoint)


class ResultaatCacheTests(CacheMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_Resultaat_get_cache_header(self):
        resultaat = ResultaatFactory.create()

        response = self.client.get(reverse(resultaat))

        self.assertHasETag(response)

    def test_Resultaat_head_cache_header(self):
        resultaat = ResultaatFactory.create()

        self.assertHeadHasETag(reverse(resultaat))

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"]["/resultaten/{uuid}"]

        self.assertIn("head", endpoint)

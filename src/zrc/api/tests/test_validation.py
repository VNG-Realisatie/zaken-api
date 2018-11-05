from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_validation_errors
from zds_schema.validators import URLValidator

from zrc.datamodel.tests.factories import ZaakFactory
from zrc.tests.utils import generate_jwt

from ..scopes import SCOPE_ZAKEN_CREATE
from .utils import reverse


class ZaakValidationTests(APITestCase):

    def setUp(self):
        super().setUp()

        self.client.credentials(HTTP_AUTHORIZATION=generate_jwt([SCOPE_ZAKEN_CREATE]))

    @override_settings(LINK_FETCHER='zds_schema.mocks.link_fetcher_404')
    def test_validate_zaaktype_invalid(self):
        url = reverse('zaak-list')

        response = self.client.post(url, {
            'zaaktype': 'https://example.com/foo/bar',
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': 'https://example.com/foo/bar',
            'registratiedatum': '2018-06-11',
            'startdatum': '2018-06-11',
        }, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        validation_error = get_validation_errors(response, 'zaaktype')
        self.assertEqual(validation_error['code'], URLValidator.code)
        self.assertEqual(validation_error['name'], 'zaaktype')

    @override_settings(LINK_FETCHER='zds_schema.mocks.link_fetcher_200')
    def test_validate_zaaktype_valid(self):
        url = reverse('zaak-list')

        response = self.client.post(url, {
            'zaaktype': 'https://example.com/foo/bar',
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': 'https://example.com/foo/bar',
            'registratiedatum': '2018-06-11',
            'startdatum': '2018-06-11',
        }, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_validation_camelcase(self):
        url = reverse('zaak-list')

        response = self.client.post(url, {}, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        bad_casing = get_validation_errors(response, 'verantwoordelijke_organisatie')
        self.assertIsNone(bad_casing)

        good_casing = get_validation_errors(response, 'verantwoordelijkeOrganisatie')
        self.assertIsNotNone(good_casing)


class ZaakInformatieObjectValidationTests(APITestCase):

    def setUp(self):
        super().setUp()

        self.client.credentials(HTTP_AUTHORIZATION=generate_jwt([SCOPE_ZAKEN_CREATE]))

    @override_settings(
        LINK_FETCHER='zds_schema.mocks.link_fetcher_404',
        ZDS_CLIENT_CLASS='zds_schema.mocks.ObjectInformatieObjectClient'
    )
    def test_informatieobject_invalid(self):
        zaak = ZaakFactory.create()
        url = reverse('zaakinformatieobject-list', kwargs={'zaak_uuid': zaak.uuid})

        response = self.client.post(url, {'informatieobject': 'https://drc.nl/api/v1'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        validation_error = get_validation_errors(response, 'informatieobject')
        self.assertEqual(validation_error['code'], URLValidator.code)
        self.assertEqual(validation_error['name'], 'informatieobject')

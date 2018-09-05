from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.validators import URLValidator

from .utils import reverse


class ZaakValidationTests(APITestCase):

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

        validation_error = response.data['invalid-params'][0]
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

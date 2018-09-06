import unittest

from django.contrib.gis.geos import Point
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from zrc.datamodel.tests.factories import ZaakFactory

from .utils import reverse


@override_settings(LINK_FETCHER='zds_schema.mocks.link_fetcher_200')
class ApiStrategyTests(APITestCase):

    @unittest.expectedFailure
    def test_api_10_lazy_eager_loading(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_11_expand_nested_resources(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_12_subset_fields(self):
        raise NotImplementedError

    def test_api_44_crs_headers(self):
        # We wijken bewust af - EPSG:4326 is de standaard projectie voor WGS84
        # De andere opties in de API strategie lijken in de praktijk niet/nauwelijks
        # gebruikt te worden, en zien er vreemd uit t.o.v. wel courant gebruikte
        # opties.
        zaak = ZaakFactory.create(zaakgeometrie=Point(4.887990, 52.377595))  # LONG LAT
        url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

        response = self.client.get(url, HTTP_ACCEPT_CRS='dummy')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

        response = self.client.get(url, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(
            response['Content-Crs'],
            'EPSG:4326'
        )

    def test_api_51_status_codes(self):
        with self.subTest(crud='create'):
            url = reverse('zaak-list')

            response = self.client.post(url, {
                'zaaktype': 'https://example.com/foo/bar',
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': 'https://example.com/foo/bar',
                'registratiedatum': '2018-06-11',
                'startdatum': '2018-06-11',
            }, HTTP_ACCEPT_CRS='EPSG:4326')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response['Location'], response.data['url'])

        with self.subTest(crud='read'):
            response_detail = self.client.get(response.data['url'], HTTP_ACCEPT_CRS='EPSG:4326')
            self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

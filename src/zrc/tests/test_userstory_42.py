"""
Als burger wil ik alle meldingen kunnen inzien in mijn omgeving, binnen mijn
gemeente zodat ik weet wat er speelt of dat een melding al gedaan is.

ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/42
"""
from django.contrib.gis.geos import Point

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import JWTScopesMixin, TypeCheckMixin, get_operation_url

from zrc.api.scopes import SCOPE_ZAKEN_ALLES_LEZEN
from zrc.datamodel.tests.factories import ZaakFactory

from .constants import POLYGON_AMSTERDAM_CENTRUM


class US42TestCase(JWTScopesMixin, TypeCheckMixin, APITestCase):

    scopes = [
        SCOPE_ZAKEN_ALLES_LEZEN,
    ]

    def test_anoniem_binnen_ams_centrum_district(self):
        """
        Test dat zaken binnen een bepaald gebied kunnen opgevraagd worden.
        """
        # in district
        zaak = ZaakFactory.create(zaakgeometrie=Point(4.887990, 52.377595))  # LONG LAT
        # outside of district
        ZaakFactory.create(zaakgeometrie=Point(4.905650, 52.357621))
        # no geo set
        ZaakFactory.create()

        url = get_operation_url('zaak__zoek')

        response = self.client.post(url, {
            'zaakgeometrie': {
                'within': {
                    'type': 'Polygon',
                    'coordinates': [POLYGON_AMSTERDAM_CENTRUM]
                }
            }
        }, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        detail_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        self.assertEqual(response_data[0]['url'], f"http://testserver{detail_url}")

    def test_filter_ook_zaaktype(self):

        # both in district
        ZaakFactory.create(
            zaakgeometrie=Point(4.887990, 52.377595),
            zaaktype='https://example.com/api/v1/zaaktype/1'
        )
        ZaakFactory.create(
            zaakgeometrie=Point(4.887990, 52.377595),
            zaaktype='https://example.com/api/v1/zaaktype/2'
        )

        url = get_operation_url('zaak__zoek')

        response = self.client.post(url, {
            'zaakgeometrie': {
                'within': {
                    'type': 'Polygon',
                    'coordinates': [POLYGON_AMSTERDAM_CENTRUM]
                }
            },
            'zaaktype': 'https://example.com/api/v1/zaaktype/1'
        }, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)

"""
Als gemeente wil ik dat de aanvraag tbh een straatoptreden als zaak wordt
gecreëerd zodat mijn dossiervorming op orde is en de voortgang transparant is.

Ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/163

Zie ook: test_userstory_39.py, test_userstory_169.py
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

# aanvraag aangemaakt in extern systeem, leeft buiten ZRC
AANVRAAG = 'https://example.com/orc/api/v1/straatartiesten/37c60cda-689e-4e4a-969c-fa4ed56cb2c6'
CATALOGUS = 'https://example.com/ztc/api/v1/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'


class US169TestCase(APITestCase):

    def test_create_aanvraag(self):
        """
        Maak een zaak voor een aanvraag.
        """
        zaak_create_url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'identificatie': 'HLM-straatartiest-42',
            'omschrijving': 'Dagontheffing - Station Haarlem',
            'toelichting': 'Het betreft een clown met grote trom, mondharmonica en cymbalen.',
            'startdatum': '2018-08-15',
        }

        # aanmaken zaak
        response = self.client.post(zaak_create_url, data, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        data = response.json()
        self.assertIn('identificatie', data)
        self.assertEqual(data['registratiedatum'], date.today().strftime('%Y-%m-%d'))
        self.assertEqual(data['startdatum'], '2018-08-15')

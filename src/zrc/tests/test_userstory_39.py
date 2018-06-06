"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import get_operation_url


class US39TestCase(APITestCase):

    def test_create_zaak(self):
        """
        Maak een zaak van een bepaald type.
        """
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': 'https://example.com/api/v1/catalogus/1/zaaktypen/1/',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('zaakidentificatie', data)

        # verify that the identification has been generated
        self.assertIsInstance(data['zaakidentificatie'], str)
        self.assertNotEqual(data['zaakidentificatie'], '')

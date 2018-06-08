"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from rest_framework import status
from rest_framework.test import APITestCase

from zrc.datamodel.models import Status, Zaak
from zrc.datamodel.tests.factories import ZaakFactory

from .utils import get_operation_url, isodatetime

ZAAKTYPE = 'https://example.com/api/v1/catalogus/1/zaaktypen/1/'
STATUS_TYPE = 'https://example.com/api/v1/catalogus/1/zaaktypen/1/statustypen/1/'


class US39TestCase(APITestCase):

    def test_create_zaak(self):
        """
        Maak een zaak van een bepaald type.
        """
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('zaakidentificatie', data)

        # verify that the identification has been generated
        self.assertIsInstance(data['zaakidentificatie'], str)
        self.assertNotEqual(data['zaakidentificatie'], '')

        zaak = Zaak.objects.get()
        self.assertEqual(zaak.zaaktype, ZAAKTYPE)

    def test_zet_zaakstatus(self):
        """
        De actuele status van een zaak moet gezet worden bij het aanmaken
        van de zaak.
        """
        url = get_operation_url('status_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'statusType': STATUS_TYPE,
            'datumStatusGezet': isodatetime(2018, 6, 6, 17, 23, 43),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        status_ = Status.objects.get()
        self.assertEqual(status_.zaak, zaak)
        detail_url = get_operation_url('status_read', id=status_.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'statusType': STATUS_TYPE,
                'datumStatusGezet': '2018-06-06T17:23:43Z',  # UTC
                'statustoelichting': '',
            }
        )

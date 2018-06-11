"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

from zrc.datamodel.models import DomeinData, Status, Zaak, ZaakObject
from zrc.datamodel.tests.factories import ZaakFactory

from .utils import isodatetime

ZAAKTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/'
STATUS_TYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/1/'
OBJECT_MET_ADRES = 'https://example.com/orc/api/v1/objecten/1/'
DOMEIN_DATA = 'https://example.com/domeindata/api/v1/data/1/'

TEST_DATA = {
    "id": 9966,
    "last_status": "o",
    "adres": "Oosterdok 51, 1011 Amsterdam, Netherlands",
    "datetime": "2018-05-28T09:05:08.732587+02:00",
    "text": "test",
    "waternet_soort_boot": "Nee",
    "waternet_rederij": "Onbekend",
    "waternet_naam_boot": "",
    "datetime_overlast": None,
    "email": "",
    "phone_number": "",
    "source": "Telefoon 14020",
    "text_extra": "",
    "image": None,
    "main_category": "",
    "sub_category": "Geluid",
    "ml_cat": "melding openbare ruimte",
    "stadsdeel": "Centrum",
    "coordinates": "POINT (4.910649523925713 52.37240093589432)",
    "verantwoordelijk": "Waternet"
}


class US39TestCase(APITestCase):

    def test_create_zaak(self):
        """
        Maak een zaak van een bepaald type.
        """
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'registratiedatum': '2018-06-11',
            'toelichting': 'Een stel dronken toeristen speelt versterkte '
                           'muziek af vanuit een gehuurde boot.',
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
        self.assertEqual(zaak.registratiedatum, date(2018, 6, 11))
        self.assertEqual(
            zaak.toelichting,
            'Een stel dronken toeristen speelt versterkte '
            'muziek af vanuit een gehuurde boot.'
        )

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

    def test_zet_adres_binnenland(self):
        """
        Het adres van de melding moet in de zaak beschikbaar zijn.
        """
        url = get_operation_url('zaakobject_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'object': OBJECT_MET_ADRES,
            'relatieomschrijving': 'Het adres waar de overlast vastgesteld werd.',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        zaakobject = ZaakObject.objects.get()
        self.assertEqual(zaakobject.zaak, zaak)
        detail_url = get_operation_url('zaakobject_read', id=zaakobject.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'object': OBJECT_MET_ADRES,
                'relatieomschrijving': 'Het adres waar de overlast vastgesteld werd.',
            }
        )

    def test_zet_domeindata(self):
        url = get_operation_url('domeindata_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'domeinData': DOMEIN_DATA,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        domeindata = DomeinData.objects.get()
        self.assertEqual(domeindata.zaak, zaak)
        detail_url = get_operation_url('domeindata_read', id=domeindata.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'domeinData': DOMEIN_DATA,
            }
        )

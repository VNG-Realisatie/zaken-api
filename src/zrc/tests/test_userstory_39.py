"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from datetime import date

from dateutil import parser
from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

from zrc.datamodel.models import (
    DomeinData, KlantContact, Status, Zaak, ZaakInformatieObject, ZaakObject
)
from zrc.datamodel.tests.factories import ZaakFactory

from .utils import isodatetime, utcdatetime

ZAAKTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/'
STATUS_TYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/1/'
STATUS_TYPE_OVERLAST_GECONSTATEERD = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/2/'
OBJECT_MET_ADRES = 'https://example.com/orc/api/v1/objecten/1/'
DOMEIN_DATA = 'https://example.com/domeindata/api/v1/data/1/'
FOTO = 'https://example.com/drc/api/v1/enkelvoudiginformatieobjecten/1/'

TEST_DATA = {
    "id": 9966,
    "last_status": "o",
    "adres": "Oosterdok 51, 1011 Amsterdam, Netherlands",
    "datetime": "2018-05-28T09:05:08.732587+02:00",
    "text": "test",
    "waternet_soort_boot": "Nee",
    "waternet_rederij": "Onbekend",
    "waternet_naam_boot": "",
    "datetime_overlast": "2018-05-28T08:35:11+02:00",
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

    def test_create_klantcontact(self):
        url = get_operation_url('klantcontact_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'datumtijd': isodatetime(2018, 6, 11, 13, 47, 55),
            'kanaal': 'Webformulier',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        klantcontact = KlantContact.objects.get()
        self.assertIsInstance(klantcontact.identificatie, str)
        self.assertNotEqual(klantcontact.identificatie, '')
        self.assertEqual(klantcontact.zaak, zaak)
        detail_url = get_operation_url('klantcontact_read', id=klantcontact.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'identificatie': klantcontact.identificatie,
                'datumtijd': '2018-06-11T13:47:55Z',
                'kanaal': 'Webformulier',
            }
        )

    def test_create_zaakinformatieobject(self):
        url = get_operation_url('zaakinformatieobject_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'informatieobject': FOTO,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        zio = ZaakInformatieObject.objects.get()
        self.assertEqual(zio.zaak, zaak)
        detail_url = get_operation_url('zaakinformatieobject_read', id=zio.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'informatieobject': FOTO,
            }
        )


class Application:

    def __init__(self, client, data: dict):
        self.client = client

        self.data = data
        self.references = {}

    def store_notification(self):
        # registreer zaak & zet statussen
        self.registreer_zaak()
        self.zet_statussen()
        self.registreer_domein_data()
        self.registreer_klantcontact()
        self.registreer_foto()

    @property
    def domein_data_url(self):
        return self.references['domein_data_url']

    def registreer_zaak(self):
        zaak_create_url = get_operation_url('zaak_create')

        created = parser.parse(self.data['datetime'])
        intern_id = self.data['id']

        response = self.client.post(zaak_create_url, {
            'zaaktype': ZAAKTYPE,
            'zaakidentificatie': f'AMS{intern_id}',
            'registratiedatum': created.strftime('%Y-%m-%d'),
            'toelichting': self.data['text'],
        })
        self.references['zaak_url'] = response.json()['url']

    def zet_statussen(self):
        status_create_url = get_operation_url('status_create')

        created = parser.parse(self.data['datetime'])

        self.client.post(status_create_url, {
            'zaak': self.references['zaak_url'],
            'statusType': STATUS_TYPE,
            'datumStatusGezet': created.isoformat(),
        })

        self.client.post(status_create_url, {
            'zaak': self.references['zaak_url'],
            'statusType': STATUS_TYPE_OVERLAST_GECONSTATEERD,
            'datumStatusGezet': parser.parse(self.data['datetime_overlast']).isoformat(),
        })

    def registreer_domein_data(self):
        url = get_operation_url('domeindata_create')
        response = self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'domeinData': DOMEIN_DATA,
        })
        self.references['domein_data_url'] = response.json()['url']

    def registreer_klantcontact(self):
        url = get_operation_url('klantcontact_create')
        self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'datumtijd': self.data['datetime'],
            'kanaal': self.data['source'],
        })

    def registreer_foto(self):
        if not self.data['image']:
            return

        url = get_operation_url('zaakinformatieobject_create')
        self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'informatieobject': self.data['image'],
        })


class US39IntegrationTestCase(APITestCase):
    """
    Simulate a full realistic flow.
    """

    def test_full_flow(self):
        app = Application(self.client, TEST_DATA)

        app.store_notification()

        zaak = Zaak.objects.get(zaakidentificatie='AMS9966')
        self.assertEqual(zaak.toelichting, 'test')

        self.assertEqual(zaak.status_set.count(), 2)

        last_status = zaak.status_set.order_by('-datum_status_gezet').first()
        self.assertEqual(last_status.status_type, STATUS_TYPE)
        self.assertEqual(
            last_status.datum_status_gezet,
            utcdatetime(2018, 5, 28, 7, 5, 8, 732587),
        )

        first_status = zaak.status_set.order_by('datum_status_gezet').first()
        self.assertEqual(first_status.status_type, STATUS_TYPE_OVERLAST_GECONSTATEERD)
        self.assertEqual(
            first_status.datum_status_gezet,
            utcdatetime(2018, 5, 28, 6, 35, 11)
        )

        domein_data = self.client.get(app.domein_data_url).json()['domeinData']
        self.assertEqual(domein_data, DOMEIN_DATA)

        klantcontact = zaak.klantcontact_set.get()
        self.assertEqual(klantcontact.kanaal, 'Telefoon 14020')
        self.assertEqual(
            klantcontact.datumtijd,
            utcdatetime(2018, 5, 28, 7, 5, 8, 732587),
        )

        self.assertFalse(zaak.zaakinformatieobject_set.exists())

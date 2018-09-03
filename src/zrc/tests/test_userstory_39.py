"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from datetime import date

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url, get_validation_errors

from zrc.datamodel.models import KlantContact, Rol, Status, Zaak, ZaakObject
from zrc.datamodel.tests.factories import ZaakFactory

from .utils import isodatetime

ZAAKTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1'
STATUS_TYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/1'
STATUS_TYPE_OVERLAST_GECONSTATEERD = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/2'
VERANTWOORDELIJKE_ORGANISATIE = 'https://www.example.com/orc/api/v1/rsgb/nietnatuurlijkepersonen/1234'
OBJECT_MET_ADRES = 'https://example.com/orc/api/v1/objecten/1'
FOTO = 'https://example.com/drc/api/v1/enkelvoudiginformatieobjecten/1'
# file:///home/bbt/Downloads/2a.aansluitspecificatieskennisgevingen-gegevenswoordenboek-entiteitenv1.0.6.pdf
# Stadsdeel is een WijkObject in het RSGB
STADSDEEL = 'https://example.com/rsgb/api/v1/wijkobjecten/1'


@override_settings(LINK_FETCHER='zrc.api.tests.mocks.link_fetcher_200')
class US39TestCase(APITestCase):

    def test_create_zaak(self):
        """
        Maak een zaak van een bepaald type.
        """
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': VERANTWOORDELIJKE_ORGANISATIE,
            'registratiedatum': '2018-06-11',
            'startdatum': '2018-06-11',
            'toelichting': 'Een stel dronken toeristen speelt versterkte '
                           'muziek af vanuit een gehuurde boot.',
            'zaakgeometrie': {
                'type': 'Point',
                'coordinates': [
                    4.910649523925713,
                    52.37240093589432
                ]
            }
        }

        response = self.client.post(url, data, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        data = response.json()
        self.assertIn('identificatie', data)

        # verify that the identification has been generated
        self.assertIsInstance(data['identificatie'], str)
        self.assertNotEqual(data['identificatie'], '')
        self.assertIsInstance(data['zaakgeometrie'], dict)  # geojson object

        zaak = Zaak.objects.get()
        self.assertEqual(zaak.zaaktype, ZAAKTYPE)
        self.assertEqual(zaak.registratiedatum, date(2018, 6, 11))
        self.assertEqual(
            zaak.toelichting,
            'Een stel dronken toeristen speelt versterkte '
            'muziek af vanuit een gehuurde boot.'
        )
        self.assertEqual(zaak.zaakgeometrie.x, 4.910649523925713)
        self.assertEqual(zaak.zaakgeometrie.y, 52.37240093589432)

    def test_create_zaak_zonder_bronorganisatie(self):
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'registratiedatum': '2018-06-11',
        }

        response = self.client.post(url, data, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = get_validation_errors(response, 'bronorganisatie')
        self.assertEqual(error['code'], 'required')

    def test_create_zaak_invalide_rsin(self):
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '123456789',
            'registratiedatum': '2018-06-11',
        }

        response = self.client.post(url, data, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = get_validation_errors(response, 'bronorganisatie')
        self.assertEqual(error['code'], 'invalid')

    def test_zet_zaakstatus(self):
        """
        De actuele status van een zaak moet gezet worden bij het aanmaken
        van de zaak.
        """
        url = get_operation_url('status_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        data = {
            'zaak': zaak_url,
            'statusType': STATUS_TYPE,
            'datumStatusGezet': isodatetime(2018, 6, 6, 17, 23, 43),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        status_ = Status.objects.get()
        self.assertEqual(status_.zaak, zaak)
        detail_url = get_operation_url('status_read', uuid=status_.uuid)
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
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        data = {
            'zaak': zaak_url,
            'object': OBJECT_MET_ADRES,
            'type': 'VerblijfsObject',
            'relatieomschrijving': 'Het adres waar de overlast vastgesteld werd.',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        zaakobject = ZaakObject.objects.get()
        self.assertEqual(zaakobject.zaak, zaak)
        detail_url = get_operation_url('zaakobject_read', uuid=zaakobject.uuid)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'object': OBJECT_MET_ADRES,
                'type': 'VerblijfsObject',
                'relatieomschrijving': 'Het adres waar de overlast vastgesteld werd.',
            }
        )

    def test_create_klantcontact(self):
        url = get_operation_url('klantcontact_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
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
        detail_url = get_operation_url('klantcontact_read', uuid=klantcontact.uuid)
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

    def test_zet_stadsdeel(self):
        url = get_operation_url('zaakobject_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        data = {
            'zaak': zaak_url,
            'object': STADSDEEL,
            'type': 'VerblijfsObject',
            'relatieomschrijving': 'Afgeleid gebied',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        zaakobject = ZaakObject.objects.get()
        self.assertEqual(zaakobject.zaak, zaak)
        detail_url = get_operation_url('zaakobject_read', uuid=zaakobject.uuid)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'object': STADSDEEL,
                'type': 'VerblijfsObject',
                'relatieomschrijving': 'Afgeleid gebied',
            }
        )

    def test_zet_verantwoordelijk(self):
        url = get_operation_url('rol_create')
        betrokkene = 'https://example.com/orc/api/v1/vestigingen/waternet'
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        data = {
            'zaak': zaak_url,
            'betrokkene': betrokkene,
            'betrokkeneType': 'Vestiging',
            'rolomschrijving': 'Behandelaar',
            'roltoelichting': 'Baggeren van gracht',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response_data = response.json()
        rol = Rol.objects.get()
        self.assertEqual(rol.zaak, zaak)
        self.assertEqual(rol.betrokkene, betrokkene)
        detail_url = get_operation_url('rol_read', uuid=rol.uuid)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'betrokkene': betrokkene,
                'betrokkeneType': 'Vestiging',
                'rolomschrijving': 'Behandelaar',
                'roltoelichting': 'Baggeren van gracht',
            }
        )

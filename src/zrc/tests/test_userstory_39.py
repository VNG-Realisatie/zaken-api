"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

from zrc.datamodel.models import KlantContact, Rol, Status, Zaak, ZaakObject
from zrc.datamodel.tests.factories import (
    OrganisatorischeEenheidFactory, ZaakFactory
)

from .utils import isodatetime

ZAAKTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1'
STATUS_TYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/1'
STATUS_TYPE_OVERLAST_GECONSTATEERD = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/statustypen/2'
OBJECT_MET_ADRES = 'https://example.com/orc/api/v1/objecten/1'
FOTO = 'https://example.com/drc/api/v1/enkelvoudiginformatieobjecten/1'
# file:///home/bbt/Downloads/2a.aansluitspecificatieskennisgevingen-gegevenswoordenboek-entiteitenv1.0.6.pdf
# Stadsdeel is een WijkObject in het RSGB
STADSDEEL = 'https://example.com/rsgb/api/v1/wijkobjecten/1'


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
            'zaakgeometrie': {
                'type': 'Point',
                'coordinates': [
                    4.910649523925713,
                    52.37240093589432
                ]
            }
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('zaakidentificatie', data)

        # verify that the identification has been generated
        self.assertIsInstance(data['zaakidentificatie'], str)
        self.assertNotEqual(data['zaakidentificatie'], '')
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

    def test_zet_stadsdeel(self):
        url = get_operation_url('zaakobject_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'object': STADSDEEL,
            'relatieomschrijving': 'Afgeleid gebied',
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
                'object': STADSDEEL,
                'relatieomschrijving': 'Afgeleid gebied',
            }
        )

    def test_zet_verantwoordelijk(self):
        url = get_operation_url('rol_create')
        betrokkene = OrganisatorischeEenheidFactory.create(
            naam='Waternet', datum_ontstaan=date(2006, 1, 1)
        )
        betrokkene_url = get_operation_url('organisatorischeeenheid_read', id=betrokkene.id)
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'betrokkene': betrokkene_url,
            'rolomschrijving': 'Behandelaar',
            'rolomschrijvingGeneriek': 'Behandelaar',
            'roltoelichting': 'Baggeren van gracht',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        rol = Rol.objects.get()
        self.assertEqual(rol.zaak, zaak)
        self.assertEqual(rol.betrokkene, betrokkene)
        detail_url = get_operation_url('rol_read', id=rol.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'betrokkene': f"http://testserver{betrokkene_url}",
                'rolomschrijving': 'Behandelaar',
                'rolomschrijvingGeneriek': 'Behandelaar',
                'roltoelichting': 'Baggeren van gracht',
            }
        )

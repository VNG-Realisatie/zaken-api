"""
Als burger wil ik een melding openbare ruimte kunnen doen zodat de gemeente
deze kan behandelen.

Ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/169

Zie ook: test_userstory_39.py
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.constants import RolOmschrijvingGeneriek, RolTypes
from zds_schema.tests import get_operation_url

from zrc.datamodel.constants import ZaakobjectTypes
from zrc.datamodel.models import Zaak
from zrc.datamodel.tests.factories import RolFactory, ZaakFactory

# MOR aangemaakt in melding-app, leeft buiten ZRC
MOR = 'https://example.com/orc/api/v1/mor/37c60cda-689e-4e4a-969c-fa4ed56cb2c6'
CATALOGUS = 'https://example.com/ztc/api/v1/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'
INITIATOR = 'https://example.com/orc/api/v1/brp/natuurlijkepersonen/4bfc45ae-c04e-4398-aa4c-671d35b42ac3'
BEHANDELAAR = 'https://example.com/orc/api/v1/brp/organisatorische-eenheden/d6cbe447-0ff9-4df6-b3d2-68e093ddebbd'


class US169TestCase(APITestCase):

    def test_create_melding(self):
        """
        Maak een zaak voor een melding.
        """
        zaak_create_url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'startdatum': '2018-07-25',
            'einddatum': '2018-08-25',  # afhankelijk van ZTC configuratie (doorlooptijd)
            'einddatumGepland': '2018-08-25',  # afhankelijk van ZTC configuratie (servicenorm)
            'verantwoordelijkeOrganisatie': '391654871',
            'toelichting': 'De struik aan de straatkant belemmert het uitzicht '
                           'vanaf mijn balkon.',
            'omschrijving': '',
            'zaakgeometrie': {
                'type': 'Point',
                'coordinates': [
                    4.4683077,
                    51.9236739
                ]
            }
        }

        # aanmaken zaak
        response = self.client.post(zaak_create_url, data, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        data = response.json()
        self.assertIn('identificatie', data)
        self.assertEqual(data['registratiedatum'], date.today().strftime('%Y-%m-%d'))
        self.assertEqual(data['einddatumGepland'], '2018-08-25')

        zaak_url = data['url']

        # verwijzen naar melding
        zo_create_url = get_operation_url('zaakobject_create')

        response = self.client.post(zo_create_url, {
            'zaak': zaak_url,
            'object': MOR,
            'type': 'MeldingOpenbareRuimte',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        zaak = Zaak.objects.get()
        melding = zaak.zaakobject_set.get()
        self.assertEqual(melding.object_type, ZaakobjectTypes.melding_openbare_ruimte)

        # toevoegen initiator
        # BRP kan/moet bevraagd worden met NAW -> INITIATOR url is resultaat
        rol_create_url = get_operation_url('rol_create')

        response = self.client.post(rol_create_url, {
            'zaak': zaak_url,
            'betrokkene': INITIATOR,
            'betrokkene_type': RolTypes.natuurlijk_persoon,  # 'Natuurlijk persoon'
            'rolomschrijving': 'Initiator',
            'rolomschrijvingGeneriek': 'Initiator',
            'roltoelichting': 'initiele melder',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        initiator = zaak.rol_set.get(rolomschrijving_generiek=RolOmschrijvingGeneriek.initiator)
        self.assertEqual(initiator.betrokkene, INITIATOR)

        # toevoegen behandelaar
        response = self.client.post(rol_create_url, {
            'zaak': zaak_url,
            'betrokkene': BEHANDELAAR,
            'betrokkene_type': RolTypes.vestiging,  # 'Vestiging'
            'rolomschrijving': 'Behandelaar',
            'rolomschrijvingGeneriek': 'Behandelaar',
            'roltoelichting': 'behandelaar',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        behandelaar = zaak.rol_set.get(rolomschrijving_generiek=RolOmschrijvingGeneriek.behandelaar)
        self.assertEqual(behandelaar.betrokkene, BEHANDELAAR)

    def test_ophalen_alle_betrokkenen(self):
        """
        Test dat alle betrokkenen kunnen opgehaald worden, onafhankelijk van rol.

        Zie https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent/pull/9#issuecomment-407882637
        """
        zaak1 = ZaakFactory.create()
        rollen1 = RolFactory.create_batch(3, zaak=zaak1)
        rol2 = RolFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak1.uuid)
        rollen_list_url = get_operation_url('rol_list')

        response = self.client.get(rollen_list_url, {
            'zaak': f"http://testserver{zaak_url}",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(len(response_data), 3)

        expected_urls = {
            f"http://testserver{get_operation_url('rol_read', uuid=rol.uuid)}"
            for rol in rollen1
        }

        received_urls = {rol['url'] for rol in response_data}
        self.assertEqual(received_urls, expected_urls)

        rol2_url = f"http://testserver{get_operation_url('rol_read', uuid=rol2.uuid)}"
        self.assertNotIn(rol2_url, received_urls)

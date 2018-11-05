"""
Als gemeente wil ik dat de aanvraag tbh een straatoptreden als zaak wordt
gecreëerd zodat mijn dossiervorming op orde is en de voortgang transparant is.

Ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/163

Zie ook: test_userstory_39.py, test_userstory_169.py
"""
import datetime

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.constants import RolOmschrijving, RolTypes
from zds_schema.tests import JWTScopesMixin, get_operation_url

from zrc.api.scopes import SCOPE_ZAKEN_CREATE
# aanvraag aangemaakt in extern systeem, leeft buiten ZRC
from zrc.datamodel.constants import ZaakobjectTypes
from zrc.datamodel.models import Zaak
from zrc.datamodel.tests.factories import ZaakFactory

from .utils import parse_isodatetime

CATALOGUS = 'https://example.com/ztc/api/v1/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'
STATUS_TYPE = f'{ZAAKTYPE}/statustypen/1'

VERANTWOORDELIJKE_ORGANISATIE = 'https://www.example.com/orc/api/v1/rsgb/nietnatuurlijkepersonen/1234'
AVG_INZAGE_VERZOEK = 'https://www.example.com/orc/api/v1/avg/inzageverzoeken/1234'
BEHANDELAAR = 'https://www.example.com/orc/api/v1/brp/natuurlijkepersonen/1234'


@override_settings(LINK_FETCHER='zds_schema.mocks.link_fetcher_200')
class US153TestCase(JWTScopesMixin, APITestCase):

    scopes = [SCOPE_ZAKEN_CREATE]

    def test_create_zaak_with_kenmerken(self):
        zaak_create_url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': VERANTWOORDELIJKE_ORGANISATIE,
            'identificatie': 'AVG-inzageverzoek-1',
            'omschrijving': 'Dagontheffing - Station Haarlem',
            'toelichting': 'Het betreft een clown met grote trom, mondharmonica en cymbalen.',
            'startdatum': '2018-08-15',
            'kenmerken': [{
                'kenmerk': 'kenmerk 1',
                'bron': 'bron 1',
            }, {
                'kenmerk': 'kenmerk 2',
                'bron': 'bron 2',
            }]
        }

        response = self.client.post(zaak_create_url, data, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        zaak = Zaak.objects.get(identificatie=data['identificatie'])
        self.assertEqual(zaak.zaakkenmerk_set.count(), 2)

    def test_read_zaak_with_kenmerken(self):
        zaak = ZaakFactory.create()
        zaak.zaakkenmerk_set.create(kenmerk='kenmerk 1', bron='bron 1')
        self.assertEqual(zaak.zaakkenmerk_set.count(), 1)

        zaak_read_url = get_operation_url('zaak_read', uuid=zaak.uuid)

        response = self.client.get(zaak_read_url, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        data = response.json()

        self.assertTrue('kenmerken' in data)
        self.assertEqual(len(data['kenmerken']), 1)
        self.assertDictEqual(
            data['kenmerken'][0],
            {
                'kenmerk': 'kenmerk 1',
                'bron': 'bron 1',
            }
        )

    def test_update_zaak_with_kenmerken(self):
        zaak = ZaakFactory.create()
        kenmerk_1 = zaak.zaakkenmerk_set.create(kenmerk='kenmerk 1', bron='bron 1')
        self.assertEqual(zaak.zaakkenmerk_set.count(), 1)

        zaak_read_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        response = self.client.get(zaak_read_url, HTTP_ACCEPT_CRS='EPSG:4326')

        data = response.json()

        zaak_update_url = get_operation_url('zaak_update', uuid=zaak.uuid)
        data['kenmerken'].append({
            'kenmerk': 'kenmerk 2',
            'bron': 'bron 2',
        })

        response = self.client.put(zaak_update_url, data, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        zaak = Zaak.objects.get(identificatie=zaak.identificatie)
        self.assertEqual(zaak.zaakkenmerk_set.count(), 2)

        # All objects are deleted, and (re)created.
        self.assertFalse(kenmerk_1.pk in zaak.zaakkenmerk_set.values_list('pk', flat=True))

    @override_settings(
        ZDS_CLIENT_CLASS='zds_schema.mocks.MockClient'
    )
    def test_full_flow(self):
        zaak_create_url = get_operation_url('zaak_create')
        zaakobject_create_url = get_operation_url('zaakobject_create')
        status_create_url = get_operation_url('status_create')
        rol_create_url = get_operation_url('rol_create')

        # Creeer InzageVerzoek
        # self.client.post(...)

        # Creeer Zaak
        data = {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': VERANTWOORDELIJKE_ORGANISATIE,
            'identificatie': 'AVG-inzageverzoek-1',
            'omschrijving': 'Melding binnengekomen via website.',
            'toelichting': 'Vanuit melding: Beste,\n\nGraag zou ik ...',
            'startdatum': '2018-08-22',
            'kenmerken': [{
                'kenmerk': 'kenmerk 1',
                'bron': 'bron 1',
            }, {
                'kenmerk': 'kenmerk 2',
                'bron': 'bron 2',
            }]
        }
        response = self.client.post(zaak_create_url, data, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        zaak = response.json()

        # Koppel Zaak aan InzageVerzoek
        data = {
            'zaak': zaak['url'],
            'object': AVG_INZAGE_VERZOEK,
            'relatieomschrijving': 'Inzage verzoek horend bij deze zaak.',
            'type': ZaakobjectTypes.avg_inzage_verzoek
        }
        response = self.client.post(zaakobject_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        # Geef de Zaak een initiele Status
        data = {
            'zaak': zaak['url'],
            'statusType': STATUS_TYPE,
            'datumStatusGezet': datetime.datetime.now().isoformat(),
        }
        response = self.client.post(status_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        # Haal mogelijke rollen op uit ZTC...
        # self.client.get(...)

        # Voeg een behandelaar toe.
        data = {
            'zaak': zaak['url'],
            'betrokkene': BEHANDELAAR,
            'betrokkeneType': RolTypes.natuurlijk_persoon,
            'rolomschrijving': RolOmschrijving.behandelaar,
            'roltoelichting': 'Initiele behandelaar die meerdere (deel)behandelaren kan aanwijzen.'
        }
        response = self.client.post(rol_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        # Status wijzigingen...

        # Update Zaak met nieuwe behandeltermijn, uitstel van 2 weken.
        zaak_update_url = get_operation_url('zaak_update', uuid=zaak['url'].rsplit('/', 1)[1])

        if zaak['einddatumGepland']:
            end_date_planned = parse_isodatetime(zaak['einddatumGepland'])
        else:
            end_date_planned = datetime.datetime.now()

        data = zaak.copy()
        data['einddatumGepland'] = (end_date_planned + datetime.timedelta(days=14)).strftime('%Y-%m-%d')

        response = self.client.put(zaak_update_url, data, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # Voeg documenten toe...
        # self.client.post(...)
        # Koppel documenten aan Zaak
        # self.client.post(...)

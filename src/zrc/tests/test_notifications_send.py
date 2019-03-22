import json

from django.conf import settings
from django.test import override_settings

from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.tests import JWTScopesMixin, get_operation_url

from zrc.api.scopes import (
    SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_BIJWERKEN, SCOPE_ZAKEN_CREATE
)
from zrc.datamodel.tests.factories import ResultaatFactory, ZaakFactory

from .utils import ZAAK_WRITE_KWARGS

VERANTWOORDELIJKE_ORGANISATIE = '517439943'

# ZTC
ZTC_ROOT = 'https://example.com/ztc/api/v1'
CATALOGUS = f'{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'
RESULTAATTYPE = f'{ZAAKTYPE}/resultaattypen/5b348dbf-9301-410b-be9e-83723e288785'


@override_settings(LINK_FETCHER='vng_api_common.mocks.link_fetcher_200')
class SendNotifTestCase(JWTScopesMixin, APITestCase):
    scopes = [SCOPE_ZAKEN_CREATE, SCOPE_ZAKEN_BIJWERKEN, SCOPE_ZAKEN_ALLES_LEZEN]

    @patch('zds_client.Client.request')
    def test_send_notif_create_zaak(self, mock_client):
        """
        Check if notifications will be send when zaak is created
        """
        url = get_operation_url('zaak_create')
        data = {
            'zaaktype': ZAAKTYPE,
            'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
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

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        data = response.json()
        notif_args, notif_kwargs = mock_client.call_args_list[0]
        msg = json.loads(notif_kwargs['data'])

        self.assertEqual(notif_args[0], settings.NOTIFICATIES_URL)
        self.assertEqual(msg['kanaal'], settings.NOTIFICATIES_KANAAL)
        self.assertEqual(msg['resource'], 'zaak')
        self.assertEqual(msg['actie'], 'create')
        self.assertEqual(msg['resourceUrl'], data['url'])
        self.assertEqual(msg['kenmerken'][0]['bronorganisatie'], data['bronorganisatie'])
        self.assertEqual(msg['kenmerken'][1]['zaaktype'], data['zaaktype'])
        self.assertEqual(msg['kenmerken'][2]['vertrouwelijkheidaanduiding'], data['vertrouwelijkheidaanduiding'])

    @patch('zds_client.Client.request')
    def test_send_notif_delete_resultaat(self, mock_client):
        """
        Check if notifications will be send when resultaat is deleted
        """
        zaak = ZaakFactory.create()
        resultaat = ResultaatFactory.create(zaak=zaak)
        resultaat_url = get_operation_url('resultaat_update', uuid=resultaat.uuid)

        response = self.client.delete(resultaat_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)

        notif_args, notif_kwargs = mock_client.call_args_list[0]
        msg = json.loads(notif_kwargs['data'])

        self.assertEqual(notif_args[0], settings.NOTIFICATIES_URL)
        self.assertEqual(msg['kanaal'], settings.NOTIFICATIES_KANAAL)
        self.assertEqual(msg['resource'], 'resultaat')
        self.assertEqual(msg['actie'], 'destroy')
        self.assertEqual(msg['resourceUrl'], 'http://testserver{}'.format(resultaat_url))
        self.assertEqual(msg['kenmerken'][0]['bronorganisatie'], zaak.bronorganisatie)
        self.assertEqual(msg['kenmerken'][1]['zaaktype'], zaak.zaaktype)
        self.assertEqual(msg['kenmerken'][2]['vertrouwelijkheidaanduiding'], zaak.vertrouwelijkheidaanduiding)

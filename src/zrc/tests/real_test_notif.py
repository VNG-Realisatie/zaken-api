from django.test import override_settings

from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.models import APICredential
from vng_api_common.tests import (
    JWTScopesMixin, get_operation_url, get_validation_errors
)

from zrc.api.scopes import SCOPE_ZAKEN_CREATE

from .utils import ZAAK_WRITE_KWARGS

ZAAKTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1'
VERANTWOORDELIJKE_ORGANISATIE = '517439943'


@override_settings(LINK_FETCHER='vng_api_common.mocks.link_fetcher_200')
class SendNotifTestCase(JWTScopesMixin, APITestCase):
    scopes = [SCOPE_ZAKEN_CREATE]

    def test_send_notif_create_zaak(self):
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
        cretential = APICredential.objects.create(
            client_id='zrc',
            secret='zrc',
            api_root='http://127.0.0.1:8001'
        )

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS, HTTP_HOST='localhost')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        data = response.json()

import unittest
from copy import deepcopy

from django.test import override_settings

from rest_framework.test import APITestCase
from vng_api_common.audittrails.models import AuditTrail
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.tests import JWTScopesMixin, generate_jwt, reverse
from zds_client.tests.mocks import mock_client

from zrc.datamodel.models import Zaak
from zrc.tests.utils import ZAAK_WRITE_KWARGS

from ..scopes import (
    SCOPE_ZAKEN_ALLES_VERWIJDEREN, SCOPE_ZAKEN_BIJWERKEN, SCOPE_ZAKEN_CREATE
)

# ZTC
ZTC_ROOT = 'https://example.com/ztc/api/v1'
DRC_ROOT = 'https://example.com/drc/api/v1'
CATALOGUS = f'{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'
RESULTAATTYPE = f'{ZAAKTYPE}/resultaattypen/5b348dbf-9301-410b-be9e-83723e288785'
INFORMATIE_OBJECT = f'{DRC_ROOT}/enkelvoudiginformatieobjecten/1234'


@override_settings(
    LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
    ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient'
)
class AuditTrailTests(JWTScopesMixin, APITestCase):
    def setUp(self):
        token = generate_jwt(
            scopes=[
                SCOPE_ZAKEN_CREATE,
                SCOPE_ZAKEN_BIJWERKEN,
                SCOPE_ZAKEN_ALLES_VERWIJDEREN
            ],
            zaaktypes=['https://example.com/zaaktype/123']
        )
        self.client.credentials(HTTP_AUTHORIZATION=token)

        self.responses = {
            'https://example.com/zaaktype/123': {
                'url': 'https://example.com/zaaktype/123',
                'productenOfDiensten': [
                    'https://example.com/product/123',
                    'https://example.com/dienst/123',
                ]
            }
        }

    def create_zaak(self):
        url = reverse('zaak-list')

        zaak_data = {
            'zaaktype': 'https://example.com/zaaktype/123',
            'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': '517439943',
            'registratiedatum': '2018-12-24',
            'startdatum': '2018-12-24',
            'productenOfDiensten': ['https://example.com/product/123']
        }
        with mock_client(self.responses):
            response = self.client.post(url, zaak_data, **ZAAK_WRITE_KWARGS)

        return response.data

    def test_create_zaak_audittrail(self):
        zaak_response = self.create_zaak()

        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_response['url'])
        self.assertEqual(audittrails.count(), 1)

        # Verify that the audittrail for the Zaak creation contains the correct
        # information
        zaak_create_audittrail = audittrails.first()
        self.assertEqual(zaak_create_audittrail.bron, 'ZRC')
        self.assertEqual(zaak_create_audittrail.actie, 'create')
        self.assertEqual(zaak_create_audittrail.resultaat, 201)
        self.assertEqual(zaak_create_audittrail.oud, None)
        self.assertEqual(zaak_create_audittrail.nieuw, zaak_response)

    def test_create_and_delete_resultaat_audittrails(self):
        zaak_response = self.create_zaak()

        url = reverse('resultaat-list')
        resultaat_data = {
            'zaak': zaak_response['url'],
            'resultaatType': RESULTAATTYPE
        }
        response = self.client.post(url, resultaat_data, **ZAAK_WRITE_KWARGS)
        resultaat_response = response.data

        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_response['url'])
        self.assertEqual(audittrails.count(), 2)

        # Verify that the audittrail for the Resultaat creation contains the
        # correct information
        resultaat_create_audittrail = audittrails[1]
        self.assertEqual(resultaat_create_audittrail.bron, 'ZRC')
        self.assertEqual(resultaat_create_audittrail.actie, 'create')
        self.assertEqual(resultaat_create_audittrail.resultaat, 201)
        self.assertEqual(resultaat_create_audittrail.oud, None)
        self.assertEqual(resultaat_create_audittrail.nieuw, resultaat_response)

        response = self.client.delete(resultaat_response['url'], **ZAAK_WRITE_KWARGS)
        self.assertEqual(audittrails.count(), 3)

        # Verify that the audittrail for the Resultaat deletion contains the
        # correct information
        resultaat_delete_audittrail = audittrails[2]
        self.assertEqual(resultaat_delete_audittrail.bron, 'ZRC')
        self.assertEqual(resultaat_delete_audittrail.actie, 'destroy')
        self.assertEqual(resultaat_delete_audittrail.resultaat, 204)
        self.assertEqual(resultaat_delete_audittrail.oud, resultaat_response)
        self.assertEqual(resultaat_delete_audittrail.nieuw, None)

    def test_update_zaak_audittrails(self):
        zaak_data = self.create_zaak()

        modified_data = deepcopy(zaak_data)
        url = modified_data.pop('url')
        modified_data.pop('verlenging')
        modified_data['toelichting'] = 'aangepast'

        with mock_client(self.responses):
            response = self.client.put(url, modified_data, **ZAAK_WRITE_KWARGS)
            zaak_response = response.data

        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_response['url'])
        self.assertEqual(audittrails.count(), 2)

        # Verify that the audittrail for the Zaak update contains the correct
        # information
        zaak_update_audittrail = audittrails[1]
        self.assertEqual(zaak_update_audittrail.bron, 'ZRC')
        self.assertEqual(zaak_update_audittrail.actie, 'update')
        self.assertEqual(zaak_update_audittrail.resultaat, 200)
        self.assertEqual(zaak_update_audittrail.oud, zaak_data)
        self.assertEqual(zaak_update_audittrail.nieuw, zaak_response)

    def test_partial_update_zaak_audittrails(self):
        zaak_data = self.create_zaak()

        with mock_client(self.responses):
            response = self.client.patch(zaak_data['url'], {
                'toelichting': 'aangepast'
            }, **ZAAK_WRITE_KWARGS)
            zaak_response = response.data

        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_response['url'])
        self.assertEqual(audittrails.count(), 2)

        # Verify that the audittrail for the Zaak partial_update contains the
        # correct information
        zaak_update_audittrail = audittrails[1]
        self.assertEqual(zaak_update_audittrail.bron, 'ZRC')
        self.assertEqual(zaak_update_audittrail.actie, 'partial_update')
        self.assertEqual(zaak_update_audittrail.resultaat, 200)
        self.assertEqual(zaak_update_audittrail.oud, zaak_data)
        self.assertEqual(zaak_update_audittrail.nieuw, zaak_response)

    def test_create_zaakinformatieobject_audittrail(self):
        zaak_data = self.create_zaak()

        zaak_uuid = zaak_data['url'].split('/')[-1]
        url = reverse('zaakinformatieobject-list', kwargs={'zaak_uuid': zaak_uuid})

        response = self.client.post(url, {
            'informatieobject': INFORMATIE_OBJECT,
        })

        zaakinformatieobject_response = response.data

        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_data['url'])
        self.assertEqual(audittrails.count(), 2)

        # Verify that the audittrail for the ZaakInformatieObject creation
        # contains the correct information
        resultaat_create_audittrail = audittrails[1]
        self.assertEqual(resultaat_create_audittrail.bron, 'ZRC')
        self.assertEqual(resultaat_create_audittrail.actie, 'create')
        self.assertEqual(resultaat_create_audittrail.resultaat, 201)
        self.assertEqual(resultaat_create_audittrail.oud, None)
        self.assertEqual(resultaat_create_audittrail.nieuw, zaakinformatieobject_response)

    def test_delete_zaak_cascade_audittrails(self):
        zaak_data = self.create_zaak()

        # Delete the Zaak
        response = self.client.delete(zaak_data['url'], **ZAAK_WRITE_KWARGS)

        # Verify that deleting the Zaak deletes all related AuditTrails
        audittrails = AuditTrail.objects.filter(hoofd_object=zaak_data['url'])
        self.assertEqual(audittrails.count(), 0)

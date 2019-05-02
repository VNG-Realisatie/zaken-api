import unittest

from django.contrib.gis.geos import Point
from django.test import override_settings, tag
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import (
    Archiefnominatie, BrondatumArchiefprocedureAfleidingswijze,
    VertrouwelijkheidsAanduiding
)
from vng_api_common.tests import (
    JWTScopesMixin, generate_jwt, get_operation_url, reverse
)
from zds_client.tests.mocks import mock_client

from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.models import Zaak
from zrc.datamodel.tests.factories import StatusFactory, ZaakFactory
from zrc.tests.constants import POLYGON_AMSTERDAM_CENTRUM
from zrc.tests.utils import (
    ZAAK_READ_KWARGS, ZAAK_WRITE_KWARGS, isodatetime, utcdatetime
)
from zrc.datamodel.models import AuditTrail

from ..scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN, SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_BIJWERKEN,
    SCOPE_ZAKEN_CREATE, SCOPEN_ZAKEN_HEROPENEN
)

# ZTC
ZTC_ROOT = 'https://example.com/ztc/api/v1'
CATALOGUS = f'{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'
RESULTAATTYPE = f'{ZAAKTYPE}/resultaattypen/5b348dbf-9301-410b-be9e-83723e288785'
STATUSTYPE = f'{ZAAKTYPE}/statustypen/5b348dbf-9301-410b-be9e-83723e288785'
STATUSTYPE2 = f'{ZAAKTYPE}/statustypen/b86aa339-151e-45f0-ad6c-20698f50b6cd'


@override_settings(
    LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
    ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient'
)
class AuditTrailTests(JWTScopesMixin, APITestCase):
    def test_create_zaak_creates_audittrail(self):
        url = reverse('zaak-list')
        token = generate_jwt(
            scopes=[SCOPE_ZAKEN_CREATE],
            zaaktypes=['https://example.com/zaaktype/123']
        )
        self.client.credentials(HTTP_AUTHORIZATION=token)

        responses = {
            'https://example.com/zaaktype/123': {
                'url': 'https://example.com/zaaktype/123',
                'productenOfDiensten': [
                    'https://example.com/product/123',
                    'https://example.com/dienst/123',
                ]
            }
        }

        with mock_client(responses):
            response = self.client.post(url, {
                'zaaktype': 'https://example.com/zaaktype/123',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-12-24',
                'startdatum': '2018-12-24',
                'productenOfDiensten': ['https://example.com/product/123'],
            }, **ZAAK_WRITE_KWARGS)

        zaak = response.data
        audittrails = AuditTrail.objects.filter(hoofdObject=zaak['url'])
        self.assertEqual(audittrails.count(), 1)

        audittrail = audittrails.first()
        self.assertEqual(audittrail.bron, 'ZRC')
        self.assertEqual(audittrail.actie, 'create')
        self.assertEqual(audittrail.resultaat, 201)




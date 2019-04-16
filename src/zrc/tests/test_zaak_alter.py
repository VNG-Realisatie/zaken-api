from django.test import override_settings
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTScopesMixin, generate_jwt, reverse

from zrc.api.scopes import (
    SCOPE_ZAKEN_BIJWERKEN, SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN
)
from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.tests.factories import ZaakFactory
from zrc.tests.utils import ZAAK_WRITE_KWARGS


@override_settings(LINK_FETCHER='vng_api_common.mocks.link_fetcher_200')
class ApiStrategyTests(JWTScopesMixin, APITestCase):

    def test_update_zaak_open(self):
        zaak = ZaakFactory.create(betalingsindicatie=BetalingsIndicatie.geheel)
        url = reverse(zaak)

        token = generate_jwt(scopes=[SCOPE_ZAKEN_BIJWERKEN], zaaktypes=[zaak.zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.patch(url, {
            'betalingsindicatie': BetalingsIndicatie.nvt,
        }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.json()['betalingsindicatie'], BetalingsIndicatie.nvt)
        zaak.refresh_from_db()
        self.assertEqual(zaak.betalingsindicatie, BetalingsIndicatie.nvt)

    def test_update_zaak_closed_not_allowed(self):
        zaak = ZaakFactory.create(
            einddatum=timezone.now()
        )
        url = reverse(zaak)

        token = generate_jwt(scopes=[SCOPE_ZAKEN_BIJWERKEN], zaaktypes=[zaak.zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.patch(url, {
            'betalingsindicatie': BetalingsIndicatie.nvt,
        }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_zaak_closed_allowed(self):
        zaak = ZaakFactory.create(
            einddatum=timezone.now()
        )
        url = reverse(zaak)

        token = generate_jwt(scopes=[SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN], zaaktypes=[zaak.zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.patch(url, {
            'betalingsindicatie': BetalingsIndicatie.nvt,
        }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

"""
Guarantee that the proper authorization amchinery is in place.
"""
from unittest import skip

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import AuthCheckMixin, generate_jwt

from zrc.datamodel.tests.factories import ZaakFactory

from ..scopes import SCOPE_ZAKEN_ALLES_LEZEN
from .utils import reverse


class ZakenCreateTests(AuthCheckMixin, APITestCase):

    def test_cannot_create_zaak_without_correct_scope(self):
        url = reverse('zaak-list')

        self.assertForbidden(url, method='post')


@skip('Test old Authentication Format. New tests in test_auth_new_format.py')
class ZakenReadTests(AuthCheckMixin, APITestCase):

    def test_cannot_read_without_correct_scope(self):
        zaak = ZaakFactory.create()
        urls = [
            reverse('zaak-list'),
            reverse('zaak-detail', kwargs={'uuid': zaak.uuid}),
            reverse('status-list'),
            reverse('status-detail', kwargs={'uuid': 'dummy'}),
            reverse('zaakobject-list'),
            reverse('zaakobject-detail', kwargs={'uuid': 'dummy'}),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertForbidden(url, method='get')

    def test_zaaktypes_claim(self):
        """
        Assert you can only read ZAAKen of the zaaktypes in the claim.
        """
        ZaakFactory.create(zaaktype='https://zaaktype.nl/ok')
        ZaakFactory.create(zaaktype='https://zaaktype.nl/not_ok')
        url = reverse('zaak-list')
        jwt = generate_jwt(
            scopes=[SCOPE_ZAKEN_ALLES_LEZEN],
            zaaktypes=['https://zaaktype.nl/ok'],
        )
        self.client.credentials(HTTP_AUTHORIZATION=jwt)

        response = self.client.get(url, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['zaaktype'], 'https://zaaktype.nl/ok')

    def test_zaaktypes_claim_detail(self):
        """
        Assert you can only read ZAAKen of the zaaktypes in the claim.
        """
        zaak = ZaakFactory.create(zaaktype='https://zaaktype.nl/not_ok')
        url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})

        self.assertForbiddenWithCorrectScope(
            url, [SCOPE_ZAKEN_ALLES_LEZEN],
            zaaktypes=['https://zaaktype.nl/ok'],
            request_kwargs={'HTTP_ACCEPT_CRS': 'EPSG:4326'}
        )

    def test_zaaktypes_wildcard(self):
        zaak = ZaakFactory.create()

        list_url = reverse('zaak-list')
        detail_url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})

        jwt = generate_jwt(
            scopes=[SCOPE_ZAKEN_ALLES_LEZEN],
            zaaktypes=['*'],
        )
        self.client.credentials(HTTP_AUTHORIZATION=jwt)

        list_response = self.client.get(list_url, HTTP_ACCEPT_CRS='EPSG:4326')
        detail_response = self.client.get(detail_url, HTTP_ACCEPT_CRS='EPSG:4326')

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['results']), 1)

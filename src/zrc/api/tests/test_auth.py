"""
Guarantee that the proper authorization amchinery is in place.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import generate_jwt

from .utils import reverse


class ZakenCreateTests(APITestCase):

    def test_cannot_create_zaak_without_correct_scope(self):
        """
        Asser that the zrc.api.scopes.SCOPE_ZAKEN_CREATE scope is required.
        """
        url = reverse('zaak-list')

        with self.subTest(case='JWT missing'):
            response = self.client.post(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(case='Correct scope missing'):
            jwt = generate_jwt(['invalid.scope'])
            self.client.credentials(HTTP_AUTHORIZATION=jwt)

            response = self.client.post(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

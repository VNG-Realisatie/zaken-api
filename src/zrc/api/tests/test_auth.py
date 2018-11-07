"""
Guarantee that the proper authorization amchinery is in place.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.scopes import Scope
from zds_schema.tests import generate_jwt

from .utils import reverse


class AuthCheckMixin:

    def assertForbidden(self, url, method='get'):
        """
        Assert that an appropriate scope is required.
        """
        do_request = getattr(self.client, method)

        with self.subTest(case='JWT missing'):
            response = do_request(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(case='Correct scope missing'):
            jwt = generate_jwt([Scope('invalid.scope')])
            self.client.credentials(HTTP_AUTHORIZATION=jwt)

            response = do_request(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ZakenCreateTests(AuthCheckMixin, APITestCase):

    def test_cannot_create_zaak_without_correct_scope(self):
        url = reverse('zaak-list')

        self.assertForbidden(url, method='post')


class ZakenReadTests(AuthCheckMixin, APITestCase):

    def test_cannot_read_without_correct_scope(self):
        urls = [
            reverse('zaak-list'),
            reverse('zaak-detail', kwargs={'uuid': 'dummy'}),
            reverse('status-list'),
            reverse('status-detail', kwargs={'uuid': 'dummy'}),
            reverse('zaakobject-list'),
            reverse('zaakobject-detail', kwargs={'uuid': 'dummy'}),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertForbidden(url, method='get')

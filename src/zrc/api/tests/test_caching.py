"""
Test that the caching mechanisms are in place.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse
from vng_api_common.tests.schema import get_spec

from zrc.datamodel.tests.factories import StatusFactory


class StatusCacheTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_status_get_cache_header(self):
        status_ = StatusFactory.create()

        response = self.client.get(reverse(status_))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ETag", response)
        self.assertNotEqual(response["ETag"], "")

    def test_status_head_cache_header(self):
        status_ = StatusFactory.create()

        response = self.client.head(reverse(status_))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ETag", response)
        self.assertNotEqual(response["ETag"], "")

        # head requests should not return a response body, only headers
        self.assertEqual(response.content, b"")

    def test_head_in_apischema(self):
        spec = get_spec()

        endpoint = spec["paths"]["/statussen/{uuid}"]

        self.assertIn("head", endpoint)

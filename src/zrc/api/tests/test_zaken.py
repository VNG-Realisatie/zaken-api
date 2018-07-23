import unittest

from rest_framework import status
from rest_framework.test import APITestCase

from .utils import reverse


class ApiStrategyTests(APITestCase):

    @unittest.expectedFailure
    def test_api_10_lazy_eager_loading(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_11_expand_nested_resources(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_12_subset_fields(self):
        raise NotImplementedError

    def test_api_51_status_codes(self):
        with self.subTest(crud='create'):
            url = reverse('zaak-list')

            response = self.client.post(url, {
                'zaaktype': 'https://example.com/foo/bar',
                'bronorganisatie': '517439943',
                'registratiedatum': '2018-06-11',
            })

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response['Location'], response.data['url'])

        with self.subTest(crud='read'):
            response_detail = self.client.get(response.data['url'])
            self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

from rest_framework.test import APITestCase

from .utils import reverse


class DSOApiStrategyTests(APITestCase):

    def test_api_19_documentation_version(self):
        url = reverse('schema-json', kwargs={'format': '.json'})

        response = self.client.get(url)

        self.assertIn('application/json', response['Content-Type'])

        doc = response.json()

        if 'swagger' in doc:
            self.assertGreaterEqual(doc['swagger'], '2.0')
        elif 'openapi' in doc:
            self.assertGreaterEqual(doc['openapi'], '3.0.0')
        else:
            self.fail('Unknown documentation version')

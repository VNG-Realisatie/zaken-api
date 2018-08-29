from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from .utils import reverse


class NotFoundView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        raise NotFound("Some detail message")


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

    def test_api_50_error_handling_standardized(self):
        view = NotFoundView.as_view()
        request = APIRequestFactory().get('/some/irrelevant/url', HTTP_ACCEPT='application/json')

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # can't verify UUID...
        self.assertTrue(response.data['instance'].startswith('urn:uuid:'))
        del response.data['instance']

        self.assertEqual(response.data, {
            'type': "NotFound",
            'title': "Niet gevonden.",
            'status': 404,
            'detail': "Some detail message",
        })

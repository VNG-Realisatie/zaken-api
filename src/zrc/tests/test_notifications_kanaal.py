from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings

from rest_framework.test import APITestCase


class CreateNotifKanaalTestCase(APITestCase):

    @patch('zds_client.Client')
    def test_kanaal_create_with_name(self, mock_client):
        """
        Test is request to create kanaal is send with specified kanaal name
        """
        client = mock_client.from_url.return_value
        client.list.return_value = []

        stdout = StringIO()
        call_command('register_kanaal', 'kanaal_test', nc_api_root='https://example.com/api/v1', stdout=stdout)

        client.create.assert_called_once_with(
            'kanaal',
            {'naam': 'kanaal_test'}
        )

    @patch('zds_client.Client')
    @override_settings(NOTIFICATIONS_KANAAL='dummy-kanaal')
    def test_kanaal_create_without_name(self, mock_client):
        """
        Test is request to create kanaal is send with default kanaal name
        """
        client = mock_client.from_url.return_value
        client.list.return_value = []

        stdout = StringIO()
        call_command('register_kanaal', nc_api_root='https://example.com/api/v1', stdout=stdout)

        client.create.assert_called_once_with(
            'kanaal',
            {'naam': 'dummy-kanaal'}
        )

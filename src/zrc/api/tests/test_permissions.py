from unittest.mock import patch

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, reverse
from zds_client.tests.mocks import mock_client

from zrc.tests.utils import ZAAK_WRITE_KWARGS

from ..scopes import SCOPE_ZAKEN_ALLES_LEZEN

# ZTC
ZTC_ROOT = 'https://example.com/ztc/api/v1'
CATALOGUS = f'{ZTC_ROOT}/catalogus/878a3318-5950-4642-8715-189745f91b04'
ZAAKTYPE = f'{CATALOGUS}/zaaktypen/283ffaf5-8470-457b-8064-90e5728f413f'

RESPONSES = {
    ZAAKTYPE: {
        'url': ZAAKTYPE,
    }
}


class PermissionTests(JWTAuthMixin, APITestCase):

    scopes = [
        SCOPE_ZAKEN_ALLES_LEZEN,
    ]
    zaaktype = ZAAKTYPE

    @override_settings(LINK_FETCHER='vng_api_common.mocks.link_fetcher_200')
    @patch("vng_api_common.validators.obj_has_shape", return_value=True)
    def test_create_zaak_without_scope_raises_permission_denied(self, *mocks):
        url = reverse('zaak-list')

        with mock_client(RESPONSES):
            response = self.client.post(url, {
                'zaaktype': ZAAKTYPE,
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-06-11',
                'startdatum': '2018-06-11',
            }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'permission_denied')

"""
Guarantee that the proper authorization amchinery is in place.
"""
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.tests import AuthCheckMixin, JWTAuthMixin

from zrc.datamodel.tests.factories import (
    StatusFactory, ZaakFactory, ZaakObjectFactory
)
from zrc.tests.utils import ZAAK_READ_KWARGS

from ..scopes import SCOPE_ZAKEN_ALLES_LEZEN
from .utils import reverse


@override_settings(ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient')
class ZakenScopeForbiddenTests(AuthCheckMixin, APITestCase):

    def test_cannot_create_zaak_without_correct_scope(self):
        url = reverse('zaak-list')
        self.assertForbidden(url, method='post')

    def test_cannot_read_without_correct_scope(self):
        zaak = ZaakFactory.create()
        status = StatusFactory.create()
        zaak_object = ZaakObjectFactory.create()
        urls = [
            reverse('zaak-list'),
            reverse('zaak-detail', kwargs={'uuid': zaak.uuid}),
            reverse('status-list'),
            reverse('status-detail', kwargs={'uuid': status.uuid}),
            reverse('zaakobject-list'),
            reverse('zaakobject-detail', kwargs={'uuid': zaak_object.uuid}),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertForbidden(url, method='get', request_kwargs=ZAAK_READ_KWARGS)


class ZaakReadCorrectScopeTests(JWTAuthMixin, APITestCase):
    scopes = [SCOPE_ZAKEN_ALLES_LEZEN]
    zaaktype = 'https://zaaktype.nl/ok'
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduiding.openbaar

    def test_zaak_list(self):
        """
        Assert you can only list ZAAKen of the zaaktypes and vertrouwelijkheidaanduiding
        of your authorization
        """
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/not_ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.zeer_geheim
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/not_ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.zeer_geheim
        )
        url = reverse('zaak-list')

        response = self.client.get(url, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['zaaktype'], 'https://zaaktype.nl/ok')
        self.assertEqual(results[0]['vertrouwelijkheidaanduiding'], VertrouwelijkheidsAanduiding.openbaar)

    def test_zaak_retreive(self):
        """
        Assert you can only read ZAAKen of the zaaktypes and vertrouwelijkheidaanduiding
        of your authorization
        """
        zaak1 = ZaakFactory.create(
            zaaktype='https://zaaktype.nl/not_ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        zaak2 = ZaakFactory.create(
            zaaktype='https://zaaktype.nl/ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.zeer_geheim
        )
        url1 = reverse('zaak-detail', kwargs={'uuid': zaak1.uuid})
        url2 = reverse('zaak-detail', kwargs={'uuid': zaak2.uuid})

        response1 = self.client.get(url1, **ZAAK_READ_KWARGS)
        response2 = self.client.get(url2, **ZAAK_READ_KWARGS)

        self.assertEqual(response1.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_superuser(self):
        """
        superuser read everything
        """
        self.applicatie.heeft_alle_autorisaties = True
        self.applicatie.save()

        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/not_ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.zeer_geheim
        )
        ZaakFactory.create(
            zaaktype='https://zaaktype.nl/not_ok',
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.zeer_geheim
        )
        url = reverse('zaak-list')

        response = self.client.get(url, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']

        self.assertEqual(len(results), 4)


class StatusReadTests(JWTAuthMixin, APITestCase):
    scopes = [SCOPE_ZAKEN_ALLES_LEZEN]
    zaaktype = 'https://zaaktype.nl/ok'
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduiding.beperkt_openbaar

    def test_list_status_limited_to_authorized_zaken(self):
        url = reverse('status-list')
        # must show up
        status1 = StatusFactory.create(
            zaak__zaaktype='https://zaaktype.nl/ok',
            zaak__vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )
        # must not show up
        StatusFactory.create(
            zaak__zaaktype='https://zaaktype.nl/ok',
            zaak__vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.vertrouwelijk
        )
        # must not show up
        StatusFactory.create(
            zaak__zaaktype='https://zaaktype.nl/not_ok',
            zaak__vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduiding.openbaar
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['url'], reverse(status1))

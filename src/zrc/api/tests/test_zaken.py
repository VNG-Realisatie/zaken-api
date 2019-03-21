import unittest

from django.contrib.gis.geos import Point
from django.test import override_settings, tag
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.mocks import ZTCMockClient
from vng_api_common.tests import JWTScopesMixin, generate_jwt, reverse
from zds_client.tests.mocks import mock_client

from zrc.datamodel.constants import BetalingsIndicatie
from zrc.datamodel.models import Zaak
from zrc.datamodel.tests.factories import StatusFactory, ZaakFactory
from zrc.tests.utils import (
    ZAAK_READ_KWARGS, ZAAK_WRITE_KWARGS, isodatetime, utcdatetime
)

from ..scopes import (
    SCOPE_STATUSSEN_TOEVOEGEN, SCOPE_ZAKEN_ALLES_LEZEN, SCOPE_ZAKEN_BIJWERKEN,
    SCOPE_ZAKEN_CREATE
)


@override_settings(LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
                   ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient')
class ApiStrategyTests(JWTScopesMixin, APITestCase):

    scopes = [
        SCOPE_ZAKEN_CREATE,
        SCOPE_ZAKEN_ALLES_LEZEN,
    ]
    zaaktypes = ['https://example.com/foo/bar']

    @unittest.expectedFailure
    def test_api_10_lazy_eager_loading(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_11_expand_nested_resources(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_api_12_subset_fields(self):
        raise NotImplementedError

    def test_api_44_crs_headers(self):
        # We wijken bewust af - EPSG:4326 is de standaard projectie voor WGS84
        # De andere opties in de API strategie lijken in de praktijk niet/nauwelijks
        # gebruikt te worden, en zien er vreemd uit t.o.v. wel courant gebruikte
        # opties.
        zaak = ZaakFactory.create(zaakgeometrie=Point(4.887990, 52.377595))  # LONG LAT
        url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

        response = self.client.get(url, HTTP_ACCEPT_CRS='dummy')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

        response = self.client.get(url, HTTP_ACCEPT_CRS='EPSG:4326')
        self.assertEqual(
            response['Content-Crs'],
            'EPSG:4326'
        )

    def test_api_51_status_codes(self):
        with self.subTest(crud='create'):
            url = reverse('zaak-list')

            response = self.client.post(url, {
                'zaaktype': 'https://example.com/foo/bar',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-06-11',
                'startdatum': '2018-06-11',
            }, **ZAAK_WRITE_KWARGS)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response['Location'], response.data['url'])

        with self.subTest(crud='read'):
            response_detail = self.client.get(
                response.data['url'],
                **ZAAK_READ_KWARGS
            )
            self.assertEqual(response_detail.status_code, status.HTTP_200_OK)


@override_settings(
    LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
    ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient'
)
class ZakenTests(JWTScopesMixin, APITestCase):

    scopes = [
        SCOPE_ZAKEN_ALLES_LEZEN,
        SCOPE_ZAKEN_CREATE,
        SCOPE_ZAKEN_ALLES_LEZEN,
    ]

    def test_zaak_afsluiten(self):
        zaak = ZaakFactory.create()
        zaak_url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})
        status_list_url = reverse('status-list')
        token = generate_jwt([SCOPE_STATUSSEN_TOEVOEGEN])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        # Validate StatusTypes from Mock client
        ztc_mock_client = ZTCMockClient()

        status_type_1 = ztc_mock_client.retrieve('statustype', uuid=1)
        self.assertFalse(status_type_1['isEindstatus'])

        status_type_2 = ztc_mock_client.retrieve('statustype', uuid=2)
        self.assertTrue(status_type_2['isEindstatus'])

        # Set initial status
        response = self.client.post(status_list_url, {
            'zaak': zaak_url,
            'statusType': 'http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/1',
            'datumStatusGezet': isodatetime(2018, 10, 1, 10, 00, 00),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        zaak.refresh_from_db()
        self.assertIsNone(zaak.einddatum)

        # Set eindstatus
        datum_status_gezet = utcdatetime(2018, 10, 22, 10, 00, 00)
        response = self.client.post(status_list_url, {
            'zaak': zaak_url,
            'statusType': 'http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/2',
            'datumStatusGezet': datum_status_gezet.isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        zaak.refresh_from_db()
        self.assertEqual(zaak.einddatum, datum_status_gezet.date())

    @override_settings(
        LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
        ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient'
    )
    def test_enkel_initiele_status_met_scope_aanmaken(self):
        """
        Met de scope zaken.aanmaken mag je enkel een status aanmaken als er
        nog geen status was.
        """
        zaak = ZaakFactory.create()
        zaak_url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})
        status_list_url = reverse('status-list')

        # initiele status
        response = self.client.post(status_list_url, {
            'zaak': zaak_url,
            'statusType': 'http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/1',
            'datumStatusGezet': isodatetime(2018, 10, 1, 10, 00, 00),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # extra status - mag niet, onafhankelijk van de data
        response = self.client.post(status_list_url, {
            'zaak': zaak_url,
            'statusType': 'http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/1',
            'datumStatusGezet': isodatetime(2018, 10, 1, 10, 00, 00),
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(zaak.status_set.count(), 1)

    @override_settings(
        LINK_FETCHER='vng_api_common.mocks.link_fetcher_200',
        ZDS_CLIENT_CLASS='vng_api_common.mocks.MockClient'
    )
    def test_zaak_heropen_reset_einddatum(self):
        token = generate_jwt([SCOPE_STATUSSEN_TOEVOEGEN])
        self.client.credentials(HTTP_AUTHORIZATION=token)
        zaak = ZaakFactory.create(einddatum='2019-01-07')
        StatusFactory.create(
            zaak=zaak,
            status_type='http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/2',
            datum_status_gezet='2019-01-07T12:51:41+0000',
        )
        zaak_url = reverse('zaak-detail', kwargs={'uuid': zaak.uuid})
        status_list_url = reverse('status-list')

        # Set status other than eindstatus
        datum_status_gezet = utcdatetime(2019, 1, 7, 12, 53, 25)
        response = self.client.post(status_list_url, {
            'zaak': zaak_url,
            'statusType': 'http://example.com/ztc/api/v1/catalogussen/1/zaaktypen/1/statustypen/1',
            'datumStatusGezet': datum_status_gezet.isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        zaak.refresh_from_db()
        self.assertIsNone(zaak.einddatum)

    def test_zaak_met_producten(self):
        url = reverse('zaak-list')
        token = generate_jwt(
            scopes=self.scopes + [SCOPE_ZAKEN_BIJWERKEN],
            zaaktypes=['https://example.com/zaaktype/123']
        )
        self.client.credentials(HTTP_AUTHORIZATION=token)

        responses = {
            'https://example.com/zaaktype/123': {
                'url': 'https://example.com/zaaktype/123',
                'productenOfDiensten': [
                    'https://example.com/product/123',
                    'https://example.com/dienst/123',
                ]
            }
        }

        with mock_client(responses):
            response = self.client.post(url, {
                'zaaktype': 'https://example.com/zaaktype/123',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-12-24',
                'startdatum': '2018-12-24',
                'productenOfDiensten': ['https://example.com/product/123'],
            }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        zaak = Zaak.objects.get()
        self.assertEqual(len(zaak.producten_of_diensten), 1)

        # update
        with mock_client(responses):
            response2 = self.client.patch(response.data['url'], {
                'productenOfDiensten': [
                    'https://example.com/product/123',
                    'https://example.com/dienst/123',
                ]
            }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        zaak.refresh_from_db()
        self.assertEqual(len(zaak.producten_of_diensten), 2)

    @tag('mock_client')
    def test_zaak_vertrouwelijkheidaanduiding_afgeleid(self):
        """
        Assert that the default vertrouwelijkheidaanduiding is set.
        """
        url = reverse('zaak-list')
        responses = {
            'https://ztc.nl/zaaktype/1': {
                'url': 'https://ztc.nl/zaaktype/1',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.zaakvertrouwelijk,
            }
        }

        with mock_client(responses):
            response = self.client.post(url, {
                'zaaktype': 'https://ztc.nl/zaaktype/1',
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-12-24',
                'startdatum': '2018-12-24',
            }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['vertrouwelijkheidaanduiding'],
            VertrouwelijkheidsAanduiding.zaakvertrouwelijk,
        )

    @tag('mock_client')
    def test_zaak_vertrouwelijkheidaanduiding_expliciet(self):
        """
        Assert that the default vertrouwelijkheidaanduiding is set.
        """
        url = reverse('zaak-list')
        responses = {
            'https://ztc.nl/zaaktype/2': {
                'url': 'https://ztc.nl/zaaktype/2',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.zaakvertrouwelijk,
            }
        }

        with mock_client(responses):
            response = self.client.post(url, {
                'zaaktype': 'https://ztc.nl/zaaktype/2',
                'bronorganisatie': '517439943',
                'verantwoordelijkeOrganisatie': '517439943',
                'registratiedatum': '2018-12-24',
                'startdatum': '2018-12-24',
                'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.openbaar,
            }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['vertrouwelijkheidaanduiding'],
            VertrouwelijkheidsAanduiding.openbaar,
        )

    def test_deelzaken(self):
        hoofdzaak = ZaakFactory.create()
        deelzaak = ZaakFactory.create(hoofdzaak=hoofdzaak)
        detail_url = reverse(hoofdzaak)
        deelzaak_url = reverse(deelzaak)

        token = generate_jwt(scopes=self.scopes, zaaktypes=[hoofdzaak.zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.get(detail_url, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['deelzaken'],
            [f"http://testserver{deelzaak_url}"]
        )

    def test_zaak_betalingsindicatie_nvt(self):
        zaak = ZaakFactory.create(
            betalingsindicatie=BetalingsIndicatie.gedeeltelijk,
            laatste_betaaldatum=timezone.now()
        )
        url = reverse(zaak)
        token = generate_jwt(scopes=[SCOPE_ZAKEN_BIJWERKEN], zaaktypes=[zaak.zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.patch(url, {
            'betalingsindicatie': BetalingsIndicatie.nvt,
        }, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['laatsteBetaaldatum'], None)
        zaak.refresh_from_db()
        self.assertIsNone(zaak.laatste_betaaldatum)

    def test_pagination_default(self):
        zaaktype = 'https://example.com/ztc/api/v1/zaaktypen/1234'
        ZaakFactory.create_batch(2, zaaktype=zaaktype)
        token = generate_jwt(scopes=[SCOPE_ZAKEN_ALLES_LEZEN], zaaktypes=[zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)
        url = reverse(Zaak)

        response = self.client.get(url, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['count'], 2)
        self.assertIsNone(response_data['previous'])
        self.assertIsNone(response_data['next'])

    def test_pagination_page_param(self):
        zaaktype = 'https://example.com/ztc/api/v1/zaaktypen/1234'
        ZaakFactory.create_batch(2, zaaktype=zaaktype)
        token = generate_jwt(scopes=[SCOPE_ZAKEN_ALLES_LEZEN], zaaktypes=[zaaktype])
        self.client.credentials(HTTP_AUTHORIZATION=token)
        url = reverse(Zaak)

        response = self.client.get(url, {'page': 1}, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['count'], 2)
        self.assertIsNone(response_data['previous'])
        self.assertIsNone(response_data['next'])

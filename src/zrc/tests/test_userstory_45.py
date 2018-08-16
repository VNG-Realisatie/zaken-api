"""
Als KCC medewerker wil ik een behandelaar kunnen toewijzen zodat de melding
kan worden gerouteerd.

Ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/45
"""
from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.constants import RolTypes, RolOmschrijvingGeneriek
from zds_schema.tests import TypeCheckMixin, get_operation_url

from zrc.datamodel.tests.factories import ZaakFactory


WATERNET = 'https://waternet.nl/api/organisatorische-eenheid/1234'


class US45TestCase(TypeCheckMixin, APITestCase):

    def test_zet_behandelaar(self):
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', uuid=zaak.uuid)
        url = get_operation_url('rol_create')

        response = self.client.post(url, {
            'zaak': zaak_url,
            'betrokkene': WATERNET,
            'betrokkeneType': RolTypes.organisatorische_eenheid,
            'rolomschrijving': RolOmschrijvingGeneriek.behandelaar,
            'rolomschrijvingGeneriek': RolOmschrijvingGeneriek.behandelaar,
            'roltoelichting': 'Verantwoordelijke behandelaar voor de melding',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

        response_data = response.json()
        self.assertIn('url', response_data)
        del response_data['url']
        self.assertEqual(response_data, {
            'zaak': f'http://testserver{zaak_url}',
            'betrokkene': WATERNET,
            'betrokkeneType': RolTypes.organisatorische_eenheid,
            'rolomschrijving': RolOmschrijvingGeneriek.behandelaar,
            'rolomschrijvingGeneriek': RolOmschrijvingGeneriek.behandelaar,
            'roltoelichting': 'Verantwoordelijke behandelaar voor de melding',
        })

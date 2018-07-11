"""
Als behandelaar wil ik locatie- en/of objectinformatie bij de melding
ontvangen, zodat ik voldoende details weet om de melding op te volgen.

ref: https://github.com/VNG-Realisatie/gemma-zaken/issues/52
"""
from rest_framework import status
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

from zrc.datamodel.models import ZaakEigenschap
from zrc.datamodel.tests.factories import ZaakFactory

EIGENSCHAP_OBJECTTYPE = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/eigenschappen/1'
EIGENSCHAP_NAAM_BOOT = 'https://example.com/ztc/api/v1/catalogus/1/zaaktypen/1/eigenschappen/2'


class US52TestCase(APITestCase):

    def test_zet_eigenschappen(self):
        url = get_operation_url('zaakeigenschap_create')
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url('zaak_read', id=zaak.id)
        data = {
            'zaak': zaak_url,
            'eigenschap': EIGENSCHAP_OBJECTTYPE,
            'waarde': 'overlast_water'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        zaakeigenschap = ZaakEigenschap.objects.get()
        self.assertEqual(zaakeigenschap.zaak, zaak)
        detail_url = get_operation_url('zaakeigenschap_read', id=zaakeigenschap.id)
        self.assertEqual(
            response_data,
            {
                'url': f"http://testserver{detail_url}",
                'zaak': f"http://testserver{zaak_url}",
                'eigenschap': EIGENSCHAP_OBJECTTYPE,
                'waarde': 'overlast_water'
            }
        )

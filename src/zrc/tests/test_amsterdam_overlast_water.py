from django.test import override_settings

from dateutil import parser
from rest_framework.test import APITestCase
from zds_schema.tests import get_operation_url

from zrc.datamodel.models import Zaak

from .test_userstory_39 import (
    STATUS_TYPE, STATUS_TYPE_OVERLAST_GECONSTATEERD,
    VERANTWOORDELIJKE_ORGANISATIE, ZAAKTYPE
)
from .test_userstory_52 import EIGENSCHAP_NAAM_BOOT, EIGENSCHAP_OBJECTTYPE
from .utils import utcdatetime

TEST_DATA = {
    "id": 9966,
    "last_status": "o",
    "adres": "Oosterdok 51, 1011 Amsterdam, Netherlands",
    "datetime": "2018-05-28T09:05:08.732587+02:00",
    "text": "test",
    "waternet_soort_boot": "Nee",
    "waternet_rederij": "Onbekend",
    "waternet_naam_boot": "De Amsterdam",
    "datetime_overlast": "2018-05-28T08:35:11+02:00",
    "email": "",
    "phone_number": "",
    "source": "Telefoon 14020",
    "text_extra": "",
    "image": None,
    "main_category": "",
    "sub_category": "Geluid",
    "ml_cat": "melding openbare ruimte",
    "stadsdeel": "Centrum",
    "coordinates": "POINT (4.910649523925713 52.37240093589432)",
    "verantwoordelijk": "Waternet"
}


class Application:

    def __init__(self, client, data: dict):
        self.client = client

        self.data = data
        self.references = {}

    def store_notification(self):
        # registreer zaak & zet statussen
        self.registreer_zaak()
        self.zet_statussen()
        self.registreer_domein_data()
        self.registreer_klantcontact()

    def registreer_zaak(self):
        zaak_create_url = get_operation_url('zaak_create')

        created = parser.parse(self.data['datetime'])
        intern_id = self.data['id']

        response = self.client.post(zaak_create_url, {
            'zaaktype': ZAAKTYPE,
            'bronorganisatie': '517439943',
            'verantwoordelijkeOrganisatie': VERANTWOORDELIJKE_ORGANISATIE,
            'identificatie': f'WATER_{intern_id}',
            'registratiedatum': created.strftime('%Y-%m-%d'),
            'startdatum': created.strftime('%Y-%m-%d'),
            'toelichting': self.data['text'],
            'zaakgeometrie': self.data['coordinates'],
        }, HTTP_ACCEPT_CRS='EPSG:4326')
        self.references['zaak_url'] = response.json()['url']

    def zet_statussen(self):
        status_create_url = get_operation_url('status_create')

        created = parser.parse(self.data['datetime'])

        self.client.post(status_create_url, {
            'zaak': self.references['zaak_url'],
            'statusType': STATUS_TYPE,
            'datumStatusGezet': created.isoformat(),
        })

        self.client.post(status_create_url, {
            'zaak': self.references['zaak_url'],
            'statusType': STATUS_TYPE_OVERLAST_GECONSTATEERD,
            'datumStatusGezet': parser.parse(self.data['datetime_overlast']).isoformat(),
        })

    def registreer_domein_data(self):
        zaak_uuid = self.references['zaak_url'].rsplit('/')[-1]
        url = get_operation_url('zaakeigenschap_create', zaak_uuid=zaak_uuid)
        self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'eigenschap': EIGENSCHAP_OBJECTTYPE,
            'waarde': 'overlast_water',
        })
        self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'eigenschap': EIGENSCHAP_NAAM_BOOT,
            'waarde': TEST_DATA['waternet_naam_boot'],
        })

    def registreer_klantcontact(self):
        url = get_operation_url('klantcontact_create')
        self.client.post(url, {
            'zaak': self.references['zaak_url'],
            'datumtijd': self.data['datetime'],
            'kanaal': self.data['source'],
        })


@override_settings(LINK_FETCHER='zrc.api.tests.mocks.link_fetcher_200')
class US39IntegrationTestCase(APITestCase):
    """
    Simulate a full realistic flow.
    """

    def test_full_flow(self):
        app = Application(self.client, TEST_DATA)

        app.store_notification()

        zaak = Zaak.objects.get(identificatie='WATER_9966')
        self.assertEqual(zaak.toelichting, 'test')
        self.assertEqual(zaak.zaakgeometrie.x, 4.910649523925713)
        self.assertEqual(zaak.zaakgeometrie.y, 52.37240093589432)

        self.assertEqual(zaak.status_set.count(), 2)

        last_status = zaak.status_set.order_by('-datum_status_gezet').first()
        self.assertEqual(last_status.status_type, STATUS_TYPE)
        self.assertEqual(
            last_status.datum_status_gezet,
            utcdatetime(2018, 5, 28, 7, 5, 8, 732587),
        )

        first_status = zaak.status_set.order_by('datum_status_gezet').first()
        self.assertEqual(first_status.status_type, STATUS_TYPE_OVERLAST_GECONSTATEERD)
        self.assertEqual(
            first_status.datum_status_gezet,
            utcdatetime(2018, 5, 28, 6, 35, 11)
        )

        klantcontact = zaak.klantcontact_set.get()
        self.assertEqual(klantcontact.kanaal, 'Telefoon 14020')
        self.assertEqual(
            klantcontact.datumtijd,
            utcdatetime(2018, 5, 28, 7, 5, 8, 732587),
        )

        eigenschappen = zaak.zaakeigenschap_set.all()
        self.assertEqual(eigenschappen.count(), 2)
        naam_boot = eigenschappen.get(eigenschap=EIGENSCHAP_NAAM_BOOT)
        self.assertEqual(naam_boot.waarde, 'De Amsterdam')

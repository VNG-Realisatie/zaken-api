from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import tag

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import JWTAuthMixin, get_operation_url, reverse

from zrc.datamodel.tests.factories import (
    ResultaatFactory,
    StatusFactory,
    ZaakEigenschapFactory,
    ZaakFactory,
)
from zrc.tests.constants import POLYGON_AMSTERDAM_CENTRUM
from zrc.tests.utils import ZAAK_READ_KWARGS, ZAAK_WRITE_KWARGS

from .utils import (
    get_catalogus_response,
    get_eigenschap_response,
    get_resultaattype_response,
    get_statustype_response,
    get_zaaktype_response,
)

ZAAKTYPE = (
    "https://externe.catalogus.nl/api/v1/zaaktypen/b71f72ef-198d-44d8-af64-ae1932df830a"
)
CATALOGUS = "https://externe.catalogus.nl/api/v1/catalogussen/1c8e36be-338c-4c07-ac5e-1adf55bec04a"
RESULTAATTYPE = "https://externe.catalogus.nl/api/v1/resultaattypen/309b0a3c-f198-4f09-bad9-d804486d6e02"
STATUSTYPE = "https://externe.catalogus.nl/api/v1/statustypen/f3663a5d-d395-42c9-87db-5512a7a4ad08"
EIGENSCHAP = "https://externe.catalogus.nl/api/v1/eigenschappen/e02d9200-a891-45f9-9d29-93cc5e809db3"


@tag("inclusions")
class ZakenIncludeTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True
    maxDiff = None

    @patch("zds_client.client.Client.schema", return_value={})
    def test_zaak_list_include(self, *m):
        """
        Test if related resources that are external can be included
        """
        zaaktype_data = get_zaaktype_response(CATALOGUS, ZAAKTYPE)
        catalogus_data = get_catalogus_response(CATALOGUS, ZAAKTYPE)

        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE)

        zaak_data = self.client.get(reverse(zaak), **ZAAK_READ_KWARGS).json()

        url = reverse("zaak-list")

        with requests_mock.Mocker() as m:
            m.get(ZAAKTYPE, json=zaaktype_data)
            m.get(CATALOGUS, json=catalogus_data)
            response = self.client.get(
                url,
                {"include": "zaaktype"},
                **ZAAK_READ_KWARGS,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = response.json()

        self.assertEqual(data["results"], [zaak_data])
        self.assertIn("inclusions", data)
        self.assertEqual(data["inclusions"], {"catalogi:zaaktype": [zaaktype_data]})

    @patch("zds_client.client.Client.schema", return_value={})
    def test_zaak_zoek_include(self, *m):
        """
        Test if related resources that are in the local database can be included
        """
        zaaktype_data = get_zaaktype_response(CATALOGUS, ZAAKTYPE)
        catalogus_data = get_catalogus_response(CATALOGUS, ZAAKTYPE)

        hoofdzaak = ZaakFactory(zaaktype=ZAAKTYPE)
        zaak = ZaakFactory.create(
            zaaktype=ZAAKTYPE,
            hoofdzaak=hoofdzaak,
            zaakgeometrie=Point(4.887990, 52.377595),
        )
        zaak_status = StatusFactory(zaak=zaak)
        resultaat = ResultaatFactory(zaak=zaak)
        eigenschap = ZaakEigenschapFactory(zaak=zaak)

        url = get_operation_url("zaak__zoek")

        zaak_data = self.client.get(reverse(zaak), **ZAAK_READ_KWARGS).json()
        hoofdzaak_data = self.client.get(reverse(hoofdzaak), **ZAAK_READ_KWARGS).json()
        status_data = self.client.get(reverse(zaak_status)).json()
        resultaat_data = self.client.get(reverse(resultaat)).json()
        eigenschap_data = self.client.get(
            reverse(eigenschap, kwargs={"zaak_uuid": zaak.uuid})
        ).json()

        with requests_mock.Mocker() as m:
            m.get(ZAAKTYPE, json=zaaktype_data)
            m.get(CATALOGUS, json=catalogus_data)
            response = self.client.post(
                url,
                {
                    "zaakgeometrie": {
                        "within": {
                            "type": "Polygon",
                            "coordinates": [POLYGON_AMSTERDAM_CENTRUM],
                        }
                    },
                    "include": [
                        "hoofdzaak",
                        "zaaktype",
                        "status",
                        "resultaat",
                        "eigenschappen",
                    ],
                },
                **ZAAK_WRITE_KWARGS,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = response.json()

        expected = {
            "zaken:zaak": [hoofdzaak_data],
            "catalogi:zaaktype": [zaaktype_data],
            "zaken:resultaat": [resultaat_data],
            "zaken:status": [status_data],
            "zaken:zaakeigenschap": [eigenschap_data],
        }

        self.assertEqual(data["results"], [zaak_data])
        self.assertIn("inclusions", data)
        self.assertEqual(data["inclusions"], expected)

    @patch("zds_client.client.Client.schema", return_value={})
    def test_zaak_list_include_wildcard(self, *m):
        """
        Test if all related resources that are in the local database can be included
        with a wildcard
        """
        # Explicitly set a UUID, because the ordering of inclusions seems a bit funky
        hoofdzaak = ZaakFactory(
            zaaktype=ZAAKTYPE, uuid="da0e1b14-bdc8-466b-b145-a0c49081a466"
        )
        hoofdzaak_status = StatusFactory(
            statustype=STATUSTYPE,
            zaak=hoofdzaak,
            uuid="da0e1b14-bdc8-466b-b145-a0c49081a466",
        )
        hoofdzaak_resultaat = ResultaatFactory(
            resultaattype=RESULTAATTYPE,
            zaak=hoofdzaak,
            uuid="da0e1b14-bdc8-466b-b145-a0c49081a466",
        )
        hoofdzaak_eigenschap = ZaakEigenschapFactory(
            eigenschap=EIGENSCHAP, zaak=hoofdzaak
        )

        zaak = ZaakFactory.create(
            zaaktype=ZAAKTYPE,
            hoofdzaak=hoofdzaak,
            uuid="bedc3f70-bcb9-4ee7-b3c8-1782c3dd8707",
        )
        zaak_status = StatusFactory(
            zaak=zaak,
            statustype=STATUSTYPE,
            uuid="bedc3f70-bcb9-4ee7-b3c8-1782c3dd8707",
        )
        resultaat = ResultaatFactory(
            zaak=zaak,
            resultaattype=RESULTAATTYPE,
            uuid="bedc3f70-bcb9-4ee7-b3c8-1782c3dd8707",
        )
        eigenschap = ZaakEigenschapFactory(zaak=zaak, eigenschap=EIGENSCHAP)

        url = reverse("zaak-list")

        hoofdzaak_data = self.client.get(reverse(hoofdzaak), **ZAAK_READ_KWARGS).json()
        hoofdzaak_status_data = self.client.get(reverse(hoofdzaak_status)).json()
        hoofdzaak_resultaat_data = self.client.get(reverse(hoofdzaak_resultaat)).json()
        hoofdzaak_zaakeigenschap_data = self.client.get(
            reverse(hoofdzaak_eigenschap, kwargs={"zaak_uuid": hoofdzaak.uuid})
        ).json()

        zaak_data = self.client.get(reverse(zaak), **ZAAK_READ_KWARGS).json()
        status_data = self.client.get(reverse(zaak_status)).json()
        resultaat_data = self.client.get(reverse(resultaat)).json()
        zaakeigenschap_data = self.client.get(
            reverse(eigenschap, kwargs={"zaak_uuid": zaak.uuid})
        ).json()

        # catalogus_data = get_catalogus_response(CATALOGUS, ZAAKTYPE)
        zaaktype_data = get_zaaktype_response(CATALOGUS, ZAAKTYPE)
        zaak_resultaattype_data = get_resultaattype_response(CATALOGUS, RESULTAATTYPE)
        zaak_statustype_data = get_statustype_response(CATALOGUS, STATUSTYPE)
        zaak_eigenschap_data = get_eigenschap_response(CATALOGUS, EIGENSCHAP)

        with requests_mock.Mocker() as m:
            m.get(ZAAKTYPE, json=zaaktype_data)
            m.get(STATUSTYPE, json=zaak_statustype_data)
            m.get(RESULTAATTYPE, json=zaak_resultaattype_data)
            m.get(EIGENSCHAP, json=zaak_eigenschap_data)
            response = self.client.get(url, {"include": "*"}, **ZAAK_READ_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = response.json()

        expected = {
            "zaken:zaak": [zaak_data, hoofdzaak_data],
            "zaken:resultaat": [resultaat_data, hoofdzaak_resultaat_data],
            "zaken:status": [status_data, hoofdzaak_status_data],
            "zaken:zaakeigenschap": [
                zaakeigenschap_data,
                hoofdzaak_zaakeigenschap_data,
            ],
            "catalogi:zaaktype": [zaaktype_data],
            "catalogi:statustype": [zaak_statustype_data],
            "catalogi:resultaattype": [zaak_resultaattype_data],
            "catalogi:eigenschap": [zaak_eigenschap_data],
        }

        self.assertEqual(data["results"], [zaak_data, hoofdzaak_data])
        self.assertIn("inclusions", data)
        self.assertEqual(data["inclusions"], expected)

    @patch("zds_client.client.Client.schema", return_value={})
    def test_zaak_list_include_nested(self, *m):
        """
        Test if nested related resources that are external can be included
        """
        hoofdzaak = ZaakFactory.create(zaaktype=ZAAKTYPE)
        zaak = ZaakFactory.create(zaaktype=ZAAKTYPE, hoofdzaak=hoofdzaak)

        url = reverse("zaak-list")

        zaak_data = self.client.get(reverse(zaak), **ZAAK_READ_KWARGS).json()
        hoofdzaak_data = self.client.get(reverse(hoofdzaak), **ZAAK_READ_KWARGS).json()
        catalogus_data = get_catalogus_response(CATALOGUS, ZAAKTYPE)
        zaaktype_data = get_zaaktype_response(CATALOGUS, ZAAKTYPE)

        with requests_mock.Mocker() as m:
            m.get(ZAAKTYPE, json=zaaktype_data)
            m.get(CATALOGUS, json=catalogus_data)
            response = self.client.get(
                url,
                {"include": "hoofdzaak,hoofdzaak.zaaktype"},
                **ZAAK_READ_KWARGS,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = response.json()

        self.assertEqual(data["results"], [zaak_data, hoofdzaak_data])
        self.assertIn("inclusions", data)
        self.assertEqual(
            data["inclusions"],
            {
                "zaken:zaak": [hoofdzaak_data],
                "catalogi:zaaktype": [zaaktype_data],
            },
        )

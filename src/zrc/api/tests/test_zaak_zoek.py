import datetime

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import (
    Archiefnominatie,
    Archiefstatus,
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduiding,
)
from vng_api_common.tests import (
    JWTAuthMixin,
    TypeCheckMixin,
    get_operation_url,
    get_validation_errors,
    reverse,
)

from zrc.datamodel.constants import IndicatieMachtiging
from zrc.datamodel.models import NatuurlijkPersoon, OrganisatorischeEenheid
from zrc.datamodel.tests.factories import RolFactory, ZaakFactory
from zrc.tests.utils import ZAAK_WRITE_KWARGS


class ZaakZoekTests(JWTAuthMixin, TypeCheckMixin, APITestCase):
    heeft_alle_autorisaties = True

    def test_zoek_uuid_in(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")
        data = {"uuid__in": [zaak1.uuid, zaak2.uuid]}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]
        data = sorted(data, key=lambda zaak: zaak["identificatie"])

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["url"], f"http://testserver{reverse(zaak1)}")
        self.assertEqual(data[1]["url"], f"http://testserver{reverse(zaak2)}")

    def test_zoek_identificatie(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")
        data = {"identificatie": zaak2.identificatie}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["identificatie"], zaak2.identificatie)

    def test_zoek_bronorganisatie(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        data = {"bronorganisatie": zaak2.bronorganisatie}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["bronorganisatie"], zaak2.bronorganisatie)

    def test_zoek_zaaktype(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        data = {"zaaktype": zaak3.zaaktype}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["zaaktype"], zaak3.zaaktype)

    def test_zoek_archiefnominatie(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")

        zaak2.archiefnominatie = Archiefnominatie.vernietigen
        zaak1.archiefnominatie = Archiefnominatie.blijvend_bewaren
        zaak2.save()
        zaak1.save()

        data = {"archiefnominatie": zaak1.archiefnominatie}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["archiefnominatie"], zaak1.archiefnominatie)

    def test_zoek_archiefnominatie__in(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak2.archiefnominatie = Archiefnominatie.blijvend_bewaren
        zaak1.archiefnominatie = Archiefnominatie.blijvend_bewaren
        zaak3.archiefnominatie = Archiefnominatie.vernietigen
        zaak2.save()
        zaak1.save()

        data = {
            "archiefnominatie__in": [zaak1.archiefnominatie, zaak2.archiefnominatie]
        }
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]
        data = sorted(data, key=lambda zaak: zaak["identificatie"])

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["archiefnominatie"], zaak1.archiefnominatie)
        self.assertEqual(data[1]["archiefnominatie"], zaak2.archiefnominatie)

    def test_zoek_archiefactiedatum(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak1.archiefactiedatum = datetime.datetime(1900, 1, 15).date()
        zaak2.archiefactiedatum = datetime.datetime(1900, 2, 15).date()
        zaak3.archiefactiedatum = datetime.datetime(1900, 3, 15).date()
        zaak1.save()
        zaak2.save()
        zaak3.save()

        data = {"archiefactiedatum": zaak2.archiefactiedatum}
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["archiefactiedatum"], str(zaak2.archiefactiedatum))

    def test_zoek_archiefactiedatum__lt(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak1.archiefactiedatum = datetime.datetime(1900, 1, 15).date()
        zaak2.archiefactiedatum = datetime.datetime(1900, 2, 15).date()
        zaak3.archiefactiedatum = datetime.datetime(1900, 3, 15).date()
        zaak1.save()
        zaak2.save()
        zaak3.save()

        data = {"archiefactiedatum__lt": zaak2.archiefactiedatum}
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["archiefactiedatum"], str(zaak1.archiefactiedatum))

    def test_zoek_archiefactiedatum__gt(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak1.archiefactiedatum = datetime.datetime(1900, 1, 15).date()
        zaak2.archiefactiedatum = datetime.datetime(1900, 2, 15).date()
        zaak3.archiefactiedatum = datetime.datetime(1900, 3, 15).date()
        zaak1.save()
        zaak2.save()
        zaak3.save()

        data = {"archiefactiedatum__gt": zaak2.archiefactiedatum}
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["archiefactiedatum"], str(zaak3.archiefactiedatum))

    def test_zoek_archiefstatus(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")

        zaak1.archiefstatus = Archiefstatus.gearchiveerd
        zaak2.archiefstatus = Archiefstatus.nog_te_archiveren

        zaak1.save()
        zaak2.save()

        data = {"archiefstatus": zaak2.archiefstatus}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["archiefstatus"], zaak2.archiefstatus)

    def test_zoek_archiefstatus__in(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak1.archiefstatus = Archiefstatus.gearchiveerd
        zaak2.archiefstatus = Archiefstatus.nog_te_archiveren
        zaak3.archiefstatus = Archiefstatus.gearchiveerd

        zaak1.save()
        zaak2.save()
        zaak3.save()

        data = {"archiefstatus__in": [zaak1.archiefstatus, zaak3.archiefstatus]}
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]
        data = sorted(data, key=lambda zaak: zaak["identificatie"])

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["archiefstatus"], zaak1.archiefstatus)
        self.assertEqual(data[1]["archiefstatus"], zaak3.archiefstatus)

    def test_zoek_startdatum(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")

        zaak1.startdatum = datetime.datetime(1900, 1, 15).date()
        zaak2.startdatum = datetime.datetime(1900, 2, 15).date()
        zaak3.startdatum = datetime.datetime(1900, 3, 15).date()
        zaak1.save()
        zaak2.save()
        zaak3.save()
        query_params = [
            "startdatum",
            "startdatum__gt",
            "startdatum__gte",
            "startdatum__lt",
            "startdatum__lte",
        ]
        assert_equals = [
            zaak2.startdatum,
            zaak3.startdatum,
            [zaak2.startdatum, zaak3.startdatum],
            zaak1.startdatum,
            [zaak1.startdatum, zaak2.startdatum],
        ]
        for query_param, equals in zip(query_params, assert_equals):
            with self.subTest(query_param=query_param, equals=equals):
                data = {query_param: zaak2.startdatum}
                response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                data = response.json()["results"]
                data = sorted(data, key=lambda zaak: zaak["identificatie"])
                if not isinstance(equals, list):
                    self.assertEqual(len(data), 1)
                    self.assertEqual(data[0]["startdatum"], str(equals))
                else:
                    self.assertEqual(len(data), 2)
                    self.assertEqual(data[0]["startdatum"], str(equals[0]))
                    self.assertEqual(data[1]["startdatum"], str(equals[1]))

    def test_zoek_rol__betrokkene_type(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")
        rol1 = RolFactory.create(
            zaak=zaak1,
            betrokkene_type=RolTypes.natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek="Beslisser",
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        rol2 = RolFactory.create(
            zaak=zaak2,
            betrokkene_type=RolTypes.niet_natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek="Beslisser",
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )

        data = {"rol__betrokkene_type": rol1.betrokkene_type}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["uuid"], str(rol1.zaak.uuid))

    def test_zoek_rol__betrokkene(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")
        rol1 = RolFactory.create(
            zaak=zaak1,
            betrokkene_type=RolTypes.natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek="Beslisser",
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        rol2 = RolFactory.create(
            zaak=zaak2,
            betrokkene_type=RolTypes.niet_natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/fdswe581-4325-kdfs-slkf-37af92d819ff",
            omschrijving="Beslisser",
            omschrijving_generiek="Beslisser",
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )

        data = {"rol__betrokkene": rol2.betrokkene}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["uuid"], str(rol2.zaak.uuid))

    def test_zoek_rol__omschrijving_generiek(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")
        rol1 = RolFactory.create(
            zaak=zaak1,
            betrokkene_type=RolTypes.natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.adviseur,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        rol2 = RolFactory.create(
            zaak=zaak2,
            betrokkene_type=RolTypes.niet_natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/fdswe581-4325-kdfs-slkf-37af92d819ff",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.behandelaar,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )

        data = {"rol__omschrijving_generiek": rol1.omschrijving_generiek}

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["uuid"], str(rol1.zaak.uuid))

    def test_zoek_maximale_vertrouwelijkheidaanduidingn(self):
        zaak1, zaak2, zaak3 = ZaakFactory.create_batch(3)
        url = get_operation_url("zaak__zoek")
        zaak2.vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduiding.openbaar
        zaak2.save()

        data = {
            "maximale_vertrouwelijkheidaanduiding": zaak2.vertrouwelijkheidaanduiding
        }
        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["vertrouwelijkheidaanduiding"], zaak2.vertrouwelijkheidaanduiding
        )

    def test_zoek_rol__betrokkene_identificatie__natuurlijk_persoon__inp_bsn(self):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")
        rol1 = RolFactory.create(
            zaak=zaak1,
            betrokkene_type=RolTypes.natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.adviseur,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        rol2 = RolFactory.create(
            zaak=zaak2,
            betrokkene_type=RolTypes.niet_natuurlijk_persoon,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/fdswe581-4325-kdfs-slkf-37af92d819ff",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.behandelaar,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        natuurlijkpersoon = NatuurlijkPersoon.objects.create(
            rol=rol1,
            anp_identificatie="12345",
            inp_a_nummer="1234567890",
            inp_bsn="183068142",
        )
        natuurlijkpersoon2 = NatuurlijkPersoon.objects.create(
            rol=rol2,
            anp_identificatie="56789",
            inp_a_nummer="2134554323",
            inp_bsn="121344242",
        )

        data = {
            "rol__betrokkene_identificatie__natuurlijk_persoon__inp_bsn": natuurlijkpersoon.inp_bsn
        }

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["uuid"], str(rol1.zaak.uuid))

    def test_zoek_rol_betrokkene_identificatie__organisatorische_eenheid__identificatie(
        self,
    ):
        zaak1, zaak2 = ZaakFactory.create_batch(2)
        url = get_operation_url("zaak__zoek")
        rol1 = RolFactory.create(
            zaak=zaak1,
            betrokkene_type=RolTypes.organisatorische_eenheid,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/8768c581-2817-4fe5-933d-37af92d819dd",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.adviseur,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        rol2 = RolFactory.create(
            zaak=zaak2,
            betrokkene_type=RolTypes.organisatorische_eenheid,
            betrokkene="http://www.zamora-silva.org/api/betrokkene/fdswe581-4325-kdfs-slkf-37af92d819ff",
            omschrijving="Beslisser",
            omschrijving_generiek=RolOmschrijving.behandelaar,
            indicatie_machtiging=IndicatieMachtiging.gemachtigde,
        )
        oe1 = OrganisatorischeEenheid.objects.create(
            rol=rol1,
            identificatie="some-id1",
        )
        oe2 = OrganisatorischeEenheid.objects.create(
            rol=rol2,
            identificatie="some-id2",
        )
        data = {
            "rol__betrokkene_identificatie__organisatorische_eenheid__identificatie": oe2.identificatie
        }

        response = self.client.post(url, data, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["uuid"], str(rol2.zaak.uuid))

    def test_zoek_without_params(self):
        url = get_operation_url("zaak__zoek")

        response = self.client.post(url, {}, **ZAAK_WRITE_KWARGS)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["code"], "empty_search_body")

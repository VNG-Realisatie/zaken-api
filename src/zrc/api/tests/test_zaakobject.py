from django.test import override_settings, tag

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import ZaakobjectTypes
from vng_api_common.tests import JWTAuthMixin, get_operation_url, get_validation_errors

from zrc.datamodel.models import (
    Adres,
    Huishouden,
    KadastraleOnroerendeZaak,
    Medewerker,
    NatuurlijkPersoon,
    NietNatuurlijkPersoon,
    Overige,
    TerreinGebouwdObject,
    WozDeelobject,
    WozObject,
    WozWaarde,
    ZaakObject,
    ZakelijkRecht,
    ZakelijkRechtHeeftAlsGerechtigde,
)
from zrc.datamodel.tests.factories import ZaakFactory, ZaakObjectFactory

OBJECT = "http://example.org/api/zaakobjecten/8768c581-2817-4fe5-933d-37af92d819dd"
ZAAKOBJECTTYPE = 'http://testserver/api/v1/zaakobjecttypen/c340323d-31a5-46b4-93e8-fdc2d621be13'

class ZaakObjectBaseTestCase(JWTAuthMixin, APITestCase):
    """
    general cases for zaakobject without object_identificatie
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_without_identificatie(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object=OBJECT, object_type=ZaakobjectTypes.besluit
        )
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": OBJECT,
                "objectType": ZaakobjectTypes.besluit,
                "objectTypeOverige": "",
                "relatieomschrijving": "",
                "objectTypeOverigeDefinitie": None,
            },
        )

    @override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
    def test_create_zaakobject_without_identificatie(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": OBJECT,
            "objectType": ZaakobjectTypes.besluit,
            "relatieomschrijving": "test",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()

        self.assertEqual(zaakobject.object, OBJECT)

    def test_create_zaakobject_fail_validation(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.besluit,
            "relatieomschrijving": "test",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        validation_error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(validation_error["code"], "invalid-zaakobject")

    def test_update_zaakobject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object=OBJECT, object_type=ZaakobjectTypes.besluit
        )
        print(zaak.__dict__)
        print(zaakobject.__dict__)
        url = get_operation_url("zaakobject_update", uuid=zaakobject.uuid)
        data = {"relatieomschrijving": "new"}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()

        self.assertEqual(zaakobject.relatieomschrijving, "new")

    def test_update_zaakobject_fail_immuitable_field(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object=OBJECT, object_type=ZaakobjectTypes.besluit
        )
        url = get_operation_url("zaakobject_update", uuid=zaakobject.uuid)
        data = {"objectType": ZaakobjectTypes.adres}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        validation_error = get_validation_errors(response, "objectType")
        self.assertEqual(validation_error["code"], "wijzigen-niet-toegelaten")

    def test_delete_zaakobject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object=OBJECT, object_type=ZaakobjectTypes.besluit
        )
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ZaakObject.objects.count(), 0)


class ZaakObjectAdresTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism with simple child object Adres
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_adres(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.adres
        )
        Adres.objects.create(
            zaakobject=zaakobject,
            identificatie="123456",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer=1,
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.adres,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "identificatie": "123456",
                    "wplWoonplaatsNaam": "test city",
                    "gorOpenbareRuimteNaam": "test space",
                    "huisnummer": 1,
                    "huisletter": "",
                    "huisnummertoevoeging": "",
                    "postcode": "",
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_adres(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.adres,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "identificatie": "123456",
                "wplWoonplaatsNaam": "test city",
                "gorOpenbareRuimteNaam": "test space",
                "huisnummer": 1,
                "huisletter": "",
                "huisnummertoevoeging": "",
                "postcode": "",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(Adres.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        adres = Adres.objects.get()

        self.assertEqual(zaakobject.adres, adres)
        self.assertEqual(adres.identificatie, "123456")

    def test_update_zaakobject_adres(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.adres
        )
        Adres.objects.create(
            zaakobject=zaakobject,
            identificatie="old",
            wpl_woonplaats_naam="old city",
            gor_openbare_ruimte_naam="old space",
            huisnummer=1,
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)
        data = {
            "objectIdentificatie": {
                "identificatie": "new",
                "wplWoonplaatsNaam": "new city",
                "gorOpenbareRuimteNaam": "new space",
                "huisnummer": 2,
            }
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()
        adres = zaakobject.adres

        self.assertEqual(adres.identificatie, "new")
        self.assertEqual(adres.wpl_woonplaats_naam, "new city")
        self.assertEqual(adres.gor_openbare_ruimte_naam, "new space")
        self.assertEqual(adres.huisnummer, 2)

    def test_delete_zaakobject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.adres
        )
        Adres.objects.create(
            zaakobject=zaakobject,
            identificatie="old",
            wpl_woonplaats_naam="old city",
            gor_openbare_ruimte_naam="old space",
            huisnummer=1,
        )
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ZaakObject.objects.count(), 0)


class ZaakObjectHuishoudenTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for Huishouden object with nesting
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_huishouden(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.huishouden
        )

        huishouden = Huishouden.objects.create(zaakobject=zaakobject, nummer="123456")
        terreingebouwdobject = TerreinGebouwdObject.objects.create(
            huishouden=huishouden, identificatie="1"
        )
        Adres.objects.create(
            terreingebouwdobject=terreingebouwdobject,
            num_identificatie="1",
            identificatie="a",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer="11",
            locatie_aanduiding="test",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.huishouden,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "nummer": "123456",
                    "isGehuisvestIn": {
                        "identificatie": "1",
                        "adresAanduidingGrp": {
                            "numIdentificatie": "1",
                            "oaoIdentificatie": "a",
                            "wplWoonplaatsNaam": "test city",
                            "gorOpenbareRuimteNaam": "test space",
                            "aoaPostcode": "",
                            "aoaHuisnummer": 11,
                            "aoaHuisletter": "",
                            "aoaHuisnummertoevoeging": "",
                            "ogoLocatieAanduiding": "test",
                        },
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_huishouden(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.huishouden,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "nummer": "123456",
                "isGehuisvestIn": {
                    "identificatie": "1",
                    "adresAanduidingGrp": {
                        "numIdentificatie": "1",
                        "oaoIdentificatie": "a",
                        "wplWoonplaatsNaam": "test city",
                        "gorOpenbareRuimteNaam": "test space",
                        "aoaPostcode": "1010",
                        "aoaHuisnummer": 11,
                        "aoaHuisletter": "a",
                        "aoaHuisnummertoevoeging": "test",
                        "ogoLocatieAanduiding": "test",
                    },
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(Huishouden.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        huishouden = Huishouden.objects.get()

        self.assertEqual(zaakobject.huishouden, huishouden)
        self.assertEqual(huishouden.nummer, "123456")
        self.assertEqual(
            huishouden.is_gehuisvest_in.adres_aanduiding_grp.identificatie, "a"
        )


class ZaakObjectMedewerkerTestCase(JWTAuthMixin, APITestCase):
    """
    check polyphormism for Rol-related object Medewerker
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_medewerker(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.medewerker
        )
        Medewerker.objects.create(
            zaakobject=zaakobject,
            identificatie="123456",
            achternaam="Jong",
            voorletters="J",
            voorvoegsel_achternaam="van",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.medewerker,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "identificatie": "123456",
                    "achternaam": "Jong",
                    "voorletters": "J",
                    "voorvoegselAchternaam": "van",
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_medewerker(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.medewerker,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "identificatie": "123456",
                "achternaam": "Jong",
                "voorletters": "J",
                "voorvoegselAchternaam": "van",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(Medewerker.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        medewerker = Medewerker.objects.get()

        self.assertEqual(zaakobject.medewerker, medewerker)
        self.assertEqual(medewerker.identificatie, "123456")

    def test_update_zaakobject_medewerker(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.medewerker
        )
        Medewerker.objects.create(
            zaakobject=zaakobject,
            identificatie="old",
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)
        data = {
            "objectIdentificatie": {
                "identificatie": "new",
            }
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()
        self.assertEqual(zaakobject.medewerker.identificatie, "new")


class ZaakObjectTerreinGebouwdObjectTestCase(JWTAuthMixin, APITestCase):
    """
    check polyphormism for object TerreinGebouwdObject with GegevensGroep
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_terreinGebouwdObject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.terrein_gebouwd_object
        )

        terreingebouwdobject = TerreinGebouwdObject.objects.create(
            zaakobject=zaakobject, identificatie="12345"
        )
        Adres.objects.create(
            terreingebouwdobject=terreingebouwdobject,
            num_identificatie="1",
            identificatie="123",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer="11",
            locatie_aanduiding="test",
        )
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.terrein_gebouwd_object,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "identificatie": "12345",
                    "adresAanduidingGrp": {
                        "numIdentificatie": "1",
                        "oaoIdentificatie": "123",
                        "wplWoonplaatsNaam": "test city",
                        "gorOpenbareRuimteNaam": "test space",
                        "aoaPostcode": "",
                        "aoaHuisnummer": 11,
                        "aoaHuisletter": "",
                        "aoaHuisnummertoevoeging": "",
                        "ogoLocatieAanduiding": "test",
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_terreinGebouwdObject(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.terrein_gebouwd_object,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "identificatie": "12345",
                "adresAanduidingGrp": {
                    "numIdentificatie": "1",
                    "oaoIdentificatie": "a",
                    "wplWoonplaatsNaam": "test city",
                    "gorOpenbareRuimteNaam": "test space",
                    "aoaPostcode": "1010",
                    "aoaHuisnummer": 11,
                    "aoaHuisletter": "a",
                    "aoaHuisnummertoevoeging": "test",
                    "ogoLocatieAanduiding": "test",
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(TerreinGebouwdObject.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        terrein_gebouwd = TerreinGebouwdObject.objects.get()
        adres = Adres.objects.get()

        self.assertEqual(zaakobject.terreingebouwdobject, terrein_gebouwd)
        self.assertEqual(terrein_gebouwd.identificatie, "12345")
        self.assertEqual(terrein_gebouwd.adres_aanduiding_grp, adres)
        self.assertEqual(adres.identificatie, "a")


class ZaakObjectWozObjectTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for WozObject object with GegevensGroep
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_wozObject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.woz_object
        )

        wozobject = WozObject.objects.create(
            zaakobject=zaakobject, woz_object_nummer="12345"
        )
        Adres.objects.create(
            wozobject=wozobject,
            identificatie="a",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer="11",
            locatie_omschrijving="test",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.woz_object,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "wozObjectNummer": "12345",
                    "aanduidingWozObject": {
                        "aoaIdentificatie": "a",
                        "wplWoonplaatsNaam": "test city",
                        "aoaPostcode": "",
                        "gorOpenbareRuimteNaam": "test space",
                        "aoaHuisnummer": 11,
                        "aoaHuisletter": "",
                        "aoaHuisnummertoevoeging": "",
                        "locatieOmschrijving": "test",
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_wozObject(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.woz_object,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "wozObjectNummer": "12345",
                "aanduidingWozObject": {
                    "aoaIdentificatie": "a",
                    "wplWoonplaatsNaam": "test city",
                    "aoaPostcode": "",
                    "gorOpenbareRuimteNaam": "test space",
                    "aoaHuisnummer": 11,
                    "aoaHuisletter": "",
                    "aoaHuisnummertoevoeging": "",
                    "locatieOmschrijving": "test",
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(WozObject.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        wozobject = WozObject.objects.get()
        adres = Adres.objects.get()

        self.assertEqual(zaakobject.wozobject, wozobject)
        self.assertEqual(wozobject.woz_object_nummer, "12345")
        self.assertEqual(wozobject.aanduiding_woz_object, adres)
        self.assertEqual(adres.identificatie, "a")

    def test_update_zaakobject_wozObject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.woz_object
        )
        wozobject = WozObject.objects.create(
            zaakobject=zaakobject, woz_object_nummer="12345"
        )
        Adres.objects.create(
            wozobject=wozobject,
            identificatie="old",
            wpl_woonplaats_naam="old city",
            gor_openbare_ruimte_naam="old space",
            huisnummer="11",
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)
        data = {
            "objectIdentificatie": {
                "wozObjectNummer": "6789",
                "aanduidingWozObject": {
                    "aoaIdentificatie": "new",
                    "wplWoonplaatsNaam": "new city",
                    "gorOpenbareRuimteNaam": "new space",
                    "aoaHuisnummer": 22,
                },
            }
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()
        wozobject = zaakobject.wozobject

        self.assertEqual(wozobject.woz_object_nummer, "6789")
        self.assertEqual(wozobject.aanduiding_woz_object.identificatie, "new")


class ZaakObjectWozDeelobjectTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for WozDeelobject object with nesting
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_wozDeelObject(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.woz_deelobject
        )

        woz_deel_object = WozDeelobject.objects.create(
            zaakobject=zaakobject, nummer_woz_deel_object="12345"
        )

        wozobject = WozObject.objects.create(
            woz_deelobject=woz_deel_object, woz_object_nummer="1"
        )
        Adres.objects.create(
            wozobject=wozobject,
            identificatie="a",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer="11",
            locatie_omschrijving="test",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.woz_deelobject,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "nummerWozDeelObject": "12345",
                    "isOnderdeelVan": {
                        "wozObjectNummer": "1",
                        "aanduidingWozObject": {
                            "aoaIdentificatie": "a",
                            "wplWoonplaatsNaam": "test city",
                            "aoaPostcode": "",
                            "gorOpenbareRuimteNaam": "test space",
                            "aoaHuisnummer": 11,
                            "aoaHuisletter": "",
                            "aoaHuisnummertoevoeging": "",
                            "locatieOmschrijving": "test",
                        },
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_wozDeelObject(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.woz_deelobject,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "nummerWozDeelObject": "12345",
                "isOnderdeelVan": {
                    "wozObjectNummer": "1",
                    "aanduidingWozObject": {
                        "aoaIdentificatie": "a",
                        "wplWoonplaatsNaam": "test city",
                        "aoaPostcode": "",
                        "gorOpenbareRuimteNaam": "test space",
                        "aoaHuisnummer": 11,
                        "aoaHuisletter": "",
                        "aoaHuisnummertoevoeging": "",
                        "locatieOmschrijving": "test",
                    },
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(WozDeelobject.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        wozdeelobject = WozDeelobject.objects.get()
        adres = Adres.objects.get()

        self.assertEqual(zaakobject.wozdeelobject, wozdeelobject)
        self.assertEqual(wozdeelobject.nummer_woz_deel_object, "12345")
        self.assertEqual(wozdeelobject.is_onderdeel_van.aanduiding_woz_object, adres)
        self.assertEqual(adres.identificatie, "a")


class ZaakObjectWozWaardeTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for WozWaarde object with nesting
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_wozWaarde(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.woz_waarde
        )

        woz_warde = WozWaarde.objects.create(
            zaakobject=zaakobject, waardepeildatum="2019"
        )

        wozobject = WozObject.objects.create(woz_warde=woz_warde, woz_object_nummer="1")
        Adres.objects.create(
            wozobject=wozobject,
            identificatie="a",
            wpl_woonplaats_naam="test city",
            gor_openbare_ruimte_naam="test space",
            huisnummer="11",
            locatie_omschrijving="test",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.woz_waarde,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "waardepeildatum": "2019",
                    "isVoor": {
                        "wozObjectNummer": "1",
                        "aanduidingWozObject": {
                            "aoaIdentificatie": "a",
                            "wplWoonplaatsNaam": "test city",
                            "aoaPostcode": "",
                            "gorOpenbareRuimteNaam": "test space",
                            "aoaHuisnummer": 11,
                            "aoaHuisletter": "",
                            "aoaHuisnummertoevoeging": "",
                            "locatieOmschrijving": "test",
                        },
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_wozWaarde(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.woz_waarde,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "waardepeildatum": "2019",
                "isVoor": {
                    "wozObjectNummer": "1",
                    "aanduidingWozObject": {
                        "aoaIdentificatie": "a",
                        "wplWoonplaatsNaam": "test city",
                        "aoaPostcode": "",
                        "gorOpenbareRuimteNaam": "test space",
                        "aoaHuisnummer": 11,
                        "aoaHuisletter": "",
                        "aoaHuisnummertoevoeging": "",
                        "locatieOmschrijving": "test",
                    },
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(WozWaarde.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        wozwaarde = WozWaarde.objects.get()
        adres = Adres.objects.get()

        self.assertEqual(zaakobject.wozwaarde, wozwaarde)
        self.assertEqual(wozwaarde.waardepeildatum, "2019")
        self.assertEqual(wozwaarde.is_voor.aanduiding_woz_object, adres)
        self.assertEqual(adres.identificatie, "a")


class ZaakObjectZakelijkRechtTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for ZakelijkRecht object with nesting
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_zakelijkRecht(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.zakelijk_recht
        )

        zakelijk_recht = ZakelijkRecht.objects.create(
            zaakobject=zaakobject, identificatie="12345", avg_aard="test"
        )

        KadastraleOnroerendeZaak.objects.create(
            zakelijk_recht=zakelijk_recht,
            kadastrale_identificatie="1",
            kadastrale_aanduiding="test",
        )

        heeft_als_gerechtigde = ZakelijkRechtHeeftAlsGerechtigde.objects.create(
            zakelijk_recht=zakelijk_recht
        )
        NatuurlijkPersoon.objects.create(
            zakelijk_rechtHeeft_als_gerechtigde=heeft_als_gerechtigde,
            anp_identificatie="12345",
            inp_a_nummer="1234567890",
        )
        NietNatuurlijkPersoon.objects.create(
            zakelijk_rechtHeeft_als_gerechtigde=heeft_als_gerechtigde,
            ann_identificatie="123456",
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.zakelijk_recht,
                "objectTypeOverige": "",
                "objectIdentificatie": {
                    "identificatie": "12345",
                    "avgAard": "test",
                    "heeftBetrekkingOp": {
                        "kadastraleIdentificatie": "1",
                        "kadastraleAanduiding": "test",
                    },
                    "heeftAlsGerechtigde": {
                        "natuurlijkPersoon": {
                            "inpBsn": "",
                            "anpIdentificatie": "12345",
                            "inpA_nummer": "1234567890",
                            "geslachtsnaam": "",
                            "voorvoegselGeslachtsnaam": "",
                            "voorletters": "",
                            "voornamen": "",
                            "geslachtsaanduiding": "",
                            "geboortedatum": "",
                            "verblijfsadres": None,
                            "subVerblijfBuitenland": None,
                        },
                        "nietNatuurlijkPersoon": {
                            "innNnpId": "",
                            "annIdentificatie": "123456",
                            "statutaireNaam": "",
                            "innRechtsvorm": "",
                            "bezoekadres": "",
                            "subVerblijfBuitenland": None,
                        },
                    },
                },
                "objectTypeOverigeDefinitie": None,
            },
        )

    def test_create_zaakobject_zakelijkRecht(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.zakelijk_recht,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
            "objectIdentificatie": {
                "identificatie": "1111",
                "avgAard": "test",
                "heeftBetrekkingOp": {
                    "kadastraleIdentificatie": "1",
                    "kadastraleAanduiding": "test",
                },
                "heeftAlsGerechtigde": {
                    "natuurlijkPersoon": {
                        "inpBsn": "",
                        "anpIdentificatie": "1234",
                        "inpA_nummer": "1234567890",
                    },
                    "nietNatuurlijkPersoon": {
                        "innNnpId": "",
                        "annIdentificatie": "123456",
                    },
                },
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(ZakelijkRecht.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        zakelijkrecht = ZakelijkRecht.objects.get()

        self.assertEqual(zaakobject.zakelijkrecht, zakelijkrecht)
        self.assertEqual(zakelijkrecht.identificatie, "1111")
        self.assertEqual(
            zakelijkrecht.heeft_betrekking_op.kadastrale_identificatie, "1"
        )
        self.assertEqual(
            zakelijkrecht.heeft_als_gerechtigde.natuurlijkpersoon.anp_identificatie,
            "1234",
        )
        self.assertEqual(
            zakelijkrecht.heeft_als_gerechtigde.nietnatuurlijkpersoon.ann_identificatie,
            "123456",
        )

    def test_update_zaakobject_zakelijkRecht(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.zakelijk_recht
        )
        zakelijk_recht = ZakelijkRecht.objects.create(
            zaakobject=zaakobject, identificatie="12345", avg_aard="old"
        )
        KadastraleOnroerendeZaak.objects.create(
            zakelijk_recht=zakelijk_recht,
            kadastrale_identificatie="1",
            kadastrale_aanduiding="old",
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)
        data = {
            "objectIdentificatie": {
                "identificatie": "6789",
                "avgAard": "new",
                "heeftBetrekkingOp": {
                    "kadastraleIdentificatie": "2",
                    "kadastraleAanduiding": "new",
                },
            }
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()
        zakelijk_recht = zaakobject.zakelijkrecht

        self.assertEqual(zakelijk_recht.identificatie, "6789")
        self.assertEqual(zakelijk_recht.avg_aard, "new")
        self.assertEqual(
            zakelijk_recht.heeft_betrekking_op.kadastrale_identificatie, "2"
        )
        self.assertEqual(
            zakelijk_recht.heeft_betrekking_op.kadastrale_aanduiding, "new"
        )


class ZaakObjectOverigeTestCase(JWTAuthMixin, APITestCase):
    """
    check polymorphism for Overige object with JSON field
    """

    heeft_alle_autorisaties = True

    def test_read_zaakobject_overige(self):

        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.overige
        )
        Overige.objects.create(
            zaakobject=zaakobject, overige_data={"some_field": "some value"}
        )

        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "uuid": str(zaakobject.uuid),
                "zaak": f"http://testserver{zaak_url}",
                "object": "",
                "relatieomschrijving": "",
                "objectType": ZaakobjectTypes.overige,
                "objectTypeOverige": "",
                "objectIdentificatie": {"overigeData": {"someField": "some value"}},
                "objectTypeOverigeDefinitie": None,
            },
        )

    @override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
    def test_create_zaakobject_overige_with_url(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": OBJECT,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverige": "test",
            "relatieomschrijving": "test",
            "objectTypeOverigeDefinitie": None,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(Overige.objects.count(), 0)

    def test_create_zaakobject_overige_with_data(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverige": "test",
            "relatieomschrijving": "test",
            "objectIdentificatie": {"overigeData": {"someField": "some value"}},
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertEqual(ZaakObject.objects.count(), 1)
        self.assertEqual(Overige.objects.count(), 1)

        zaakobject = ZaakObject.objects.get()
        overige = Overige.objects.get()

        self.assertEqual(zaakobject.overige, overige)
        self.assertEqual(overige.overige_data, {"some_field": "some value"})

    @override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
    def test_create_zaakobject_overige_without_type(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": OBJECT,
            "objectType": ZaakobjectTypes.overige,
            "relatieomschrijving": "test",
            "objectTypeOverige": "",
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )
        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["code"], "missing-object-type-overige")

    @override_settings(LINK_FETCHER="vng_api_common.mocks.link_fetcher_200")
    def test_create_zaakobject_with_overige_type(self):
        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": OBJECT,
            "objectType": ZaakobjectTypes.adres,
            "relatieomschrijving": "test",
            "objectTypeOverige": "test",
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )
        error = get_validation_errors(response, "nonFieldErrors")
        self.assertEqual(error["code"], "invalid-object-type-overige-usage")

    def test_update_zaakobject_overige(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.overige
        )
        Overige.objects.create(
            zaakobject=zaakobject, overige_data={"some_field": "old value"}
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)
        data = {"objectIdentificatie": {"overigeData": {"someField": "new value"}}}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zaakobject.refresh_from_db()
        overige = zaakobject.overige

        self.assertEqual(overige.overige_data, {"some_field": "new value"})

    def test_delete_zaakobject_overige(self):
        zaak = ZaakFactory.create()
        zaakobject = ZaakObjectFactory.create(
            zaak=zaak, object="", object_type=ZaakobjectTypes.overige
        )
        Overige.objects.create(
            zaakobject=zaakobject, overige_data={"some_field": "some value"}
        )

        url = get_operation_url("zaakobject_read", uuid=zaakobject.uuid)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ZaakObject.objects.count(), 0)


@tag("objecttype-overige-definitie")
@requests_mock.Mocker()
class ZaakObjectObjectTypeOverigeDefinitie(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True

    OBJECT_TYPE = {
        "url": "https://objecttypes.example.com/api/objecttypes/foo",
        "version": 123,
        "jsonSchema": {
            "$schema": "http://json-schema.org/draft-07/schema",
            "$id": "http://gemeente.nl/beleidsveld.json",
            "type": "object",
            "title": "Beleidsvelden",
            "description": "Beleidsvelden in gebruik binnen de gemeente",
            "default": {},
            "examples": [
                {"name": "Burgerzaken"},
            ],
            "required": ["name"],
            "properties": {
                "name": {
                    "$id": "#/properties/name",
                    "type": "string",
                    "title": "The name schema",
                    "default": "",
                    "examples": ["Burgerzaken"],
                    "maxLength": 100,
                    "minLength": 1,
                    "description": "The name identifying each beleidsveld.",
                },
            },
            "additionalProperties": False,
        },
    }

    def test_create_zaakobject_overig_explicit_schema(self, m):
        """
        Assert that external object type definitions can be referenced.
        """
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo", json=self.OBJECT_TYPE
        )
        m.get(
            object_url,
            json={
                "url": object_url,
                "type": "https://objecttypes.example.com/api/objecttypes/foo",
                "record": {
                    "data": {
                        "name": "Asiel en Migratie",
                    }
                },
            },
        )

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

        zaakobject = ZaakObject.objects.get()
        self.assertEqual(zaakobject.object, object_url)
        self.assertEqual(
            zaakobject.object_type_overige_definitie,
            {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "object_data": ".record.data",
            },
        )

    def test_invalid_schema_reference(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo", json=self.OBJECT_TYPE
        )
        m.get(
            object_url,
            json={
                "url": object_url,
                "type": "https://objecttypes.example.com/api/objecttypes/foo",
                "record": {
                    "data": {
                        "name": "Asiel en Migratie",
                    }
                },
            },
        )

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".invalid",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

    def test_not_json_objecttype(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo",
            text="<DOCTYPE html><html><head></head><body></body></html>",
        )
        m.get(
            object_url,
            json={
                "url": object_url,
                "type": "https://objecttypes.example.com/api/objecttypes/foo",
                "record": {
                    "data": {
                        "name": "Asiel en Migratie",
                    }
                },
            },
        )

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

    def test_unexpected_objecttype_response(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get("https://objecttypes.example.com/api/objecttypes/foo", json="foo")
        m.get(
            object_url,
            json={
                "url": object_url,
                "type": "https://objecttypes.example.com/api/objecttypes/foo",
                "record": {
                    "data": {
                        "name": "Asiel en Migratie",
                    }
                },
            },
        )

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

    def test_invalid_object_url_passed(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo", json=self.OBJECT_TYPE
        )
        m.get(
            object_url,
            json={
                "url": object_url,
                "type": "https://objecttypes.example.com/api/objecttypes/foo",
                "record": {
                    "data": {
                        "invalidKey": "should not validate",
                    }
                },
            },
        )

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

    def test_invalid_object_data_returned(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo", json=self.OBJECT_TYPE
        )
        m.get(object_url, json="foo")

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

    def test_not_json_object(self, m):
        object_url = "https://objects.example.com/api/objects/1234"
        m.get(
            "https://objecttypes.example.com/api/objecttypes/foo", json=self.OBJECT_TYPE
        )
        m.get(object_url, text="<DOCTYPE html><html><head></head><body></body></html>")

        url = get_operation_url("zaakobject_create")
        zaak = ZaakFactory.create()
        zaak_url = get_operation_url("zaak_read", uuid=zaak.uuid)
        data = {
            "zaak": f"http://testserver{zaak_url}",
            "object": object_url,
            "objectType": ZaakobjectTypes.overige,
            "objectTypeOverigeDefinitie": {
                "url": "https://objecttypes.example.com/api/objecttypes/foo",
                # https://stedolan.github.io/jq/ format
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.json()
        )

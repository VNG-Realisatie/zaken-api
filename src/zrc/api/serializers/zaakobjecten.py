import logging

from rest_framework import serializers
from vng_api_common.serializers import GegevensGroepSerializer, NestedGegevensGroepMixin, add_choice_values_help_text
from zrc.datamodel.constants import TyperingWater

from zrc.datamodel.models import (
    Adres, Buurt, Gemeente, GemeentelijkeOpenbareRuimte, Huishouden,
    Inrichtingselement, Kunstwerkdeel, MaatschappelijkeActiviteit, OpenbareRuimte,
    Pand, Spoorbaandeel, Terreindeel, Waterdeel, Wegdeel, Wijk, Woonplaats, Overige,
    TerreinGebouwdObject, WozDeelobject, WozWaarde, WozObjectNummer, ZakelijkRecht,
    ZakelijkRechtHeeftAlsGerechtigde, KadastraleOnroerendeZaak
)
from .base_serializers import RolNietNatuurlijkPersoonSerializer, RolNatuurlijkPersoonSerializer

logger = logging.getLogger(__name__)


class ObjectAdresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adres
        fields = (
            'identificatie',
            'wpl_woonplaats_naam',
            'gor_openbare_ruimte_naam',
            'huisnummer',
            'huisletter',
            'huisnummertoevoeging',
            'postcode',
        )


class ObjectBuurtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buurt
        fields = (
            'buurt_code',
            'buurt_naam',
            'gem_gemeente_code',
            'wyk_wijk_code',
        )


class ObjectGemeenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gemeente
        fields = (
            'gemeente_naam',
            'gemeente_code',
        )


class ObjectGemeentelijkeOpenbareRuimteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GemeentelijkeOpenbareRuimte
        fields = (
            'identificatie',
            'openbare_ruimte_naam',
        )


class ObjectHuishoudenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Huishouden
        fields = (
            'nummer',
        )


class ObjectInrichtingselementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inrichtingselement
        fields = (
            'type',
            'identificatie',
            'naam',
        )


class ObjectKunstwerkdeelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kunstwerkdeel
        fields = (
            'type',
            'identificatie',
            'naam',
        )


class ObjectMaatschappelijkeActiviteitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaatschappelijkeActiviteit
        fields = (
            'kvk_nummer',
            'handelsnaam',
        )


class ObjectOpenbareRuimteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenbareRuimte
        fields = (
            'identificatie',
            'wpl_woonplaats_naam',
            'gor_openbare_ruimte_naam',
        )


class ObjectPandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pand
        fields = (
            'identificatie',
        )


class ObjectSpoorbaandeelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spoorbaandeel
        fields = (
            'type',
            'identificatie',
            'naam',
        )


class ObjectTerreindeelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terreindeel
        fields = (
            'type',
            'identificatie',
            'naam',
        )


class ObjectWaterdeelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waterdeel
        fields = (
            'type_waterdeel',
            'identificatie',
            'naam',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(TyperingWater)
        self.fields['type_waterdeel'].help_text += f"\n\n{value_display_mapping}"


class ObjectWegdeelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wegdeel
        fields = (
            'type',
            'identificatie',
            'naam',
        )


class ObjectWijkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wijk
        fields = (
            'wijk_code',
            'wijk_naam',
            'gem_gemeente_code',
        )


class ObjectWoonplaatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Woonplaats
        fields = (
            'identificatie',
            'woonplaats_naam',
        )


class AdresAanduidingGrpSerializer(GegevensGroepSerializer):
    class Meta:
        model = TerreinGebouwdObject
        gegevensgroep = 'adres_aanduiding_grp'


class ObjectTerreinGebouwdObjectSerializer(NestedGegevensGroepMixin, serializers.ModelSerializer):
    adres_aanduiding_grp = AdresAanduidingGrpSerializer(required=False, allow_null=True)

    class Meta:
        model = TerreinGebouwdObject
        fields = (
            'identificatie',
            'adres_aanduiding_grp',
        )


class AanduidingWozObjectSerializer(GegevensGroepSerializer):
    class Meta:
        model = WozObjectNummer
        gegevensgroep = 'aanduiding_WOZ_object'


class ObjectWozObjectNummerSerializer(NestedGegevensGroepMixin, serializers.ModelSerializer):
    aanduiding_WOZ_object = AanduidingWozObjectSerializer(required=False, allow_null=True)

    class Meta:
        model = WozObjectNummer
        fields = (
            'wozobject_nummer',
            'aanduiding_WOZ_object',
        )


class ObjectWozDeelobjectSerializer(serializers.ModelSerializer):
    is_onderdeel_van = ObjectWozObjectNummerSerializer(required=False)

    class Meta:
        model = WozDeelobject
        fields = (
            'nummer_WOZ_deel_object',
            'is_onderdeel_van',
        )


class ObjectWozWaardeSerializer(serializers.ModelSerializer):
    is_voor = ObjectWozObjectNummerSerializer(required=False)

    class Meta:
        model = WozWaarde
        fields = (
            'waardepeildatum',
            'is_voor',
        )


class ObjectKadastraleOnroerendeZaakSerializer(serializers.ModelSerializer):
    class Meta:
        model = KadastraleOnroerendeZaak
        fields = (
            'kadastrale_identificatie',
            'kadastrale_aanduiding',
        )


class ZakelijkRechtHeeftAlsGerechtigdeSerializer(serializers.ModelSerializer):
    natuurlijk_persoon = RolNatuurlijkPersoonSerializer(required=False)
    niet_natuurlijk_persoon = RolNietNatuurlijkPersoonSerializer(required=False)

    class Meta:
        model = ZakelijkRechtHeeftAlsGerechtigde


class ObjectZakelijkRechtSerializer(serializers.ModelSerializer):
    heeft_betrekking_op = ObjectKadastraleOnroerendeZaakSerializer(required=False)
    heeft_als_gerechtigde = ZakelijkRechtHeeftAlsGerechtigdeSerializer(required=False)

    class Meta:
        model = ZakelijkRecht
        fields = (
            'identificatie',
            'avg_aard',
            'heeft_betrekking_op',
            'heeft_als_gerechtigde',
        )


class ObjectOverigeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Overige
        fields = (
            'overige_data',
        )

import logging

from rest_framework import serializers
from vng_api_common.serializers import add_choice_values_help_text

from zrc.datamodel.constants import GeslachtsAanduiding
from zrc.datamodel.models import (
    Medewerker, NatuurlijkPersoon, NietNatuurlijkPersoon,
    OrganisatorischeEenheid, Vestiging
)
from .adres_serializers import VerblijfsAdresSerializer

logger = logging.getLogger(__name__)


class RolNatuurlijkPersoonSerializer(serializers.ModelSerializer):
    verblijfsadres = VerblijfsAdresSerializer(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(GeslachtsAanduiding)
        self.fields['geslachtsaanduiding'].help_text += f"\n\n{value_display_mapping}"

    class Meta:
        model = NatuurlijkPersoon
        fields = (
            'inp_bsn',
            'anp_identificatie',
            'inp_a_nummer',
            'geslachtsnaam',
            'voorvoegsel_geslachtsnaam',
            'voorletters',
            'voornamen',
            'geslachtsaanduiding',
            'geboortedatum',
            'verblijfsadres',
            'sub_verblijf_buitenland'
        )

    def create(self, validated_data):
        verblijfsadres_data = validated_data.pop('verblijfsadres', None)
        natuurlijkpersoon = super().create(validated_data)

        if verblijfsadres_data:
            verblijfsadres_data['natuurlijkpersoon'] = natuurlijkpersoon
            VerblijfsAdresSerializer().create(verblijfsadres_data)
        return natuurlijkpersoon


class RolNietNatuurlijkPersoonSerializer(serializers.ModelSerializer):
    class Meta:
        model = NietNatuurlijkPersoon
        fields = (
            'inn_nnp_id',
            'ann_identificatie',
            'statutaire_naam',
            'inn_rechtsvorm',
            'bezoekadres',
            'sub_verblijf_buitenland'
        )


class RolVestigingSerializer(serializers.ModelSerializer):
    verblijfsadres = VerblijfsAdresSerializer(required=False, allow_null=True)

    class Meta:
        model = Vestiging
        fields = (
            'vestigings_nummer',
            'handelsnaam',
            'verblijfsadres',
            'sub_verblijf_buitenland'
        )

    def create(self, validated_data):
        verblijfsadres_data = validated_data.pop('verblijfsadres', None)
        natuurlijkpersoon = super().create(validated_data)

        if verblijfsadres_data:
            verblijfsadres_data['natuurlijkpersoon'] = natuurlijkpersoon
            VerblijfsAdresSerializer().create(verblijfsadres_data)
        return natuurlijkpersoon


class RolOrganisatorischeEenheidSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisatorischeEenheid
        fields = (
            'identificatie',
            'naam',
            'is_gehuisvest_in'
        )


class RolMedewerkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medewerker
        fields = (
            'identificatie',
            'achternaam',
            'voorletters',
            'voorvoegsel_achternaam'
        )

from zds_schema.filtersets import FilterSet

from zrc.datamodel.models import Rol, Zaak


class ZaakFilter(FilterSet):
    class Meta:
        model = Zaak
        fields = (
            'identificatie',
            'bronorganisatie',
            'zaaktype',
        )


class RolFilter(FilterSet):
    class Meta:
        model = Rol
        fields = (
            'zaak',
            'betrokkene',
            'betrokkene_type',
            'rolomschrijving',
            'rolomschrijving_generiek',
        )

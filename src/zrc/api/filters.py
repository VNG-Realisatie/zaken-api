from django_filters import rest_framework as filters

from zrc.datamodel.models import Zaak


class ZaakFilter(filters.FilterSet):
    class Meta:
        model = Zaak
        fields = (
            'zaakidentificatie',
            'bronorganisatie',
            'zaaktype',
        )

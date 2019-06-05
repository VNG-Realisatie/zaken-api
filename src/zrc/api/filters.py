from vng_api_common.filtersets import FilterSet

from zrc.datamodel.models import (
    Resultaat, Rol, Status, Zaak, ZaakInformatieObject
)


class ZaakFilter(FilterSet):
    class Meta:
        model = Zaak
        fields = {
            'identificatie': ['exact', ],
            'bronorganisatie': ['exact', ],
            'zaaktype': ['exact', ],
            'archiefnominatie': ['exact', 'in', ],
            'archiefactiedatum': ['exact', 'lt', 'gt', ],
            'archiefstatus': ['exact', 'in', ]
        }


class RolFilter(FilterSet):
    class Meta:
        model = Rol
        fields = (
            'zaak',
            'betrokkene',
            'betrokkene_type',
            'rolomschrijving',
        )


class StatusFilter(FilterSet):
    class Meta:
        model = Status
        fields = (
            'zaak',
            'status_type',
        )


class ResultaatFilter(FilterSet):
    class Meta:
        model = Resultaat
        fields = (
            'zaak',
            'resultaat_type',
        )


class ZaakInformatieObjectFilter(FilterSet):
    class Meta:
        model = ZaakInformatieObject
        fields = (
            'zaak',
            'informatieobject',
        )

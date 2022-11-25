from django.utils.translation import ugettext_lazy as _

from django_filters import filters
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.filtersets import FilterSet
from vng_api_common.utils import get_field_attribute, get_help_text

from zrc.datamodel.models import (
    KlantContact,
    Resultaat,
    Rol,
    Status,
    Zaak,
    ZaakContactMoment,
    ZaakInformatieObject,
    ZaakObject,
    ZaakVerzoek,
)


def get_most_recent_status(queryset, name, value):
    qs = queryset.order_by("-datum_status_gezet")[:1]
    return qs


class MaximaleVertrouwelijkheidaanduidingFilter(filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", VertrouwelijkheidsAanduiding.choices)
        kwargs.setdefault("lookup_expr", "lte")
        super().__init__(*args, **kwargs)

        # rewrite the field_name correctly
        self._field_name = self.field_name
        self.field_name = f"_{self._field_name}_order"

    def filter(self, qs, value):
        if value in filters.EMPTY_VALUES:
            return qs
        order_expression = VertrouwelijkheidsAanduiding.get_order_expression(
            self._field_name
        )
        qs = qs.annotate(**{self.field_name: order_expression})
        numeric_value = VertrouwelijkheidsAanduiding.get_choice(value).order
        return super().filter(qs, numeric_value)


class ZaakFilter(FilterSet):
    maximale_vertrouwelijkheidaanduiding = MaximaleVertrouwelijkheidaanduidingFilter(
        field_name="vertrouwelijkheidaanduiding",
        help_text=(
            "Zaken met een vertrouwelijkheidaanduiding die beperkter is dan de "
            "aangegeven aanduiding worden uit de resultaten gefiltered."
        ),
    )

    rol__betrokkene_identificatie__natuurlijk_persoon__inp_bsn = filters.CharFilter(
        field_name="rol__natuurlijkpersoon__inp_bsn",
        help_text=get_help_text("datamodel.NatuurlijkPersoon", "inp_bsn"),
        max_length=get_field_attribute(
            "datamodel.NatuurlijkPersoon", "inp_bsn", "max_length"
        ),
    )
    rol__betrokkene_identificatie__natuurlijk_persoon__anp_identificatie = (
        filters.CharFilter(
            field_name="rol__natuurlijkpersoon__anp_identificatie",
            help_text=get_help_text("datamodel.NatuurlijkPersoon", "anp_identificatie"),
            max_length=get_field_attribute(
                "datamodel.NatuurlijkPersoon", "anp_identificatie", "max_length"
            ),
        )
    )
    rol__betrokkene_identificatie__natuurlijk_persoon__inp_a_nummer = (
        filters.CharFilter(
            field_name="rol__natuurlijkpersoon__inp_a_nummer",
            help_text=get_help_text("datamodel.NatuurlijkPersoon", "inp_a_nummer"),
            max_length=get_field_attribute(
                "datamodel.NatuurlijkPersoon", "inp_a_nummer", "max_length"
            ),
        )
    )
    rol__betrokkene_identificatie__niet_natuurlijk_persoon__inn_nnp_id = (
        filters.CharFilter(
            field_name="rol__nietnatuurlijkpersoon__inn_nnp_id",
            help_text=get_help_text("datamodel.NietNatuurlijkPersoon", "inn_nnp_id"),
        )
    )
    rol__betrokkene_identificatie__niet_natuurlijk_persoon__ann_identificatie = (
        filters.CharFilter(
            field_name="rol__nietnatuurlijkpersoon__ann_identificatie",
            help_text=get_help_text(
                "datamodel.NietNatuurlijkPersoon", "ann_identificatie"
            ),
            max_length=get_field_attribute(
                "datamodel.NietNatuurlijkPersoon", "ann_identificatie", "max_length"
            ),
        )
    )
    rol__betrokkene_identificatie__vestiging__vestigings_nummer = filters.CharFilter(
        field_name="rol__vestiging__vestigings_nummer",
        help_text=get_help_text("datamodel.Vestiging", "vestigings_nummer"),
        max_length=get_field_attribute(
            "datamodel.Vestiging", "vestigings_nummer", "max_length"
        ),
    )
    rol__betrokkene_identificatie__medewerker__identificatie = filters.CharFilter(
        field_name="rol__medewerker__identificatie",
        help_text=get_help_text("datamodel.Medewerker", "identificatie"),
        max_length=get_field_attribute(
            "datamodel.Medewerker", "identificatie", "max_length"
        ),
    )
    rol__betrokkene_identificatie__organisatorische_eenheid__identificatie = (
        filters.CharFilter(
            field_name="rol__organisatorischeeenheid__identificatie",
            help_text=get_help_text(
                "datamodel.OrganisatorischeEenheid", "identificatie"
            ),
        )
    )
    ordering = filters.OrderingFilter(
        fields=(
            "startdatum",
            "einddatum",
            "publicatiedatum",
            "archiefactiedatum",
        ),
        help_text="Het veld waarop de resultaten geordend worden.",
    )

    class Meta:
        model = Zaak
        fields = {
            "identificatie": ["exact"],
            "bronorganisatie": ["exact"],
            "zaaktype": ["exact"],
            "archiefnominatie": ["exact", "in"],
            "archiefactiedatum": ["exact", "lt", "gt"],
            "archiefstatus": ["exact", "in"],
            "startdatum": ["exact", "gt", "gte", "lt", "lte"],
            "registratiedatum": ["exact", "gt", "lt"],
            "einddatum": ["exact", "gt", "lt"],
            "einddatum_gepland": ["exact", "gt", "lt"],
            "uiterlijke_einddatum_afdoening": ["exact", "gt", "lt"],
            # filters for werkvoorraad
            "rol__betrokkene_type": ["exact"],
            "rol__betrokkene": ["exact"],
            "rol__omschrijving_generiek": ["exact"],
        }


class RolFilter(FilterSet):
    betrokkene_identificatie__natuurlijk_persoon__inp_bsn = filters.CharFilter(
        field_name="natuurlijkpersoon__inp_bsn",
        help_text=get_help_text("datamodel.NatuurlijkPersoon", "inp_bsn"),
    )
    betrokkene_identificatie__natuurlijk_persoon__anp_identificatie = (
        filters.CharFilter(
            field_name="natuurlijkpersoon__anp_identificatie",
            help_text=get_help_text("datamodel.NatuurlijkPersoon", "anp_identificatie"),
        )
    )
    betrokkene_identificatie__natuurlijk_persoon__inp_a_nummer = filters.CharFilter(
        field_name="natuurlijkpersoon__inp_a_nummer",
        help_text=get_help_text("datamodel.NatuurlijkPersoon", "inp_a_nummer"),
    )
    betrokkene_identificatie__niet_natuurlijk_persoon__inn_nnp_id = filters.CharFilter(
        field_name="nietnatuurlijkpersoon__inn_nnp_id",
        help_text=get_help_text("datamodel.NietNatuurlijkPersoon", "inn_nnp_id"),
    )
    betrokkene_identificatie__niet_natuurlijk_persoon__ann_identificatie = (
        filters.CharFilter(
            field_name="nietnatuurlijkpersoon__ann_identificatie",
            help_text=get_help_text(
                "datamodel.NietNatuurlijkPersoon", "ann_identificatie"
            ),
        )
    )
    betrokkene_identificatie__vestiging__vestigings_nummer = filters.CharFilter(
        field_name="vestiging__vestigings_nummer",
        help_text=get_help_text("datamodel.Vestiging", "vestigings_nummer"),
    )
    betrokkene_identificatie__organisatorische_eenheid__identificatie = (
        filters.CharFilter(
            field_name="organisatorischeeenheid__identificatie",
            help_text=get_help_text(
                "datamodel.OrganisatorischeEenheid", "identificatie"
            ),
        )
    )
    betrokkene_identificatie__medewerker__identificatie = filters.CharFilter(
        field_name="medewerker__identificatie",
        help_text=get_help_text("datamodel.Medewerker", "identificatie"),
    )

    class Meta:
        model = Rol
        fields = (
            "zaak",
            "betrokkene",
            "betrokkene_type",
            "betrokkene_identificatie__natuurlijk_persoon__inp_bsn",
            "betrokkene_identificatie__natuurlijk_persoon__anp_identificatie",
            "betrokkene_identificatie__natuurlijk_persoon__inp_a_nummer",
            "betrokkene_identificatie__niet_natuurlijk_persoon__inn_nnp_id",
            "betrokkene_identificatie__niet_natuurlijk_persoon__ann_identificatie",
            "betrokkene_identificatie__vestiging__vestigings_nummer",
            "betrokkene_identificatie__organisatorische_eenheid__identificatie",
            "betrokkene_identificatie__medewerker__identificatie",
            "roltype",
            "omschrijving",
            "omschrijving_generiek",
        )


class StatusFilter(FilterSet):
    indicatie_laatst_gezette_status = filters.Filter(
        method=get_most_recent_status,
        help_text=_(
            "Het gegeven is afleidbaar uit de historie van de attribuutsoort Datum "
            "status gezet van van alle statussen bij de desbetreffende zaak."
        ),
    )

    class Meta:
        model = Status
        fields = ("zaak", "statustype", "indicatie_laatst_gezette_status")


class ResultaatFilter(FilterSet):
    class Meta:
        model = Resultaat
        fields = ("zaak", "resultaattype")


class ZaakInformatieObjectFilter(FilterSet):
    class Meta:
        model = ZaakInformatieObject
        fields = ("zaak", "informatieobject")


class ZaakObjectFilter(FilterSet):
    class Meta:
        model = ZaakObject
        fields = ("zaak", "object", "object_type")


class KlantContactFilter(FilterSet):
    class Meta:
        model = KlantContact
        fields = ("zaak",)


class ZaakContactMomentFilter(FilterSet):
    class Meta:
        model = ZaakContactMoment
        fields = ("zaak", "contactmoment")


class ZaakVerzoekFilter(FilterSet):
    class Meta:
        model = ZaakVerzoek
        fields = ("zaak", "verzoek")

from django.contrib import admin
from django.utils.translation import gettext as _

from zrc.datamodel.forms import ZakenForm
from zrc.utils.forms import GegevensGroepTypeMixin

from ..models import (
    KlantContact,
    RelevanteZaakRelatie,
    Resultaat,
    Rol,
    Status,
    Zaak,
    ZaakContactMoment,
    ZaakEigenschap,
    ZaakInformatieObject,
    ZaakObject,
)


class StatusInline(admin.TabularInline):
    model = Status


class ZaakObjectInline(admin.TabularInline):
    model = ZaakObject


class ZaakEigenschapInline(admin.TabularInline):
    model = ZaakEigenschap


class ZaakInformatieObjectInline(admin.TabularInline):
    model = ZaakInformatieObject


class KlantContactInline(admin.TabularInline):
    model = KlantContact


class RolInline(admin.TabularInline):
    model = Rol

    raw_id_fields = ["zaak"]
    readonly_fields = ("uuid",)

    fieldsets = (
        (
            _("Algemeen"),
            {
                "fields": (
                    "uuid",
                    "zaak",
                    "roltype",
                    "roltoelichting",
                    "indicatie_machtiging",
                    "statussen",
                ),
            },
        ),
        (
            _("Betrokkene"),
            {
                "fields": (
                    "betrokkene",
                    "betrokkene_type",
                    "afwijkende_naam_betrokkene",
                ),
            },
        ),
        (
            _("Contactpersoon"),
            {
                "fields": (
                    "contactpersoon_email",
                    "contactpersoon_functie",
                    "contactpersoon_telefoonnummer",
                    "contactpersoon_naam",
                ),
            },
        ),
    )


class ResultaatInline(admin.TabularInline):
    model = Resultaat


class RelevanteZaakRelatieInline(admin.TabularInline):
    model = RelevanteZaakRelatie


class ZaakContactMomentInline(admin.TabularInline):
    model = ZaakContactMoment


@admin.register(Zaak)
class ZaakAdmin(admin.ModelAdmin):
    form = ZakenForm

    list_display = ["identificatie"]
    inlines = [
        StatusInline,
        ZaakObjectInline,
        ZaakInformatieObjectInline,
        KlantContactInline,
        ZaakEigenschapInline,
        RolInline,
        ResultaatInline,
        RelevanteZaakRelatieInline,
        ZaakContactMomentInline,
    ]

    fieldsets = (
        (
            _("Algemeen"),
            {
                "fields": (
                    "uuid",
                    "hoofdzaak",
                    "identificatie",
                    "bronorganisatie",
                    "omschrijving",
                    "toelichting",
                    "zaaktype",
                    "registratiedatum",
                    "verantwoordelijke_organisatie",
                    "startdatum",
                    "einddatum",
                    "einddatum_gepland",
                    "uiterlijke_einddatum_afdoening",
                    "publicatiedatum",
                    "producten_of_diensten",
                    "communicatiekanaal",
                    "vertrouwelijkheidaanduiding",
                    "betalingsindicatie",
                    "laatste_betaaldatum",
                    "zaakgeometrie",
                    "selectielijstklasse",
                    "opdrachtgevende_organisatie",
                    "processobjectaard",
                    "resultaattoelichting",
                    "startdatum_bewaartermijn",
                ),
            },
        ),
        (
            _("Verlenging"),
            {
                "fields": (
                    "verlenging_reden",
                    "verlenging_duur",
                ),
            },
        ),
        (
            _("Opschorting"),
            {
                "fields": (
                    "opschorting_indicatie",
                    "opschorting_reden",
                ),
            },
        ),
        (
            _("Archievering"),
            {
                "fields": (
                    "archiefnominatie",
                    "archiefstatus",
                    "archiefactiedatum",
                ),
            },
        ),
        (
            _("Gerelateerde externe zaken"),
            {
                "fields": (
                    "gerelateerde_externe_zaken_aanvraagdatum",
                    "gerelateerde_externe_zaken_aard_relatie",
                    "gerelateerde_externe_zaken_datum_status_gezet",
                    "gerelateerde_externe_zaken_einddatum",
                    "gerelateerde_externe_zaken_resultaatomschrijving",
                    "gerelateerde_externe_zaken_startdatum",
                    "gerelateerde_externe_zaken_status_omschrijving_generiek",
                    "gerelateerde_externe_zaken_verantwoordelijke_organisatie",
                    "gerelateerde_externe_zaken_zaakidentificatie",
                    "gerelateerde_externe_zaken_zaaktype_omschrijving_generiek",
                    "gerelateerde_externe_zaken_zaaktypecode",
                    "gerelateerde_externe_zaken_url",
                ),
            },
        ),
        (
            _("Processobject"),
            {
                "fields": (
                    "processobject_datumkenmerk",
                    "processobject_identificatie",
                    "processobject_objecttype",
                    "processobject_registratie",
                ),
            },
        ),
    )


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ["zaak", "datum_status_gezet", "_etag"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]
    search_field = ("_etag",)


@admin.register(ZaakObject)
class ZaakObjectAdmin(admin.ModelAdmin):
    list_display = ["zaak", "object", "relatieomschrijving"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]


@admin.register(KlantContact)
class KlantContactAdmin(admin.ModelAdmin):
    list_display = ["zaak", "identificatie", "datumtijd", "kanaal"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]


@admin.register(ZaakEigenschap)
class ZaakEigenschapAdmin(admin.ModelAdmin):
    list_display = ["zaak", "eigenschap", "waarde"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]


@admin.register(ZaakInformatieObject)
class ZaakInformatieObjectAdmin(admin.ModelAdmin):
    list_display = ["zaak", "informatieobject"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak", "status"]


@admin.register(Resultaat)
class ResultaatAdmin(admin.ModelAdmin):
    list_display = ["zaak", "toelichting"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]


@admin.register(ZaakContactMoment)
class ZaakContactMomentAdmin(admin.ModelAdmin):
    list_display = ["zaak", "contactmoment"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]

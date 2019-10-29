from django.contrib import admin

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


class ResultaatInline(admin.TabularInline):
    model = Resultaat


class RelevanteZaakRelatieInline(admin.TabularInline):
    model = RelevanteZaakRelatie


class ZaakContactMomentInline(admin.TabularInline):
    model = ZaakContactMoment


@admin.register(Zaak)
class ZaakAdmin(admin.ModelAdmin):
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
        ZaakContactMomentInline
    ]


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
    raw_id_fields = ["zaak"]


@admin.register(Resultaat)
class ResultaatAdmin(admin.ModelAdmin):
    list_display = ["zaak", "toelichting"]
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]


@admin.register(ZaakContactMoment)
class ZaakContactMomentAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'contactmoment']
    list_select_related = ["zaak"]
    raw_id_fields = ["zaak"]

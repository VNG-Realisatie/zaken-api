from django.contrib import admin

from .models import (
    DomeinData, KlantContact, Status, Zaak, ZaakInformatieObject, ZaakObject
)


class StatusInline(admin.TabularInline):
    model = Status


class ZaakObjectInline(admin.TabularInline):
    model = ZaakObject


class DomeinDataInline(admin.TabularInline):
    model = DomeinData


class KlantContactInline(admin.TabularInline):
    model = KlantContact


class ZaakInformatieObjectInline(admin.TabularInline):
    model = ZaakInformatieObject


@admin.register(Zaak)
class ZaakAdmin(admin.ModelAdmin):
    list_display = ['zaakidentificatie']
    inlines = [
        StatusInline,
        ZaakObjectInline,
        ZaakInformatieObjectInline,
        KlantContactInline,
        DomeinDataInline
    ]


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'datum_status_gezet']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(ZaakObject)
class ZaakObjectAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'object', 'relatieomschrijving']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(KlantContact)
class KlantContactAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'identificatie', 'datumtijd', 'kanaal']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(DomeinData)
class DomeinDataAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'domein_data']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(ZaakInformatieObject)
class ZaakInformatieObjectAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'informatieobject']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']

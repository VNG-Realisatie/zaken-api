from django.contrib import admin

from .models import (
    KlantContact, Resultaat, Rol, Status, Zaak, ZaakEigenschap,
    ZaakInformatieObject, ZaakObject,
    NatuurlijkPersoon, NietNatuurlijkPersoon, OrganisatorischeEenheid,
    Medewerker, Vestiging
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
    raw_id_fields = ['zaak']


class ResultaatInline(admin.TabularInline):
    model = Resultaat


@admin.register(Zaak)
class ZaakAdmin(admin.ModelAdmin):
    list_display = ['identificatie']
    inlines = [
        StatusInline,
        ZaakObjectInline,
        ZaakInformatieObjectInline,
        KlantContactInline,
        ZaakEigenschapInline,
        RolInline,
        ResultaatInline,
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


@admin.register(ZaakEigenschap)
class ZaakEigenschapAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'eigenschap', 'waarde']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(ZaakInformatieObject)
class ZaakInformatieObjectAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'informatieobject']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


@admin.register(Resultaat)
class ResultaatAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'toelichting']
    list_select_related = ['zaak']
    raw_id_fields = ['zaak']


# Betrokkene models
@admin.register(NatuurlijkPersoon)
class NatuurlijkPersoonAdmin(admin.ModelAdmin):
    list_display = ['rol', 'burgerservicenummer']


@admin.register(NietNatuurlijkPersoon)
class NietNatuurlijkPersoonAdmin(admin.ModelAdmin):
    list_display = ['rol', 'rsin']


@admin.register(OrganisatorischeEenheid)
class OrganisatorischeEenheidAdmin(admin.ModelAdmin):
    list_display = ['rol', 'identificatie']


@admin.register(Vestiging)
class VestigingAdmin(admin.ModelAdmin):
    list_display = ['rol', 'vestigings_nummer']


@admin.register(Medewerker)
class MedewerkerAdmin(admin.ModelAdmin):
    list_display = ['rol', 'identificatie']

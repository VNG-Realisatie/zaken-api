from django.contrib import admin

from .models import Status, Zaak


@admin.register(Zaak)
class ZaakAdmin(admin.ModelAdmin):
    list_display = ['zaakidentificatie']


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['zaak', 'datum_status_gezet']
    list_select_related = ['zaak']

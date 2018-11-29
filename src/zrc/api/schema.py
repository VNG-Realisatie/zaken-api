from django.conf import settings

from drf_yasg import openapi

info = openapi.Info(
    title="Zaakregistratiecomponent (ZRC) API",
    default_version=settings.API_VERSION,
    description="Een API om een zaakregistratiecomponent te benaderen",
    contact=openapi.Contact(
        email="support@maykinmedia.nl",
        url="https://github.com/VNG-Realisatie/gemma-zaken"
    ),
    license=openapi.License(name="EUPL 1.2"),
)

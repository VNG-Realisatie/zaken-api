from notifications_api_common.kanalen import Kanaal

from zrc.datamodel.models import Zaak

KANAAL_ZAKEN = Kanaal(
    "zaken",
    main_resource=Zaak,
    kenmerken=("bronorganisatie", "zaaktype", "vertrouwelijkheidaanduiding"),
)

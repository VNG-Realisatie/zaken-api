import os

from vng_api_common.conf.api import *  # noqa - imports white-listed

API_VERSION = "1.3.0-rc3"

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()
REST_FRAMEWORK["PAGE_SIZE"] = 100

SECURITY_DEFINITION_NAME = "JWT-Claims"

SPECTACULAR_SETTINGS = BASE_SPECTACULAR_SETTINGS.copy()
SPECTACULAR_SETTINGS.update(
    {
        "TAGS": [
            {
                "name": "zaken",
                "path": "zrc.api.viewsets",
                "view": "ZaakViewSet",
            },
            {
                "name": "statussen",
                "path": "zrc.api.viewsets",
                "view": "StatusViewSet",
            },
            {
                "name": "zaakobjecten",
                "path": "zrc.api.viewsets",
                "view": "ZaakObjectViewSet",
            },
            {
                "name": "klantcontacten",
                "path": "zrc.api.viewsets",
                "view": "KlantContactViewSet",
            },
            {
                "name": "rollen",
                "path": "zrc.api.viewsets",
                "view": "RolViewSet",
            },
            {
                "name": "resultaten",
                "path": "zrc.api.viewsets",
                "view": "ResultaatViewSet",
            },
            {
                "name": "zaakinformatieobjecten",
                "path": "zrc.api.viewsets",
                "view": "ZaakInformatieObjectViewSet",
            },
            {
                "name": "zaakcontactmomenten",
                "path": "zrc.api.viewsets",
                "view": "ZaakContactMomentViewSet",
            },
            {
                "name": "zaakverzoeken",
                "path": "zrc.api.viewsets",
                "view": "ZaakVerzoekViewSet",
            },
        ],
        "DESCRIPTION": "zrc.api.schema",
        "POSTPROCESSING_HOOKS": [
            "drf_spectacular.hooks.postprocess_schema_enums",
            "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
        ],
        "SCHEMA_PATH_PREFIX": "/api/v1",
        "SERVERS": [{"url": "/api/v1"}],
        "EXTENSIONS_INFO": {},
        "PREPROCESSING_HOOKS": ["vng_api_common.utils.preprocessing_filter_spec"],
        "APPEND_COMPONENTS": {
            "securitySchemes": {
                "JWT-Claims": {
                    "type": "http",
                    "bearerFormat": "JWT",
                    "scheme": "bearer",
                }
            },
        },
        "SECURITY": [
            {
                "JWT-Claims": [],
            }
        ],
    }
)

GEMMA_URL_INFORMATIEMODEL_VERSIE = "1.0"

repo = "vng-Realisatie/vng-referentielijsten"
commit = "da1b2cfdaadb2d19a7d3fc14530923913a2560f2"
REFERENTIELIJSTEN_API_SPEC = (
    f"https://raw.githubusercontent.com/{repo}/{commit}/src/openapi.yaml"  # noqa
)

ztc_repo = "vng-Realisatie/catalogi-api"
ztc_commit = "e2e037d3b901d38c58b0e1339610347bf02279a5"
ZTC_API_SPEC = f"https://raw.githubusercontent.com/{ztc_repo}/{ztc_commit}/src/openapi.yaml"  # noqa

drc_repo = "vng-Realisatie/documenten-api"
drc_commit = "e82802907c24ea6a11a39c77595c29338d55e8c3"
DRC_API_SPEC = f"https://raw.githubusercontent.com/{drc_repo}/{drc_commit}/src/openapi.yaml"  # noqa

zrc_repo = "vng-Realisatie/zaken-api"
zrc_commit = "8ea1950fe4ec2ad99504d345eba60a175eea3edf"
ZRC_API_SPEC = f"https://raw.githubusercontent.com/{zrc_repo}/{zrc_commit}/src/openapi.yaml"  # noqa

SELF_REPO = zrc_repo
SELF_BRANCH = os.getenv("SELF_BRANCH") or API_VERSION
GITHUB_API_SPEC = f"https://raw.githubusercontent.com/{SELF_REPO}/{SELF_BRANCH}/src/openapi.yaml"  # noqa

cmc_repo = "VNG-Realisatie/contactmomenten-api"
cmc_commit = "75980b03ca80c3359fd71cde2140bd88c98b6529"
CMC_API_SPEC = f"https://raw.githubusercontent.com/{cmc_repo}/{cmc_commit}/src/openapi.yaml"  # noqa

kc_repo = "VNG-Realisatie/klanten-api"
kc_commit = "3048e71fb58e59fed334414a08949363cfe43e35"
KC_API_SPEC = (
    f"https://raw.githubusercontent.com/{kc_repo}/{kc_commit}/src/openapi.yaml"  # noqa
)

vrc_repo = "VNG-Realisatie/verzoeken-api"
vrc_commit = "fc27f8b386dfe49f0b4a20adf93119c866c7047d"
VRC_API_SPEC = f"https://raw.githubusercontent.com/{vrc_repo}/{vrc_commit}/src/openapi.yaml"  # noqa

SPEC_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

NOTIFICATIONS_KANAAL = "zaken"

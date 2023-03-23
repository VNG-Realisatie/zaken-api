import os

from vng_api_common.conf.api import *  # noqa - imports white-listed

API_VERSION = "1.4.0-rc3"

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()
REST_FRAMEWORK["PAGE_SIZE"] = 100

DOCUMENTATION_INFO_MODULE = "zrc.api.schema"

SPECTACULAR_SETTINGS = BASE_SPECTACULAR_SETTINGS.copy()
SPECTACULAR_SETTINGS.update(
    {
        # Optional list of servers.
        # Each entry MUST contain "url", MAY contain "description", "variables"
        # e.g. [{'url': 'https://example.com/v1', 'description': 'Text'}, ...]
        "SERVERS": [
            {
                "url": "https://zaken-api.vng.cloud/api/v1",
                "description": "Productie Omgeving",
            }
        ],
        "SORT_OPERATION_PARAMETERS": False,
        "ENUM_NAME_OVERRIDES": {
            "Rol_betrokkeneTypeEnum": "vng_api_common.constants.RolTypes",
            "MaximaleVertrouwelijkheidaanduidingEnum": "vng_api_common.constants.VertrouwelijkheidsAanduiding",
        },
    }
)
SPECTACULAR_EXTENSIONS = [
    "vng_api_common.extensions.fields.duration.DurationFieldExtension",
    "vng_api_common.extensions.fields.geojson.GeometryFieldExtension",
    "vng_api_common.extensions.fields.hyperlink_identity.HyperlinkedIdentityFieldExtension",
    "vng_api_common.extensions.fields.hyperlinked_related.HyperlinkedRelatedFieldExtension",
    "vng_api_common.extensions.fields.many_related.ManyRelatedFieldExtension",
    "vng_api_common.extensions.fields.read_only.ReadOnlyFieldExtension",
    "vng_api_common.extensions.filters.query.FilterExtension",
    "vng_api_common.extensions.serializers.gegevensgroep.GegevensGroepExtension",
    "vng_api_common.extensions.serializers.polymorphic.PolymorphicSerializerExtension",
]

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

from vng_api_common.conf.api import *  # noqa - imports white-listed

API_VERSION = "1.1.0-alpha"

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()
REST_FRAMEWORK["PAGE_SIZE"] = 100

SECURITY_DEFINITION_NAME = "JWT-Claims"

SWAGGER_SETTINGS = BASE_SWAGGER_SETTINGS.copy()
SWAGGER_SETTINGS.update(
    {
        "DEFAULT_INFO": "zrc.api.schema.info",
        "DEFAULT_AUTO_SCHEMA_CLASS": "zrc.api.inspectors.AutoSchema",
        "SECURITY_DEFINITIONS": {
            SECURITY_DEFINITION_NAME: {
                # OAS 3.0
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                # not official...
                # 'scopes': {},  # TODO: set up registry that's filled in later...
                # Swagger 2.0
                # 'name': 'Authorization',
                # 'in': 'header'
                # 'type': 'apiKey',
            }
        },
        "DEFAULT_FIELD_INSPECTORS": (
            "vng_api_common.inspectors.geojson.GeometryFieldInspector",
        )
        + BASE_SWAGGER_SETTINGS["DEFAULT_FIELD_INSPECTORS"],
    }
)

GEMMA_URL_INFORMATIEMODEL_VERSIE = "1.0"

repo = "vng-Realisatie/vng-referentielijsten"
commit = "da1b2cfdaadb2d19a7d3fc14530923913a2560f2"
REFERENTIELIJSTEN_API_SPEC = (
    f"https://raw.githubusercontent.com/{repo}/{commit}/src/openapi.yaml"  # noqa
)

ztc_repo = "vng-Realisatie/gemma-zaaktypecatalogus"
ztc_commit = "b8cc38484ad862b9bbbf975e24718ede3f662e1e"
ZTC_API_SPEC = f"https://raw.githubusercontent.com/{ztc_repo}/{ztc_commit}/src/openapi.yaml"  # noqa

drc_repo = "vng-Realisatie/gemma-documentregistratiecomponent"
drc_commit = "e82802907c24ea6a11a39c77595c29338d55e8c3"
DRC_API_SPEC = f"https://raw.githubusercontent.com/{drc_repo}/{drc_commit}/src/openapi.yaml"  # noqa

zrc_repo = "vng-Realisatie/gemma-zaakregistratiecomponent"
zrc_commit = "8ea1950fe4ec2ad99504d345eba60a175eea3edf"
ZRC_API_SPEC = f"https://raw.githubusercontent.com/{zrc_repo}/{zrc_commit}/src/openapi.yaml"  # noqa

kic_repo = "VNG-Realisatie/klantinteracties-api"
kic_commit = "c62f0a2e9c47955316fe2f8f4caa6b522d71bbe9"
KIC_API_SPEC = f"https://raw.githubusercontent.com/{kic_repo}/{kic_commit}/src/openapi.yaml"  # noqa

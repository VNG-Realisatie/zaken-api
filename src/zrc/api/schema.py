import os
from urllib.parse import urlsplit

from django.conf import settings

import yaml
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.response import Response
from zds_schema.schema import OpenAPISchemaGenerator

info = openapi.Info(
    title="Zaakregistratiecomponent (ZRC) API",
    default_version='1',
    description="Een API om een zaakregistratiecomponent te benaderen",
    contact=openapi.Contact(
        email="support@maykinmedia.nl",
        url="https://github.com/VNG-Realisatie/gemma-zaken"
    ),
    license=openapi.License(name="EUPL 1.2"),
)

DefaultSchemaView = get_schema_view(
    # validators=['flex', 'ssv'],
    generator_class=OpenAPISchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class SchemaView(DefaultSchemaView):

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        version = request.GET.get('v', '')
        if not version.startswith('3'):
            return response

        # serve the staticically included V3 schema
        SCHEMA_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')
        with open(SCHEMA_PATH, 'r') as infile:
            schema = yaml.safe_load(infile)

        # fix the servers
        for server in schema['servers']:
            split_url = urlsplit(server['url'])
            if split_url.netloc:
                continue
            server['url'] = request.build_absolute_uri(server['url'])

        # FIXME: fix renderer
        # see drf_yasg.renderers

        return Response(
            data=schema,
            headers={'X-OAS-Version': schema['openapi']}
        )

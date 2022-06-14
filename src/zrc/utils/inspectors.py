from collections import OrderedDict
from typing import Iterable, List

from django.conf import settings

from drf_yasg import openapi
from drf_yasg.inspectors.field import SerializerInspector

from zrc.api.inclusion import get_component_name, get_include_resources


# TODO API settings should have a list of supported API versions
# see: https://github.com/open-zaak/open-zaak/pull/1138#discussion_r892398142
def get_external_schema_refs(component: str, resource: str) -> List[str]:
    """
    Constructs the schema references for external resources
    """
    schema_ref = f"#/components/schemas/{resource}"
    ref_url = f"{settings.COMPONENT_TO_API_SPEC_MAPPING[component]}{schema_ref}"
    return [ref_url]


class IncludeSerializerInspector(SerializerInspector):
    def get_inclusion_props(self, serializer_class) -> OrderedDict:
        inclusion_props = OrderedDict()
        inclusion_opts = get_include_resources(serializer_class)
        for component, resource in inclusion_opts:
            # If the compont the resource is present in is the component for which the
            # schema is being generated, simply use an internal reference
            if component == get_component_name(serializer_class):
                ref_url = f"#/components/schemas/{resource}"
                inclusion_props[f"{component}:{resource}".lower()] = openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.SwaggerDict(**{"$ref": ref_url}),
                )
            else:
                ref_urls = get_external_schema_refs(component, resource)
                inclusion_props[f"{component}:{resource}".lower()] = openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.SwaggerDict(
                        oneOf=[
                            openapi.SwaggerDict(**{"$ref": ref_url})
                            for ref_url in ref_urls
                        ]
                    ),
                )
        return inclusion_props

    def get_inclusion_responses(
        self, renderer_classes: Iterable, response_schema: OrderedDict
    ) -> OrderedDict:
        allowed_check = getattr(self.view, "include_allowed", lambda: True)
        skip_includes = not allowed_check()
        if skip_includes:
            return response_schema

        for status, response in response_schema.items():
            if "schema" not in response:
                continue

            inclusion_props = self.get_inclusion_props(self.view.serializer_class)
            if "properties" in response["schema"]:
                properties = response["schema"]["properties"]
                properties["inclusions"] = openapi.Schema(
                    type=openapi.TYPE_OBJECT, properties=inclusion_props
                )

                schema = openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties=properties,
                    required=response["schema"].get("required", []) + ["inclusions"],
                )
                response["schema"] = schema

        return response_schema

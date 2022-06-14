from collections import OrderedDict

from drf_yasg import openapi
from vng_api_common.inspectors.view import AutoSchema as _AutoSchema, response_header

from ..middleware import WARNING_HEADER

warning_header = response_header(
    "Geeft een endpoint-specifieke waarschuwing, zoals het uitfaseren van functionaliteit.",
    type=openapi.TYPE_STRING,
)


class AutoSchema(_AutoSchema):
    def should_include(self):
        if hasattr(self.view.serializer_class, "inclusion_serializers"):
            return True
        return False

    def get_default_responses(self) -> OrderedDict:
        default_schema = super().get_default_responses()
        if self.should_include():
            self.get_inclusion_responses(default_schema) or default_schema

        return default_schema

    def get_inclusion_responses(self, response_schema):
        """
        Add appropriate inclusion fields to a response :class:`.Schema`
        """
        return self.probe_inspectors(
            self.field_inspectors,
            "get_inclusion_responses",
            getattr(self.view, "renderer_classes"),
            response_schema=response_schema,
            initkwargs={"field_inspectors": self.field_inspectors},
        )

    def get_response_schemas(self, response_serializers):
        responses = super().get_response_schemas(response_serializers)
        if not hasattr(self.view, "deprecation_message"):
            return responses

        for status_code, response in responses.items():
            if "$ref" not in response:
                response.setdefault("headers", OrderedDict())
                response["headers"][WARNING_HEADER] = warning_header

        return responses

    def is_deprecated(self):
        deprecation_message = getattr(self.view, "deprecation_message", None)
        return bool(deprecation_message) or super().is_deprecated()

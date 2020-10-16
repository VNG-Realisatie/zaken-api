from collections import OrderedDict

from drf_yasg import openapi
from vng_api_common.inspectors.view import AutoSchema as _AutoSchema, response_header

from ..middleware import WARNING_HEADER

warning_header = response_header(
    "Geeft een endpoint-specifieke waarschuwing, zoals het uitfaseren van functionaliteit.",
    type=openapi.TYPE_STRING,
)


class AutoSchema(_AutoSchema):
    def get_response_schemas(self, response_serializers):
        responses = super().get_response_schemas(response_serializers)
        if not hasattr(self.view, "deprecation_message"):
            return responses

        for status_code, response in responses.items():
            response.setdefault("headers", OrderedDict())
            response["headers"][WARNING_HEADER] = warning_header

        return responses

    def is_deprecated(self):
        deprecation_message = getattr(self.view, "deprecation_message", None)
        return bool(deprecation_message) or super().is_deprecated()

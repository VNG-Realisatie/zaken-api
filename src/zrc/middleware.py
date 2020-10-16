# See https://github.com/Geonovum/KP-APIs/blob/master/Werkgroep%20API%20strategie/extensies/ext-versionering.md

WARNING_HEADER = "Warning"
DEPRECATION_WARNING_CODE = 299


class Warning:
    def __init__(self, code: int, agent: str, text: str):
        self.code = code
        self.agent = agent
        self.text = text

    def __str__(self):
        return f'{self.code} "{self.agent}" "{self.text}"'


class DeprecationMiddleware:
    """
    Include a header outputting a deprecation warning.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if self.get_response is None:
            return None

        response = self.get_response(request)

        warning = getattr(request, "_warning", None)
        if warning:
            response[WARNING_HEADER] = str(warning)

        return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # not a viewset
        if not hasattr(callback, "cls"):
            return None

        deprecation_msg = getattr(callback.cls, "deprecation_message", None)
        # no deprecation happening
        if not deprecation_msg:
            return None

        request._warning = Warning(
            DEPRECATION_WARNING_CODE,
            request.build_absolute_uri(request.path),
            deprecation_msg,
        )

        return None

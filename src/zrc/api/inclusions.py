import json
import re
from typing import Union
from urllib.request import Request, urlopen

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from vng_api_common.middleware import JWTAuth

from zrc.datamodel.models import (
    KlantContact,
    Resultaat,
    Rol,
    Status,
    Zaak,
    ZaakBesluit,
    ZaakContactMoment,
    ZaakEigenschap,
    ZaakInformatieObject,
    ZaakObject,
)

from .serializers import (
    KlantContactSerializer,
    ResultaatSerializer,
    RolSerializer,
    StatusSerializer,
    ZaakBesluitSerializer,
    ZaakContactMomentSerializer,
    ZaakEigenschapSerializer,
    ZaakInformatieObjectSerializer,
    ZaakObjectSerializer,
    ZaakSerializer,
    ZaakVerzoek,
    ZaakVerzoekSerializer,
    ZaakZoekSerializer,
)

EXTERNAL_URIS = [
    "zaaktype",
    "hoofdzaak",
    "deelzaken",
    "relevanteAndereZaken",
    "statustypen",
    "catalogus",
]

URI_NAME_TO_MODEL_NAME_MAPPER = {
    "rollen": Rol,
    "rol": Rol,
    "statussen": Status,
    "status": Status,
    "zaak": Zaak,
    "zaken": Zaak,
    "eigenschappen": ZaakEigenschap,
    "eigenschap": ZaakEigenschap,
    "zaakinformatieobjecten": ZaakInformatieObject,
    "zaakinformatieobject": ZaakInformatieObject,
    "zaakobjecten": ZaakObject,
    "zaakobject": ZaakObject,
    "resultaten": Resultaat,
    "resultaat": Resultaat,
}
URI_NAME_TO_SERIALIZER_MAPPER = {
    "rollen": RolSerializer,
    "rol": RolSerializer,
    "statussen": StatusSerializer,
    "status": StatusSerializer,
    "zaak": ZaakSerializer,
    "zaken": ZaakSerializer,
    "eigenschappen": ZaakEigenschapSerializer,
    "eigenschap": ZaakEigenschapSerializer,
    "zaakinformatieobjecten": ZaakInformatieObjectSerializer,
    "zaakinformatieobject": ZaakInformatieObjectSerializer,
    "zaakobjecten": ZaakObjectSerializer,
    "zaakobject": ZaakObjectSerializer,
    "resultaten": ResultaatSerializer,
    "resultaat": ResultaatSerializer,
}


class Inclusions:
    def list(self, request, *args, **kwargs):
        """Override LIST operation to override serializer and add inclusions"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer = self.inclusions(serializer, request)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        serializer = self.inclusions(serializer, request)
        return Response(serializer.data)

    def get_data(
        self,
        url: str,
        resource_to_expand: list,
        called_external_uris: dict,
        jwt_auth: JWTAuth,
    ) -> dict:
        """Get data from external url or from local database"""
        if resource_to_expand in EXTERNAL_URIS:
            if not called_external_uris.get(url, []):
                try:
                    access_token = jwt_auth.encoded
                    headers = {"Authorization": f"Bearer {access_token}"}
                    with urlopen(Request(url, headers=headers)) as response:
                        data = json.loads(response.read().decode("utf8"))
                        called_external_uris[url] = data
                        return data

                except:
                    called_external_uris[url] = {}
                    return {}
            else:
                return called_external_uris[url]

        else:
            uuid = url.split("/")[-1]
            model = get_object_or_404(
                URI_NAME_TO_MODEL_NAME_MAPPER[resource_to_expand], uuid=uuid
            )
            serializer_exp_field = URI_NAME_TO_SERIALIZER_MAPPER[resource_to_expand](
                model, context={"request": self.request}
            )
            return serializer_exp_field.data

    def expand_array(
        self,
        array_data: dict,
        sub_field: str,
        called_external_uris: dict,
        jwt_auth: JWTAuth,
    ) -> Union[dict, bool]:
        """Expand array of urls"""
        array_data["_inclusions"][sub_field] = []
        if array_data[sub_field]:
            for url in array_data[sub_field]:
                data_from_url = self.get_data(
                    url, sub_field, called_external_uris, jwt_auth
                )
                array_data["_inclusions"][sub_field].append(data_from_url)
                recursion_data = array_data["_inclusions"][sub_field]

            return False, recursion_data
        else:
            return True, array_data

    def expand_dict(
        self,
        array_data: dict,
        sub_field: str,
        called_external_uris: dict,
        jwt_auth: JWTAuth,
    ):
        if array_data[sub_field]:
            data_from_url = self.get_data(
                array_data[sub_field], sub_field, called_external_uris, jwt_auth
            )
            array_data["_inclusions"][sub_field] = data_from_url
            return False, array_data["_inclusions"][sub_field]
        else:
            array_data["_inclusions"][sub_field] = {}
            return True, array_data

    def build_inclusions_schema(
        self,
        result: dict,
        fields_to_expand: list,
        called_external_uris: dict,
        jwt_auth: JWTAuth,
    ):
        for exp_field in fields_to_expand:
            for counter, sub_field in enumerate(exp_field.split(".")):
                if counter == 0:
                    if isinstance(result[sub_field], list):
                        break_off, recursion_data = self.expand_array(
                            result, sub_field, called_external_uris, jwt_auth
                        )
                    else:
                        break_off, recursion_data = self.expand_dict(
                            result, sub_field, called_external_uris, jwt_auth
                        )
                    if break_off:
                        break
                else:

                    if isinstance(recursion_data, list):
                        for data in recursion_data:
                            data["_inclusions"] = {}
                            if isinstance(data[sub_field], list):
                                break_off, recursion_data = self.expand_array(
                                    data, sub_field, called_external_uris, jwt_auth
                                )
                            else:
                                break_off, recursion_data = self.expand_dict(
                                    data, sub_field, called_external_uris, jwt_auth
                                )
                        if break_off:
                            break

                    else:
                        recursion_data["_inclusions"] = {}
                        if isinstance(recursion_data[sub_field], list):
                            break_off, recursion_data = self.expand_array(
                                recursion_data,
                                sub_field,
                                called_external_uris,
                                jwt_auth,
                            )
                        else:
                            break_off, recursion_data = self.expand_dict(
                                recursion_data,
                                sub_field,
                                called_external_uris,
                                jwt_auth,
                            )
                        if break_off:
                            break

    def inclusions(self, serializer, request: DRFRequest):
        expand_filter = request.query_params.get("expand", "")
        if expand_filter:
            fields_to_expand = expand_filter.split(",")
            called_external_uris = {}
            for serialized_data in serializer.data:
                serialized_data["_inclusions"] = {}
                self.build_inclusions_schema(
                    serialized_data,
                    fields_to_expand,
                    called_external_uris,
                    request.jwt_auth,
                )

        return serializer


class ExpandFieldValidator:
    MAX_STEPS = 3
    REGEX = r"^[\w']+([.,][\w']+)*$"

    def _validate_fields_exist(self, expanded_fields, valid_inclusions):
        """Validate submitted expansion fields are recognized by API"""

        for expand_combination in expanded_fields.split(","):
            for field in expand_combination.split("."):
                if field not in valid_inclusions:
                    raise serializers.ValidationError(
                        {
                            "expand": _(
                                f"The submitted field {field} does not match valid expandable fields in API. Valid choices are {valid_inclusions}"
                            )
                        },
                        code="invalid-expand-field",
                    )

    def _validate_maximum_depth_reached(self, expanded_fields):
        """Validate maximum iterations to prevent infinite recursion"""
        for expand_combination in expanded_fields:
            if len(expand_combination.split(".")) > self.MAX_STEPS:
                raise serializers.ValidationError(
                    {
                        "expand": _(
                            f"The submitted fields have surpassed its maximum recursion limit of {self.MAX_STEPS}"
                        )
                    },
                    code="recursion-limit",
                )

    def _validate_regex(self, expanded_fields):
        if not re.match(self.REGEX, expanded_fields):
            raise serializers.ValidationError(
                {
                    "expand": _(
                        f"The submitted expand fields do not match the required regex of {self.REGEX}"
                    )
                },
                code="expand-format-error",
            )

    def list(self, request, *args, **kwargs):
        expand_filter = request.query_params.get("expand", "")

        if not request.query_params or not expand_filter:
            return super().list(request, *args, **kwargs)

        internal_uris = list(URI_NAME_TO_MODEL_NAME_MAPPER.keys())
        external_uris = EXTERNAL_URIS
        valid_inclusions = internal_uris + external_uris

        self._validate_regex(expand_filter)
        self._validate_fields_exist(expand_filter, valid_inclusions)
        self._validate_maximum_depth_reached(expand_filter)
        return super().list(request, *args, **kwargs)

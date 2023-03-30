from django.shortcuts import get_object_or_404
from rest_framework.response import Response
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

# zaaktype extern
# hoofdzaak extern
# deelzaken extern
# relevanteAndereZaken extern

EXTERNAL_URIS = ["zaaktype", "hoofdzaak", "deelzaken", "relevanteAndereZaken"]

URI_NAME_TO_MODEL_NAME_MAPPER = {"rollen": Rol,
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
URI_NAME_TO_SERIALIZER_MAPPER = {"rollen": RolSerializer,
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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer = self.inclusions(serializer, request)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        serializer = self.inclusions(serializer, request)
        return Response(serializer.data)

    def get_data(self, url, resource_to_expand, request):
        if resource_to_expand in EXTERNAL_URIS:
            return {}
        else:
            uuid = url.split("/")[-1]
            model = get_object_or_404(URI_NAME_TO_MODEL_NAME_MAPPER[resource_to_expand], uuid=uuid)
            serializer_exp_field = URI_NAME_TO_SERIALIZER_MAPPER[resource_to_expand](model,
                                                                                     context={
                                                                                         'request': request})
            return serializer_exp_field.data

    def impregnate_array(self, array_data, sub_field):
        if array_data[sub_field]:
            array_data["_inclusions"][sub_field] = []
            for url in array_data[sub_field]:
                data_from_url = self.get_data(url, sub_field, self.request)
                array_data["_inclusions"][sub_field].append(data_from_url)
                recursion_data = array_data["_inclusions"][sub_field]

            return recursion_data
        else:
            return False

    def impregnate_dict(self, array_data, sub_field):
        if array_data[sub_field]:
            data_from_url = self.get_data(array_data[sub_field], sub_field, self.request)
            array_data["_inclusions"][sub_field] = data_from_url
            return array_data["_inclusions"][sub_field]
        else:
            return False

    def build_inclusions_schema(self, result, fields_to_expand):
        for exp_field in fields_to_expand:
            for counter, sub_field in enumerate(exp_field.split(".")):
                if counter == 0:
                    if isinstance(result[sub_field], list):
                        recursion_data = self.impregnate_array(result, sub_field)
                        if not recursion_data:
                            break
                    else:
                        recursion_data = self.impregnate_dict(result, sub_field)
                        if not recursion_data:
                            break
                else:
                    if isinstance(recursion_data, list):
                        for data in recursion_data:
                            data["_inclusions"] = {}
                            if isinstance(data[sub_field], list):
                                recursion_data = self.impregnate_array(data, sub_field)
                                if not recursion_data:
                                    break

                            else:
                                recursion_data = self.impregnate_dict(data, sub_field)
                                if not recursion_data:
                                    break
                    else:
                        recursion_data["_inclusions"] = {}
                        if isinstance(recursion_data[sub_field], list):
                            recursion_data = self.impregnate_array(recursion_data, sub_field)
                            if not recursion_data:
                                break
                        else:
                            recursion_data = self.impregnate_dict(recursion_data, sub_field)
                            if not recursion_data:
                                break

        return result

    def inclusions(self, serializer, request):
        expand_filter = request.query_params.get("expand", "")
        fields_to_expand = expand_filter.split(",")

        for serialized_data in serializer.data:
            serialized_data["_inclusions"] = {}
            self.build_inclusions_schema(serialized_data, fields_to_expand)

        return serializer

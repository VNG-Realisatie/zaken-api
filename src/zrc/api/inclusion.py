from typing import List, Type

from django.conf import settings
from django.utils.module_loading import import_string

import requests
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework.serializers import (
    BaseSerializer,
    HyperlinkedRelatedField,
    Serializer,
    URLField,
)
from rest_framework_inclusions.core import InclusionLoader as _InclusionLoader, sort_key
from rest_framework_inclusions.renderer import (
    InclusionJSONRenderer as _InclusionJSONRenderer,
)


def get_component_name(serializer: Type[Serializer]) -> str:
    if getattr(serializer.Meta, "external", False):
        return serializer.Meta.model._meta.app_label
    return settings.PROJECT_NAME.lower()


def get_resource_name(serializer: Type[Serializer]) -> str:
    return serializer.Meta.model._meta.object_name


def get_inclusion_key(serializer: Type[Serializer]) -> str:
    component_label = get_component_name(serializer)
    model_name = serializer.Meta.model._meta.model_name
    return f"{component_label}:{model_name}"


class InclusionLoader(_InclusionLoader):
    # When doing inclusions, this indicates whether or not the entire path should
    # be used to include nested resources, e.g.: `?include=resource1.resource2` vs `?include=resource2`
    nested_inclusions_use_complete_path = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_external = set()

    def _has_been_seen_external(self, url: str) -> bool:
        if url in self._seen_external:
            return True
        self._seen_external.add(url)
        return False

    def get_model_key(self, obj, serializer):
        return get_inclusion_key(serializer)

    def _instance_inclusions(
        self, path, serializer, instance, inclusion_serializers=None
    ):
        # Use inclusion serializers derived from parent serializer
        inclusion_serializers = inclusion_serializers or getattr(
            serializer, "inclusion_serializers", {}
        )
        for name, field in serializer.fields.items():
            for entry in self._field_inclusions(
                path, field, instance, name, inclusion_serializers
            ):
                yield entry

    def _field_inclusions(self, path, field, instance, name, inclusion_serializers):
        # if this turns out to be None, we don't want to do a thing
        if instance is None:
            return
        new_path = path + (name,)
        if isinstance(field, BaseSerializer):
            for entry in self._sub_serializer_inclusions(new_path, field, instance):
                yield entry
            return
        inclusion_serializer = inclusion_serializers.get(name)
        if inclusion_serializer is None:
            return
        if isinstance(inclusion_serializer, str):
            inclusion_serializer = import_string(inclusion_serializer)
        for obj in self._some_related_field_inclusions(
            new_path, field, instance, inclusion_serializer
        ):
            yield obj, inclusion_serializer
            # when we do inclusions in inclusions, we base path off our
            # parent object path, not the sub-field

            # TODO option to derive serializers from parent serializer, instead of child
            # serializer
            nested_serializers = {
                field_name[len(name) + 1 :]: serializer
                for field_name, serializer in inclusion_serializers.items()
                if field_name.startswith(name)
            }

            nested_path = (
                new_path if self.nested_inclusions_use_complete_path else new_path[:-1]
            )
            for entry in self._instance_inclusions(
                nested_path,
                inclusion_serializer(instance=object),
                obj,
                inclusion_serializers=nested_serializers,
            ):
                yield entry

    def _external_url_field_inclusions(
        self, path, field, instance, inclusion_serializer
    ):
        value = field.get_attribute(instance)
        # In case it's an external resource
        if isinstance(value, str):
            if self._has_been_seen_external(value):
                return

            try:
                yield getattr(instance, field.field_name)  # ._initial_data
            except requests.RequestException:  # Something failed during fetching, ignore this instance
                return []
        else:
            for entry in self._primary_key_related_field_inclusions(
                path, field, instance, inclusion_serializer
            ):
                yield entry

    def _some_related_field_inclusions(
        self, path, field, instance, inclusion_serializer
    ):
        if self.allowed_paths is not None and path not in self.allowed_paths:
            return []

        if isinstance(field, URLField):
            return self._external_url_field_inclusions(
                path, field, instance, inclusion_serializer
            )
        return super()._some_related_field_inclusions(
            path, field, instance, inclusion_serializer
        )


class InclusionJSONRenderer(_InclusionJSONRenderer, CamelCaseJSONRenderer):
    """
    Ensure that the InclusionJSONRenderer produces camelCase and properly loads loose fk
    objects
    """

    loader_class = InclusionLoader
    response_data_key = "results"


def get_include_resources(serializer_class: Type[Serializer]) -> List[tuple]:
    resources = []
    for opt in serializer_class.inclusion_serializers.values():
        sub_serializer = import_string(opt) if isinstance(opt, str) else opt
        component = get_component_name(sub_serializer)
        resource = get_resource_name(sub_serializer)
        resources.append(
            (
                component,
                resource,
            )
        )
    return resources


def get_include_options_for_serializer(serializer_class: Serializer) -> List[tuple]:
    choices = [
        (
            opt,
            opt,
        )
        for opt in serializer_class.inclusion_serializers
    ]
    choices.append(
        (
            "*",
            "*",
        )
    )
    return choices


def external_serializer_factory(
    app_label: str, model_name: str
) -> Type[BaseSerializer]:
    """
    Create a custom serializer that simply retrieves external resources and returns that
    data when serializing
    """
    from zrc.api.validators import fetch_object

    ModelMeta = type(
        "_meta",
        (object,),
        {
            "app_label": app_label,
            "object_name": model_name,
            "model_name": model_name.lower(),
        },
    )
    Model = type("Model", (object,), {"_meta": ModelMeta})
    Meta = type("Meta", (object,), {"model": Model, "external": True})

    ExternalSerializer = type(
        "ExternalSerializer",
        (BaseSerializer,),
        {
            "Meta": Meta,
            "to_representation": lambda self, url: fetch_object(
                model_name.lower(), url
            ),
            "fields": {},  # Do not attempt to further include subresources from external resources
        },
    )
    return ExternalSerializer

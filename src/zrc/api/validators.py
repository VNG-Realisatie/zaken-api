import logging
import json
from typing import Iterable, Optional
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

import jq
import jsonschema
from rest_framework import serializers
from vng_api_common.models import APICredential
from vng_api_common.validators import (
    UniekeIdentificatieValidator as _UniekeIdentificatieValidator,
    URLValidator,
)

from .auth import get_auth
from ..datamodel.models.core import Zaak

logger = logging.getLogger(__name__)


def fetch_object(resource: str, url: str) -> dict:
    Client = import_string(settings.ZDS_CLIENT_CLASS)
    client = Client.from_url(url)
    client.auth = APICredential.get_auth(url)
    obj = client.retrieve(resource, url=url)
    return obj


class RolOccurenceValidator:
    """
    Validate that max x occurences of a field occur for a related object.

    Should be applied to the serializer class, not to an individual field
    """

    message = _("There are already {num} `{value}` occurences")

    def __init__(self, omschrijving_generiek: str, max_amount: int = 1):
        self.omschrijving_generiek = omschrijving_generiek
        self.max_amount = max_amount

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, "instance", None)

    def __call__(self, attrs):
        roltype = fetch_object("roltype", attrs["roltype"])

        attrs["omschrijving"] = roltype["omschrijving"]
        attrs["omschrijving_generiek"] = roltype["omschrijvingGeneriek"]

        if attrs["omschrijving_generiek"] != self.omschrijving_generiek:
            return

        is_noop_update = (
            self.instance
            and self.instance.omschrijving_generiek == self.omschrijving_generiek
        )
        if is_noop_update:
            return

        existing = (
            attrs["zaak"]
            .rol_set.filter(omschrijving_generiek=self.omschrijving_generiek)
            .count()
        )

        if existing >= self.max_amount:
            message = self.message.format(
                num=existing, value=self.omschrijving_generiek
            )
            raise serializers.ValidationError(
                {"roltype": message}, code="max-occurences"
            )


class UniekeIdentificatieValidator(_UniekeIdentificatieValidator):
    """
    Valideer dat de combinatie van bronorganisatie en zaak uniek is.
    """

    message = _("Deze identificatie bestaat al voor deze bronorganisatie")

    def __init__(self):
        super().__init__("bronorganisatie", "identificatie")


class NotSelfValidator:
    code = "self-forbidden"
    message = _("The '{field_name}' may not be a self-reference")

    def set_context(self, field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.field_name = field.field_name
        self.instance = getattr(field.root, "instance", None)

    def __call__(self, obj: models.Model):
        if self.instance == obj:
            message = self.message.format(field_name=self.field_name)
            raise serializers.ValidationError(message, code=self.code)


class HoofdzaakValidator:
    code = "deelzaak-als-hoofdzaak"
    message = _("Deelzaken van deelzaken wordt niet ondersteund.")

    def __call__(self, obj: models.Model):
        if obj.hoofdzaak_id is not None:
            raise serializers.ValidationError(self.message, code=self.code)


class HoofdZaaktypeRelationValidator:
    code = "invalid-deelzaaktype"
    message = _("Zaaktype niet vastgelegd in deelzaaktypen van hoofdzaak.zaaktype")

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, "instance", None)

    def __call__(self, attrs):
        if not attrs.get("hoofdzaak"):
            return

        hoofdzaak = attrs.get("hoofdzaak") or self.instance.hoofdzaak
        zaaktype = attrs.get("zaaktype") or self.instance.zaaktype

        hoofdzaaktype = fetch_object("zaaktype", hoofdzaak.zaaktype)

        if zaaktype not in hoofdzaaktype.get("deelzaaktypen", []):
            raise serializers.ValidationError(self.message, code=self.code)


class CorrectZaaktypeValidator:
    code = "zaaktype-mismatch"
    message = _("De referentie hoort niet bij het zaaktype van de zaak.")

    def __init__(self, url_field: str, zaak_field: str = "zaak", resource: str = None):
        self.url_field = url_field
        self.zaak_field = zaak_field
        self.resource = resource or url_field

    def __call__(self, attrs):
        url = attrs.get(self.url_field)
        zaak = attrs.get(self.zaak_field)
        if not url or not zaak:
            return

        obj = fetch_object(self.resource, url)
        if obj["zaaktype"] != zaak.zaaktype:
            raise serializers.ValidationError(self.message, code=self.code)


class ZaaktypeInformatieobjecttypeRelationValidator:
    code = "missing-zaaktype-informatieobjecttype-relation"
    message = _("Het informatieobjecttype hoort niet bij het zaaktype van de zaak.")

    def __init__(self, url_field: str, zaak_field: str = "zaak", resource: str = None):
        self.url_field = url_field
        self.zaak_field = zaak_field
        self.resource = resource or url_field

    def __call__(self, attrs):
        url = attrs.get(self.url_field)
        zaak = attrs.get(self.zaak_field)
        if not url or not zaak:
            return

        obj = fetch_object(self.resource, url)
        zaaktype = fetch_object("zaaktype", zaak.zaaktype)

        if obj["informatieobjecttype"] not in zaaktype["informatieobjecttypen"]:
            raise serializers.ValidationError(self.message, code=self.code)


class DateNotInFutureValidator:
    code = "date-in-future"
    message = _("Deze datum mag niet in de toekomst zijn")

    def __call__(self, value):
        now = timezone.now()
        if type(value) == date:
            now = now.date()

        if value > now:
            raise serializers.ValidationError(self.message, code=self.code)


class ZaakBesluitValidator:
    message = _(
        "Zaak has related Besluit(en), these relations should be deleted "
        "before deleting the Zaak"
    )
    code = "related-besluiten"

    def __call__(self, zaak: Zaak):
        if zaak.zaakbesluit_set.exists():
            raise serializers.ValidationError(self.message, code=self.code)


class EitherFieldRequiredValidator:
    default_message = _("One of %(fields)s must be provided")
    default_code = "invalid"

    def __init__(self, fields: Iterable[str], message: str = "", code: str = ""):
        self.fields = fields
        self.message = (message or self.default_message) % {"fields": ", ".join(fields)}
        self.code = code or self.default_code

    def __call__(self, attrs: dict):
        values = [attrs.get(field, None) for field in self.fields]
        if not any(values):
            raise serializers.ValidationError(self.message, code=self.code)


class JQExpressionValidator:
    message = _("This is not a valid jq expression.")
    code = "invalid"

    def __call__(self, value: str):
        try:
            jq.compile(value)
        except ValueError:
            raise serializers.ValidationError(self.message, code=self.code)


class ObjectTypeOverigeDefinitieValidator:
    code = "invalid"

    def __call__(self, attrs: dict):
        object_type_overige_definitie: Optional[dict] = attrs.get("object_type_overige_definitie")
        object_url: str = attrs.get("object", "")

        if not object_type_overige_definitie:
            return

        # object type overige definitie can only be used with object URL reference
        if object_type_overige_definitie and not object_url:
            raise serializers.ValidationError(
                {"object_url": _(
                    "Indien je `objectTypeOverigeDefinitie` gebruikt, dan moet je "
                    "een OBJECT url opgeven."
                )},
                code="required"
            )

        if attrs.get("object_identificatie"):
            logger.warning("Both object URL and objectIdentificatie supplied, clearing the latter.")
            attrs["object_identificatie"] = None

        # now validate the schema
        url_validator = URLValidator(get_auth=get_auth)

        response = url_validator(object_type_overige_definitie["url"])
        try:
            object_type = response.json()
        except json.JSONDecodeError:
            raise serializers.ValidationError({
                "objectTypeOverigeDefinitie.url": _("The endpoint did not return valid JSON.")
            }, code="invalid")

        schema_jq = jq.compile(object_type_overige_definitie["schema"])
        record_data_jq = jq.compile(object_type_overige_definitie["object_data"])

        try:
            json_schema_definition = schema_jq.input(object_type).first()
        except ValueError:
            json_schema_definition = None

        if not json_schema_definition:
            raise serializers.ValidationError({
                "objectTypeOverigeDefinitie.schema": _("No schema was found at the specified path.")
            }, code="invalid")

        # validate the object
        object_response = url_validator(object_url)
        try:
            object_resource = object_response.json()
        except json.JSONDecodeError:
            raise serializers.ValidationError({
                "object": _("The endpoint did not return valid JSON.")
            }, code="invalid")

        try:
            object_data = record_data_jq.input(object_resource).first()
        except ValueError:
            object_data = None
        if object_data is None:
            raise serializers.ValidationError({
                "objectTypeOverigeDefinitie.objectData": _("No data was found at the specified path.")
            }, code="invalid")

        # validate the schema
        try:
            jsonschema.validate(instance=object_data, schema=json_schema_definition)
        except jsonschema.ValidationError:
            raise serializers.ValidationError({
                "object": _("The object data does not match the specified schema.")
            }, code="invalid-schema")

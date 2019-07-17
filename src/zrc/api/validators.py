from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from vng_api_common.models import APICredential
from vng_api_common.validators import (
    UniekeIdentificatieValidator as _UniekeIdentificatieValidator
)


class RolOccurenceValidator:
    """
    Validate that max x occurences of a field occur for a related object.

    Should be applied to the serializer class, not to an individual field
    """
    message = _('There are already {num} `{value}` occurences')

    def __init__(self, omschrijving_generiek: str, max_amount: int=1):
        self.omschrijving_generiek = omschrijving_generiek
        self.max_amount = max_amount

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def __call__(self, attrs):
        roltype = attrs["roltype"]

        Client = import_string(settings.ZDS_CLIENT_CLASS)
        client = Client.from_url(roltype)
        client.auth = APICredential.get_auth(roltype)
        roltype = client.retrieve("roltype", url=roltype)

        attrs["omschrijving"] = roltype["omschrijving"]
        attrs["omschrijving_generiek"] = roltype["omschrijvingGeneriek"]

        if attrs['omschrijving_generiek'] != self.omschrijving_generiek:
            return

        is_noop_update = self.instance and self.instance.omschrijving_generiek == self.omschrijving_generiek
        if is_noop_update:
            return

        existing = (
            attrs['zaak']
            .rol_set
            .filter(omschrijving_generiek=self.omschrijving_generiek)
            .count()
        )

        if existing >= self.max_amount:
            message = self.message.format(num=existing, value=self.omschrijving_generiek)
            raise serializers.ValidationError({
                'roltype': message
            }, code='max-occurences')


class UniekeIdentificatieValidator(_UniekeIdentificatieValidator):
    """
    Valideer dat de combinatie van bronorganisatie en zaak uniek is.
    """
    message = _('Deze identificatie bestaat al voor deze bronorganisatie')

    def __init__(self):
        super().__init__('bronorganisatie', 'identificatie')


class NotSelfValidator:
    code = 'self-forbidden'
    message = _("The '{field_name}' may not be a self-reference")

    def set_context(self, field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.field_name = field.field_name
        self.instance = getattr(field.root, 'instance', None)

    def __call__(self, obj: models.Model):
        if self.instance == obj:
            message = self.message.format(field_name=self.field_name)
            raise serializers.ValidationError(message, code=self.code)


class HoofdzaakValidator:
    code = 'deelzaak-als-hoofdzaak'
    message = _("Deelzaken van deelzaken wordt niet ondersteund.")

    def __call__(self, obj: models.Model):
        if obj.hoofdzaak_id is not None:
            raise serializers.ValidationError(self.message, code=self.code)

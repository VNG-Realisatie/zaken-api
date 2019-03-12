from django.db import models
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from vng_api_common.validators import (
    UniekeIdentificatieValidator as _UniekeIdentificatieValidator
)


class RolOccurenceValidator:
    """
    Validate that max x occurences of a field occur for a related object.

    Should be applied to the serializer class, not to an individual field
    """
    message = _('There are already {num} `{value}` occurences')

    def __init__(self, rolomschrijving: str, max_amount: int=1):
        self.rolomschrijving = rolomschrijving
        self.max_amount = max_amount

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def __call__(self, attrs):
        if attrs['rolomschrijving'] != self.rolomschrijving:
            return

        is_noop_update = self.instance and self.instance.rolomschrijving == self.rolomschrijving
        if is_noop_update:
            return

        existing = (
            attrs['zaak']
            .rol_set
            .filter(rolomschrijving=self.rolomschrijving)
            .count()
        )

        if existing >= self.max_amount:
            message = self.message.format(num=existing, value=self.rolomschrijving)
            raise serializers.ValidationError({
                'rolomschrijving': message
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

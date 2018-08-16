from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


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


class UniekeIdentificatieValidator:
    """
    Valideer dat de combinatie van bronorganisatie en zaak uniek is.
    """
    message = _('Deze identificatie bestaat al voor deze bronorganisatie')

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)
        self.model = serializer.Meta.model

    def __call__(self, attrs: dict):
        identificatie = attrs.get('identificatie')
        if not identificatie:
            # identification is being generated, and the generation checks for
            # uniqueness
            return

        bronorganisatie = attrs.get('bronorganisatie')
        pk = self.instance.pk if self.instance else None

        # if we're updating an instance, setting the current values will not
        # trigger an error because the instance-to-be-updated is excluded from
        # the queryset. If either bronorganisatie or identificatie changes,
        # and it already exists, it will raise a validation error
        combination_exists = (
            self.model.objects
            # in case of an update, exclude the current object. for a create, this
            # will be None
            .exclude(pk=pk)
            .filter(bronorganisatie=bronorganisatie, identificatie=identificatie)
            .exists()
        )

        if combination_exists:
            raise serializers.ValidationError({
                'identificatie': self.message
            }, code='identificatie-niet-uniek')

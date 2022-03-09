from django import forms

from zrc.datamodel.models.core import Zaak
from zrc.utils.forms import GegevensGroepTypeMixin


class ZakenForm(GegevensGroepTypeMixin, forms.ModelForm):
    class Meta:
        fields = "__all__"
        model = Zaak

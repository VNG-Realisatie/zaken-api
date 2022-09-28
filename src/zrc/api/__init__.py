default_app_config = "zrc.api.apps.ZRCApiConfig"

from vng_api_common.extensions.fields.duration import DurationFieldExtension
from vng_api_common.extensions.fields.geojson import GeometryFieldExtension
from vng_api_common.extensions.fields.hyperlink_identity import (
    HyperlinkedIdentityFieldExtension,
)
from vng_api_common.extensions.fields.hyperlinked_related import (
    HyperlinkedRelatedFieldExtension,
)
from vng_api_common.extensions.fields.many_related import ManyRelatedFieldExtension
from vng_api_common.extensions.fields.read_only import ReadOnlyFieldExtension
from vng_api_common.extensions.filters.query import FilterExtension
from vng_api_common.extensions.serializers.gegevensgroep import GegevensGroepExtension
from vng_api_common.extensions.serializers.polymorphic import (
    PolymorphicSerializerExtension,
)

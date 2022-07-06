from datetime import date

from django.utils import timezone

import factory
import factory.fuzzy
from vng_api_common.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduiding,
    ZaakobjectTypes,
)

from ..constants import AardZaakRelatie


class ZaakFactory(factory.django.DjangoModelFactory):
    zaaktype = factory.Faker("url")
    vertrouwelijkheidaanduiding = factory.fuzzy.FuzzyChoice(
        choices=VertrouwelijkheidsAanduiding.values
    )
    registratiedatum = factory.Faker("date_this_month", before_today=True)
    startdatum = factory.Faker("date_this_month", before_today=True)
    bronorganisatie = factory.Faker("ssn", locale="nl_NL")
    verantwoordelijke_organisatie = factory.Faker("ssn", locale="nl_NL")

    class Meta:
        model = "datamodel.Zaak"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )
        closed = factory.Trait(
            einddatum=factory.LazyFunction(date.today),
            status_set=factory.RelatedFactory(
                "zrc.datamodel.tests.factories.StatusFactory",
                factory_related_name="zaak",
            ),
        )


class ZaakInformatieObjectFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    informatieobject = factory.Faker("url")

    class Meta:
        model = "datamodel.ZaakInformatieObject"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )


class ZaakEigenschapFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    eigenschap = factory.Faker("url")
    _naam = factory.Faker("word")
    waarde = factory.Faker("word")

    class Meta:
        model = "datamodel.ZaakEigenschap"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )


class ZaakObjectFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    object = factory.Faker("url")

    # Excluded: overige
    object_type = factory.fuzzy.FuzzyChoice(choices=list(ZaakobjectTypes.values)[:-1])

    class Meta:
        model = "datamodel.ZaakObject"


class RolFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    betrokkene = factory.Faker("url")
    betrokkene_type = factory.fuzzy.FuzzyChoice(RolTypes.values)
    roltype = factory.Faker("url")
    omschrijving = factory.Faker("word")
    omschrijving_generiek = factory.fuzzy.FuzzyChoice(RolOmschrijving.values)

    class Meta:
        model = "datamodel.Rol"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )


class StatusFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    statustype = factory.Faker("url")
    datum_status_gezet = factory.Faker("date_time_this_month", tzinfo=timezone.utc)

    class Meta:
        model = "datamodel.Status"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )


class ResultaatFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    resultaattype = factory.Faker("url")

    class Meta:
        model = "datamodel.Resultaat"

    class Params:
        with_etag = factory.Trait(
            _etag=factory.PostGenerationMethodCall("calculate_etag_value")
        )


class KlantContactFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    identificatie = factory.Sequence(lambda n: f"{n}")
    datumtijd = factory.Faker("date_time_this_month", tzinfo=timezone.utc)

    class Meta:
        model = "datamodel.KlantContact"


class ZaakBesluitFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    besluit = factory.Faker("url")

    class Meta:
        model = "datamodel.ZaakBesluit"


class RelevanteZaakRelatieFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    url = factory.Faker("url")
    aard_relatie = AardZaakRelatie.vervolg

    class Meta:
        model = "datamodel.RelevanteZaakRelatie"


class WozWaardeFactory(factory.django.DjangoModelFactory):
    zaakobject = factory.SubFactory(ZaakObjectFactory)

    class Meta:
        model = "datamodel.WozWaarde"


class ZaakContactMomentFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    contactmoment = factory.Faker("url")

    class Meta:
        model = "datamodel.ZaakContactMoment"


class ZaakVerzoekFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    verzoek = factory.Faker("url")

    class Meta:
        model = "datamodel.ZaakVerzoek"

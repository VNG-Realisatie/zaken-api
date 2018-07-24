import factory
import factory.fuzzy


class ZaakFactory(factory.django.DjangoModelFactory):
    zaaktype = factory.Faker('url')
    registratiedatum = factory.Faker('date_this_month', before_today=True)
    bronorganisatie = factory.Faker('ssn', locale='nl_NL')

    class Meta:
        model = 'datamodel.Zaak'


class OrganisatorischeEenheidFactory(factory.django.DjangoModelFactory):
    organisatie_eenheid_identificatie = factory.Faker('word')
    # TODO: correct format, see VIPS / BSN validation
    organisatie_identificatie = factory.fuzzy.FuzzyInteger(low=11111111, high=999999999)
    datum_ontstaan = factory.Faker('date_this_decade')
    naam = factory.Faker('bs')

    class Meta:
        model = 'datamodel.OrganisatorischeEenheid'


class ZaakEigenschapFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    eigenschap = factory.Faker('url')
    waarde = factory.Faker('word')

    class Meta:
        model = 'datamodel.ZaakEigenschap'

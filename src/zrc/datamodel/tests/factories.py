import factory
import factory.fuzzy


class ZaakFactory(factory.django.DjangoModelFactory):
    zaaktype = factory.Faker('url')
    registratiedatum = factory.Faker('date_this_month', before_today=True)
    bronorganisatie = factory.Faker('ssn', locale='nl_NL')

    class Meta:
        model = 'datamodel.Zaak'


class ZaakEigenschapFactory(factory.django.DjangoModelFactory):
    zaak = factory.SubFactory(ZaakFactory)
    eigenschap = factory.Faker('url')
    waarde = factory.Faker('word')

    class Meta:
        model = 'datamodel.ZaakEigenschap'

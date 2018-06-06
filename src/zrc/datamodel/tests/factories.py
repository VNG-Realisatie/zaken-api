import factory


class ZaakFactory(factory.django.DjangoModelFactory):
    zaaktype = factory.Faker('url')

    class Meta:
        model = 'datamodel.Zaak'

===========
Wijzigingen
===========

0.6.0 (2018-11-01)
==================

Feature release: zaak afsluiten & status filteren

* ``Zaak.einddatum`` is alleen-lezen geworden
* ``Zaak.einddatum`` wordt gezet indien de gezette status de eindstatus is
* ``Status`` list endpoint accepteert filters op ``zaak`` en ``statusType``

0.5.2 (2018-10-22)
==================

Bugfix in bugfix release

* Commit vergeten te pushen voor: Docker image fixed: ontbrekende
  ``swagger2openapi`` zit nu in image.

0.5.1 (2018-10-19)
==================

Bugfix release i.v.m. zaakinformatieobjecten

* ``zaakinformatieobject_destroy`` operatie verwijderd. Deze bestaat ook niet in
  het DRC namelijk.
* ``zds-schema`` versiebump - DNS errors worden nu HTTP 400 in plaats van
  HTTP 500 bij url-validatie.
* Fix in ``ZaakInformatieObject`` serializer door het ontbreken van een detail
  URL.
* Docker image fixed: ontbrekende ``swagger2openapi`` zit nu in image.

0.5.0 (2018-10-03)
==================

Deze release heeft backwards incompatible wijzigingen op gebied van
zaakinformatieobjecten.

* licentiebestand toegevoegd (Boris van Hoytema <boris@publiccode.net>)
* toevoeging API resources documentatie (markdown uit API spec)
* correctie op error-response MIME-types
* #166 - expliciet zaak-informatieobject relatieresource toegevoegd, met
  validatie-implementaties

0.4.0 (2018-09-06)
==================

* nieuwe velden (waaronder ``Kenmerken``) toegevoegd aan de ZAAK-resource
  (vng-Realisatie/gemma-zaken#153)
* DSO API-50: implementatie formaat van error-responses & documentatie (
  vng-Realisatie/gemma-zaken#130)
* Validatie (business logic) toegevoegd:
    * ``zaaktype`` URL referentie moet een geldige URL zijn
    * strengere validatie wordt gradueel ingevoerd
* Uniciteit validator (combinatie ``bronorganisatie`` en ``identificatie``)
  bouwt op generieke validator uit ``gemma-zaken-common``.

0.3.1 (2018-08-20)
==================

* Validatie toegevoegd op aantal initiators/coordinatoren voor een zaak
* ``rolomschrijvingGeneriek`` weggehaald
* validatie op unieke ZAAK.``identificatie`` binnen een bronorganisatie

0.3.0 (2018-08-16)
==================

* Unit test toegevoegd voor vng-Realisatie/gemma-zaken#163

Breaking changes
----------------

* Hernoem ``zaakidentificatie`` -> ``identificatie`` cfr. de design decisions


0.2.5 (2018-08-15)
==================

* Fixes in CI
* README netjes gemaakt
* Aanpassingen aan BETROKKENEn bij ZAAKen

    * rol betrokkene is nu een referentie naar een andere resource via URL,
      mogelijks in een externe registratie (zoals BRP)
    * ``OrganisatorischeEenheid`` verwijderd door bovenstaande
    * ``startdatum``, ``einddatum`` en ``einddatum_gepland`` velden
      toegevoegd
    * ``registratiedatum`` optioneel gemaakt, met een default van 'vandaag'
      indien niet opgegeven
    * Polymorfisme mechanischme toegevoegd voor betrokkenen en zaakobjecten
    * Filter parameters toegevoegd

0.2.5 (2018-07-30)
==================

Fixes in OAS 3.0 schema op gebied van GeoJSON definities.

0.2.4 (2018-07-30)
==================

Dependency ``zds_schema`` versie verhoogd, met een fix voor de ``required`` key
in het OAS 3.0 schema.

0.2.3 (2018-07-25)
==================

Uitbreiding en aanpassingen API spec

* alle API url parameters zijn nu UUIDs in plaats van database primary
  keys

* ``<resource>_list`` operations toegevoegd (volgende release zal hiervoor
  nested resources gebruiken)


0.1 (2018-06-26)
================

* Initial release.

===========
Wijzigingen
===========

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

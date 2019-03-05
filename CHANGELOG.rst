===========
Wijzigingen
===========

0.10.2 (2019-03-05)
===================

Bugfix release

* Bumped gemma-zds-client via zds-schema

0.10.1 (2019-02-27)
===================

Bugfix release

* Fixed operation/scope mapping

0.10.0 (2019-02-27)
===================

Archiving feature release

Set the ``Resultaat`` for a ``Zaak`` to trigger the archiving machinery.

* Requires the ZTC to be configured correctly.
* Requires ZTC 0.9.0 or higher

Changes
-------

* added ``Resultaat`` resource
* added ``Zaak.archiefnominatie`` + filter params
* added ``Zaak.archiefactiedatum`` + filter params
* added ``Zaak.archiefstatus`` + filter params
* added ``Zaak.resultaat`` URL-reference
* added read-only ``Eigenschap.naam`` (taken from ZTC)
* added explicit ``duration`` format to duration fields

Notes
-----

The following ``afleidingswijze``s for ``brondatum`` are not implemented yet:

* ``gerelateerde_zaak``
* ``ingangsdatum_besluit``
* ``vervaldatum_besluit``

0.9.2 (2019-02-07)
==================

Documentation improvements

* #620 - better/added documentation for various resource operations
* Bumped to bugfix releases of Django and zds-schema

0.9.1 (2019-01-30)
==================

Modified data migration to set ``Zaak.vertrouwelijkheidaanduiding`` based
on zaaktype so that corrupt data doesn't crash the migrations.

0.9.0 (2019-01-30)
==================

API maturity update

See https://github.com/VNG-Realisatie/gemma-zaken/pull/673 for a more
verbose description of the changes.

* Documentation improvements
* Fixed resetting ``Zaak.einddatum`` if a status other than the end-status is
  set after closing the ``Zaak`` (#660)
* Added validation on related ``Informatieobject``s when a ``Zaak`` is being
  closed (#549)
* Added more attributes (#549)
    * ``Zaak.productenOfDiensten``
    * ``Zaak.publicatiedatum``
    * ``Zaak.communicatiekanaal``
    * ``Zaak.vertrouwelijkheidaanduiding`` - always set, default derived from
      ``Zaak.zaaktype.vertrouwelijkheidaanduiding``
    * ``Zaak.resultaattoelichting``
    * ``Zaak.betalingsindicatie``
    * ``Zaak.laatsteBetaaldatum`` + validation with ``Zaak.betalingsindicatie``
      value (no value is allowed if payment is irrelevant)
    * ``Zaak.verlenging`` - which is a nested object. ``null`` is accepted to
      leave the value empty. Pending change to calculate ``Zaak.einddatumGepland``
      from this.
    * ``Zaak.opschorting`` added as nested object
    * ``ZAAK.selectielijstklasse`` added, should point to
      https://ref.tst.vng.cloud/referentielijsten API
    * ``Zaak.hoofdzaak`` and ``Zaak.deelzaken`` attributes + validation logic
      added.
    * ``ZAAK.andereGerelateerdeZaken``
* Bumped a bunch of library versions (zds-schema, gemma-zds-client)
* Improved help text of duration fields in the admin

Breaking changes
----------------

* The ``Content-Crs`` header is now required for write-requests, and
  CRS-negotiation is performed on this. Update all create, update and partial
  update calls to include this header, even if you are not submitting geo
  data. (#639)

0.8.6 (2018-12-13)
==================

Bump Django and urllib

* urllib3<=1.22 has a CVE
* use latest patch release of Django 2.0

0.8.5 (2018-12-11)
==================

Small bugfixes

* Fixed validator using newer gemma-zds-client
* Added a name for the session cookie to preserve sessions on the same domain
  between components.
* Added missing Api-Version header
* Added missing Location header to OAS


0.8.2 (2018-12-04)
==================

Client method signature fixed

0.8.1 (2018-12-03)
==================

Refs. #565 -- change URL reference to RSIN

0.8.0 (2018-11-27)
==================

Stap naar volwassenere API

* Update naar recente zds-schema versie
* HTTP 400 errors op onbekende/invalide filter-parameters
* Docker container beter te customizen via environment variables

Breaking change
---------------

De ``Authorization`` headers is veranderd van formaat. In plaats van ``<jwt>``
is het nu ``Bearer <jwt>`` geworden.

0.7.1 (2018-11-22)
==================

DSO API-srategie fix

Foutberichten bevatten een `type` key. De waarde van deze key begint niet
langer incorrect met `"URI: "`.

0.7.0 (2018-11-21)
==================

Autorisatie-feature release

* Scopes toegevoegd: ``ZAKEN_CREATE``, ``STATUSSEN_TOEVOEGEN``, ``ZAKEN_ALLES_LEZEN``
* Autorisatie-informatie toegevoegd aan API spec
* Auth/Autz via middleware en JWT toegevoegd
* Documentatie van scopes toegevoegd op ``http://localhost:8000/ref/scopes/``
* Maak authenticated calls naar ZTC
* JWT client/secret management toegevoegd

Breaking changes
----------------

Door autorisatie toe te voegen zijn bestaande endpoints niet langer functioneel
zonder een geldige ``Authentication`` header. Je kan de `token issuer`_ gebruiken
om geldige credentials te verkrijgen.

Kleine wijzigingen
------------------

* dwing gebruik van timeze-aware datetimes af (hard error in dev)
* OAS 3.0 versie wordt nu geserveerd vanaf ``/api/v1/schema/openapi.yaml?v=3``.
  Zonder ``?v=3`` querystring krijg je nog steeds Swagger 2.0.

.. _token issuer: https://ref.tst.vng.cloud/tokens/

0.6.1 (2018-11-16)
==================

Added CORS-headers

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

===========
Wijzigingen
===========

0.19.1 (2019-07-02)
===================

Added a data migration to handle the flattened ZTC urls.

0.19.0 (2019-07-01)
===================

Added support for all kinds of ``Zaakobjecten``.

Following the "Grenzen van het API landschap" design document,
the possible RGBZ/RSGB objects that can be related to a ``Zaak`` have been
implemented.

0.18.2 (2019-06-28)
===================

Fixed a bug in the migrations

0.18.1 (2019-06-28)
===================

Small fixes:

* Fix changelog version
* Fix display of version information (git sha was missing)

0.18.0 (2019-06-28)
===================

Third release towards release candidate

* Included version information in Docker image, which is now displayed in the
  footer. Version info is the git sha and API version number.
* Enabled explicit OAS 3.x version test so that no more OAS 2.x is served
* Bumped to latest vng-api-common
* If no ``Zaak.identificatie`` is given, the generated identification is now
  more human-readable.
* Added filter parameters on ``betrokkeneIdentificatie``

Breaking changes
----------------

* Added document validation when closing a ``Zaak``: all documents must be
  unlocked
* Renamed identifying fields of ``Rol.betrokkene``
* Changed ``Zaak.relevanteAndereZaken`` from a list of URLs to a list of
  objects (``url`` + ``aardRelatie``) so that more meta information can be
  provided.

0.17.0 (2019-06-18)
===================

Second release towards release candidate

* Added filters to ``Zaak`` list endpoint: ``startdatum`` variations (equal,
  greater then, etc.)
* Added fixture loading to container start script
* Added more tests
* Added models for ``Betrokkene`` types - see "Grenzen van het API-Landschap"
* Added polymorphism to ``Betrokkene`` serializer
* Fixed a bug on ZIO deletion w/r to DRC validation
* Fixed docker image build

Breaking changes
----------------

* Re-enabled validation of ``ZaakBesluit.besluit``. Requires BRC >= 0.11.1

0.16.0 (2019-05-22)
===================

First release towards release candidate

* Added representation function to all models
* Fixed fetching ``relevanteAndereZaken`` with correct headers
* Translated API docs
* Added ``ZaakBesluit`` to easily retrieve besluiten from the ``Zaak`` object.
  Relation is created by BRC.
* Applied fixes to nested ``GegevensGroep``-validation
* Enabled config view to diagnose problems
* Bumped to Django 2.2 (LTS)
* Removed unused dependencies

Breaking changes
----------------

* Moved relation information ``ZaakInformatieObject`` to ZRC. Relations are now
  created here instead of DRC, and are synced from ZRC to DRC. It is now a
  root resource instead of a subresource.

0.15.0 (2019-05-22)
===================

Authorizations V2 and audittrail release - breaking changes!

* Reworked authorizations - authorizations are now retrieved from the
  authorizations component (AC) and need to be configured there. You can use
  the token tool for this.
* Authorizations are now more fine-grained, scopes/maximum
  vertrouwelijkheidaanduiding apply to a ``zaaktype``, which filters data at
  the source. Only ``zaken`` of the ``zaaktype``s you're authorized for are
  returned. The same logic applies to related data, such as ``status``.
* Creation of ``zaken`` of a ``zaaktype`` you are not authorized for is no
  longer allowed (it results in an HTTP 403).
* Renamed scopes - the ``zds.scopes`` prefix is dropped.
* Added scope-based protection on resources/operations where they were missing
* Improved URL-based reference validation
* Added audittrails - actions are now logged in an audittrail and they can be
  retrieved for a ``zaak``.  Consumers need to/should:

    * include the ``client_id`` in the JWT (always needed)
    * include the ``X-Audit-Toelichting`` header
    * include the ``user_id`` claim in the JWT, or use the
      ``X-Nlx-Request-User-Id`` header, which should uniquely identify the
      end-user (in combination with the application ID)
    * include the ``user_representation`` claim in the JWT for a human-readable
      representation of the end-user


0.14.0 (2019-04-24)
===================

Cleaned up some loose ends

* Bumped Jinja2 dep (security release)
* Improved accessibility in secret management [admin]
* Added a test case for complexere GeoJSON
* Implemented re-opening of ``Zaken`` & added a new scope

0.13.4 (2019-04-18)
===================

Fixed a bug when setting ``Zaak.opschorting.indicatie`` to ``false``

0.13.3 (2019-04-17)
===================

Fixed an issue with duration validation

0.13.2 (2019-04-17)
===================

Default value NRC api root fixed.

0.13.1 (2019-04-16)
===================

Bugfix in ``brondatum`` calculations

0.13.0 (2019-04-16)
===================

API-lab release

* Improved homepage layout, using vng-api-common boilerplate
* Bumped to latest bugfix release of gemma-zds-client
* Fixed a bug preventing ``ZaakInformatieObject`` being created/deleted

Breaking changes
----------------

* Flattened the ``kenmerken`` in notifications sent from a list of objects with
  one key-value to a single object with multiple key-value pairs.
  Requires the NC to be at version 0.4.0 or higher.

  Old:

  .. code-block:: json

  {
    "kenmerken": [
      {"key1": "value1"},
      {"key2": "value2"},
    ]
  }

  New:

  .. code-block:: json

  {
    "kenmerken": {
      "key1": "value1",
      "key2": "value2",
    }
  }

* ``Zaak.archiefactiedatum`` is now calculated when the final status is being
  set, instead of when the ``Resultaat`` is created. This effectively changes
  the order of operations needed:

  1. First, set a ``Resultaat`` on a ``Zaak``
  2. Then, create an end-status for a ``Zaak`` to close the ``Zaak``

  A ``Zaak`` cannot be closed if no ``Resultaat`` has been set.

* It is now no longer possible to modify a closed ``Zaak``, unless you include
  the appropriate scope (``SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN``).

0.12.2 (2019-04-04)
===================

Fixed another vng-api-common notifications bug

0.12.1 (2019-04-04)
===================

Fixed notifications throwing 500 errors

Notifications resolve internal paths to resources, which had a bug when
components are hosted on subpaths. This has been fixed in vng-api-common.

0.12.0 (2019-03-27)
===================

Added support for notifications

* Switched to vng-api-common, which is the rebrand of zds-schema
* Fixed CRS-parameters ending up in API spec for ``DELETE`` actions
* Added django-solo to store configuration
* Added the notifications support
    * NC configuration in database possible
    * viewset mixins for API endpoints, to publish notifications
    * callback endpoint available on ``/api/v1/callbacks``, to receive notifications
    * management command ``register_kanaal`` available to register the exchange
    * added documentation page for kanalen/exchanges

0.11.2 (2019-03-11)
===================

Increased URL-length validation from 200 to 1000 characters

0.11.1 (2019-03-08)
===================

Fixed a bug where pagination parameters were incorrectly marked as invalid
params.

0.11.0 (2019-03-08)
===================

Added pagination to the ``/zaken`` endpoint

Breaking changes:
-----------------

* Response body of ``/zaken`` and ``/zaken/_zoek`` endpoints is now on object
  instead of a list. The list with results can be found in the ``results`` key.
* Pagination defaults to a 100 objects, so to read all results, you'll have to
  fetch the other pages and/or supply a bigger ``page_size`` parameter.

Minor changes
-------------

* Updated to security release of Django
* Included URL to the EUPL-1.2 License in the API documentation

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

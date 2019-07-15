# Resources

Dit document beschrijft de (RGBZ-)objecttypen die als resources ontsloten
worden met de beschikbare attributen.


## KlantContact

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/klantcontact)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| identificatie | De unieke aanduiding van een KLANTCONTACT | string | nee | C​R​U​D |
| datumtijd | De datum en het tijdstip waarop het KLANTCONTACT begint | string | ja | C​R​U​D |
| kanaal | Het communicatiekanaal waarlangs het KLANTCONTACT gevoerd wordt | string | nee | C​R​U​D |

## Resultaat

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/resultaat)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| resultaatType | URL naar het resultaattype uit het ZTC. | string | ja | C​R​U​D |
| toelichting | Een toelichting op wat het resultaat van de zaak inhoudt. | string | nee | C​R​U​D |

## Rol

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/rol)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| betrokkene | Een betrokkene gerelateerd aan een zaak | string | nee | C​R​U​D |
| betrokkeneType | Soort betrokkene | string | ja | C​R​U​D |
| rolomschrijving | Algemeen gehanteerde benaming van de aard van de ROL | string | ja | C​R​U​D |
| roltoelichting |  | string | ja | C​R​U​D |
| registratiedatum | De datum waarop dit object is geregistreerd. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| indicatieMachtiging | Indicatie_machtiging

Uitleg bij mogelijke waarden:

* `gemachtigde` - De betrokkene in de rol bij de zaak is door een andere betrokkene bij dezelfde zaak gemachtigd om namens hem of haar te handelen
* `machtiginggever` - De betrokkene in de rol bij de zaak heeft een andere betrokkene bij dezelfde zaak gemachtigd om namens hem of haar te handelen | string | nee | C​R​U​D |

## SubVerblijfBuitenland

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/subverblijfbuitenland)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| lndLandcode | De code, behorende bij de landnaam, zoals opgenomen in de Land/Gebied-tabel van de BRP. | string | ja | C​R​U​D |
| lndLandnaam | De naam van het land, zoals opgenomen in de Land/Gebied-tabel van de BRP. | string | ja | C​R​U​D |
| subAdresBuitenland_1 |  | string | nee | C​R​U​D |
| subAdresBuitenland_2 |  | string | nee | C​R​U​D |
| subAdresBuitenland_3 |  | string | nee | C​R​U​D |

## Status

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/status)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| statusType | URL naar het statustype uit het ZTC. | string | ja | C​R​U​D |
| datumStatusGezet | De datum waarop de ZAAK de status heeft verkregen. | string | ja | C​R​U​D |
| statustoelichting | Een, voor de initiator van de zaak relevante, toelichting op de status van een zaak. | string | nee | C​R​U​D |

## ZaakInformatieObject

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakinformatieobject)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| informatieobject | URL-referentie naar het informatieobject in het DRC, waar ook de relatieinformatie opgevraagd kan worden. | string | ja | C​R​U​D |
| zaak |  | string | ja | C​R​U​D |
| aardRelatieWeergave |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| titel | De naam waaronder het INFORMATIEOBJECT binnen het OBJECT bekend is. | string | nee | C​R​U​D |
| beschrijving | Een op het object gerichte beschrijving van de inhoud vanhet INFORMATIEOBJECT. | string | nee | C​R​U​D |
| registratiedatum | De datum waarop de behandelende organisatie het INFORMATIEOBJECT heeft geregistreerd bij het OBJECT. Geldige waardes zijn datumtijden gelegen op of voor de huidige datum en tijd. | string | nee | ~~C~~​R​~~U~~​~~D~~ |

## ZaakObject

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakobject)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| object | URL naar de resource die het OBJECT beschrijft. | string | nee | C​R​U​D |
| relatieomschrijving | Omschrijving van de betrekking tussen de ZAAK en het OBJECT. | string | nee | C​R​U​D |
| type | Beschrijft het type object gerelateerd aan de zaak | string | ja | C​R​U​D |

## ZakelijkRechtHeeftAlsGerechtigde

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zakelijkrechtheeftalsgerechtigde)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |

## ZaakKenmerk

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakkenmerk)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| kenmerk | Identificeert uniek de zaak in een andere administratie. | string | ja | C​R​U​D |
| bron | De aanduiding van de administratie waar het kenmerk op slaat. | string | ja | C​R​U​D |

## Zaak

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaak)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url | URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| identificatie | De unieke identificatie van de ZAAK binnen de organisatie die verantwoordelijk is voor de behandeling van de ZAAK. | string | nee | C​R​U​D |
| bronorganisatie | Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die de zaak heeft gecreeerd. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef | string | ja | C​R​U​D |
| omschrijving | Een korte omschrijving van de zaak. | string | nee | C​R​U​D |
| toelichting | Een toelichting op de zaak. | string | nee | C​R​U​D |
| zaaktype | URL naar het zaaktype in de CATALOGUS waar deze voorkomt | string | ja | C​R​U​D |
| registratiedatum | De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd. Indien deze niet opgegeven wordt, wordt de datum van vandaag gebruikt. | string | nee | C​R​U​D |
| verantwoordelijkeOrganisatie | Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die eindverantwoordelijk is voor de behandeling van de zaak. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef | string | ja | C​R​U​D |
| startdatum | De datum waarop met de uitvoering van de zaak is gestart | string | ja | C​R​U​D |
| einddatum | De datum waarop de uitvoering van de zaak afgerond is. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| einddatumGepland | De datum waarop volgens de planning verwacht wordt dat de zaak afgerond wordt. | string | nee | C​R​U​D |
| uiterlijkeEinddatumAfdoening | De laatste datum waarop volgens wet- en regelgeving de zaak afgerond dient te zijn. | string | nee | C​R​U​D |
| publicatiedatum | Datum waarop (het starten van) de zaak gepubliceerd is of wordt. | string | nee | C​R​U​D |
| communicatiekanaal | Het medium waarlangs de aanleiding om een zaak te starten is ontvangen. URL naar een communicatiekanaal in de VNG-Referentielijst van communicatiekanalen. | string | nee | C​R​U​D |
| productenOfDiensten | De producten en/of diensten die door de zaak worden voortgebracht. Dit zijn URLs naar de resources zoals die door de producten- en dienstencatalogus-API wordt ontsloten. De producten/diensten moeten bij het zaaktype vermeld zijn. | array | nee | C​R​U​D |
| vertrouwelijkheidaanduiding | Aanduiding van de mate waarin het zaakdossier van de ZAAK voor de openbaarheid bestemd is. Optioneel - indien geen waarde gekozen wordt, dan wordt de waarde van het ZAAKTYPE overgenomen. Dit betekent dat de API _altijd_ een waarde teruggeeft. | string | nee | C​R​U​D |
| betalingsindicatie | Indicatie of de, met behandeling van de zaak gemoeide, kosten betaald zijn door de desbetreffende betrokkene.

Uitleg bij mogelijke waarden:

* `nvt` - Er is geen sprake van te betalen, met de zaak gemoeide, kosten.
* `nog_niet` - De met de zaak gemoeide kosten zijn (nog) niet betaald.
* `gedeeltelijk` - De met de zaak gemoeide kosten zijn gedeeltelijk betaald.
* `geheel` - De met de zaak gemoeide kosten zijn geheel betaald. | string | nee | C​R​U​D |
| betalingsindicatieWeergave |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| laatsteBetaaldatum | De datum waarop de meest recente betaling is verwerkt van kosten die gemoeid zijn met behandeling van de zaak. | string | nee | C​R​U​D |
| selectielijstklasse | URL-referentie naar de categorie in de gehanteerde &#39;Selectielijst Archiefbescheiden&#39; die, gezien het zaaktype en het resultaattype van de zaak, bepalend is voor het archiefregime van de zaak. | string | nee | C​R​U​D |
| hoofdzaak | De verwijzing naar de ZAAK, waarom verzocht is door de initiator daarvan, die behandeld wordt in twee of meer separate ZAAKen waarvan de onderhavige ZAAK er één is. | string | nee | C​R​U​D |
| deelzaken |  | array | nee | ~~C~~​R​~~U~~​~~D~~ |
| relevanteAndereZaken | Een lijst van objecten met ieder twee elementen:
* `zaak` - een url naar een andere `Zaak`
* `aardRelatie` - beschrijving van de relatie tussen de twee `Zaak`en, waarbij de onderstaande waardes toegestaan zijn.

Uitleg bij mogelijke waarden:

* `vervolg` - De andere zaak gaf aanleiding tot het starten van de onderhanden zaak.
* `onderwerp` - De andere zaak is relevant voor cq. is onderwerp van de onderhanden zaak.
* `bijdrage` - Aan het bereiken van de uitkomst van de andere zaak levert de onderhanden zaak een bijdrage. | array | nee | C​R​U​D |
| status | Indien geen status bekend is, dan is de waarde &#39;null&#39; | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| kenmerken | Lijst van kenmerken. Merk op dat refereren naar gerelateerde objecten beter kan via `ZaakObject`. | array | nee | C​R​U​D |
| archiefnominatie | Aanduiding of het zaakdossier blijvend bewaard of na een bepaalde termijn vernietigd moet worden. | string | nee | C​R​U​D |
| archiefstatus | Aanduiding of het zaakdossier blijvend bewaard of na een bepaalde termijn vernietigd moet worden. | string | nee | C​R​U​D |
| archiefactiedatum | De datum waarop het gearchiveerde zaakdossier vernietigd moet worden dan wel overgebracht moet worden naar een archiefbewaarplaats. Wordt automatisch berekend bij het aanmaken of wijzigen van een RESULTAAT aan deze ZAAK indien nog leeg. | string | nee | C​R​U​D |
| resultaat | Indien geen resultaat bekend is, dan is de waarde &#39;null&#39; | string | nee | ~~C~~​R​~~U~~​~~D~~ |

## AuditTrail

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/audittrail)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| uuid | Unieke identificatie van de audit regel. | string | nee | C​R​U​D |
| bron | De naam van het component waar de wijziging in is gedaan.

Uitleg bij mogelijke waarden:

* `ac` - Autorisatiecomponent
* `nrc` - Notificatierouteringcomponent
* `zrc` - Zaakregistratiecomponent
* `ztc` - Zaaktypecatalogus
* `drc` - Documentregistratiecomponent
* `brc` - Besluitregistratiecomponent | string | ja | C​R​U​D |
| applicatieId | Unieke identificatie van de applicatie, binnen de organisatie. | string | nee | C​R​U​D |
| applicatieWeergave | Vriendelijke naam van de applicatie. | string | nee | C​R​U​D |
| gebruikersId | Unieke identificatie van de gebruiker die binnen de organisatie herleid kan worden naar een persoon. | string | nee | C​R​U​D |
| gebruikersWeergave | Vriendelijke naam van de gebruiker. | string | nee | C​R​U​D |
| actie | De uitgevoerde handeling.

De bekende waardes voor dit veld zijn hieronder aangegeven,                         maar andere waardes zijn ook toegestaan

Uitleg bij mogelijke waarden:

* `create` - Object aangemaakt
* `list` - Lijst van objecten opgehaald
* `retrieve` - Object opgehaald
* `destroy` - Object verwijderd
* `update` - Object bijgewerkt
* `partial_update` - Object deels bijgewerkt | string | ja | C​R​U​D |
| actieWeergave | Vriendelijke naam van de actie. | string | nee | C​R​U​D |
| resultaat | HTTP status code van de API response van de uitgevoerde handeling. | integer | ja | C​R​U​D |
| hoofdObject | De URL naar het hoofdobject van een component. | string | ja | C​R​U​D |
| resource | Het type resource waarop de actie gebeurde. | string | ja | C​R​U​D |
| resourceUrl | De URL naar het object. | string | ja | C​R​U​D |
| toelichting | Toelichting waarom de handeling is uitgevoerd. | string | nee | C​R​U​D |
| resourceWeergave | Vriendelijke identificatie van het object. | string | ja | C​R​U​D |
| aanmaakdatum | De datum waarop de handeling is gedaan. | string | nee | ~~C~~​R​~~U~~​~~D~~ |

## ZaakBesluit

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakbesluit)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| besluit | URL-referentie naar het informatieobject in het BRC, waar ook de relatieinformatie opgevraagd kan worden. | string | ja | C​R​U​D |

## ZaakEigenschap

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakeigenschap)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| eigenschap | URL naar de eigenschap in het ZTC | string | ja | C​R​U​D |
| naam | De naam van de EIGENSCHAP (overgenomen uit ZTC). | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| waarde |  | string | ja | C​R​U​D |


* Create, Read, Update, Delete

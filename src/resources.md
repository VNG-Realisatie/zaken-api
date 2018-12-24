# Resources

Dit document beschrijft de (RGBZ-)objecttypen die als resources ontsloten
worden met de beschikbare attributen.


## KlantContact

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/klantcontact)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| identificatie | De unieke aanduiding van een KLANTCONTACT | string | nee | C​R​U​D |
| datumtijd | De datum en het tijdstip waarop het KLANTCONTACT begint | string | ja | C​R​U​D |
| kanaal | Het communicatiekanaal waarlangs het KLANTCONTACT gevoerd wordt | string | nee | C​R​U​D |

## Rol

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/rol)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| betrokkene | Een betrokkene gerelateerd aan een zaak | string | ja | C​R​U​D |
| betrokkeneType | Soort betrokkene | string | ja | C​R​U​D |
| rolomschrijving | Algemeen gehanteerde benaming van de aard van de ROL | string | ja | C​R​U​D |
| roltoelichting |  | string | ja | C​R​U​D |

## Status

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/status)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| statusType |  | string | ja | C​R​U​D |
| datumStatusGezet | De datum waarop de ZAAK de status heeft verkregen. | string | ja | C​R​U​D |
| statustoelichting | Een, voor de initiator van de zaak relevante, toelichting op de status van een zaak. | string | nee | C​R​U​D |

## ZaakObject

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakobject)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| object | URL naar de resource die het OBJECT beschrijft. | string | ja | C​R​U​D |
| relatieomschrijving | Omschrijving van de betrekking tussen de ZAAK en het OBJECT. | string | nee | C​R​U​D |
| type | Beschrijft het type object gerelateerd aan de zaak | string | ja | C​R​U​D |

## ZaakProductOfDienst

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakproductofdienst)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| productOfDienst | Het product of de dienst die door de zaak wordt voortgebracht. | string | ja | C​R​U​D |

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
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| identificatie | De unieke identificatie van de ZAAK binnen de organisatie die verantwoordelijk is voor de behandeling van de ZAAK. | string | nee | C​R​U​D |
| bronorganisatie | Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die de zaak heeft gecreeerd. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef | string | ja | C​R​U​D |
| omschrijving | Een korte omschrijving van de zaak. | string | nee | C​R​U​D |
| zaaktype | URL naar het zaaktype in de CATALOGUS waar deze voorkomt | string | ja | C​R​U​D |
| registratiedatum | De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd. Indien deze niet opgegeven wordt, wordt de datum van vandaag gebruikt. | string | nee | C​R​U​D |
| verantwoordelijkeOrganisatie | Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die eindverantwoordelijk is voor de behandeling van de zaak. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef | string | ja | C​R​U​D |
| startdatum | De datum waarop met de uitvoering van de zaak is gestart | string | ja | C​R​U​D |
| einddatum | De datum waarop de uitvoering van de zaak afgerond is. | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| einddatumGepland | De datum waarop volgens de planning verwacht wordt dat de zaak afgerond wordt. | string | nee | C​R​U​D |
| uiterlijkeEinddatumAfdoening | De laatste datum waarop volgens wet- en regelgeving de zaak afgerond dient te zijn. | string | nee | C​R​U​D |
| publicatiedatum | Datum waarop (het starten van) de zaak gepubliceerd is of wordt. | string | nee | C​R​U​D |
| productenEnDiensten | De producten en/of diensten die door de zaak worden voortgebracht. De producten/diensten moeten bij het zaaktype vermeld zijn. | array | nee | C​R​U​D |
| toelichting | Een toelichting op de zaak. | string | nee | C​R​U​D |
| status | Indien geen status bekend is, dan is de waarde &#39;null&#39; | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| kenmerken | Lijst van kenmerken | array | nee | C​R​U​D |

## ZaakInformatieObject

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakinformatieobject)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| informatieobject | URL-referentie naar het informatieobject in het DRC, waar ook de relatieinformatie opgevraagd kan worden. | string | ja | C​R​U​D |

## ZaakEigenschap

Objecttype op [GEMMA Online](https://www.gemmaonline.nl/index.php/Rgbz_1.0/doc/objecttype/zaakeigenschap)

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |
| url |  | string | nee | ~~C~~​R​~~U~~​~~D~~ |
| zaak |  | string | ja | C​R​U​D |
| eigenschap | URL naar de eigenschap in het ZTC | string | ja | C​R​U​D |
| waarde |  | string | ja | C​R​U​D |


* Create, Read, Update, Delete

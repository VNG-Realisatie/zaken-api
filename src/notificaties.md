## Notificaties
## Berichtkenmerken voor Zaken API

Kanalen worden typisch per component gedefinieerd. Producers versturen berichten op bepaalde kanalen,
consumers ontvangen deze. Consumers abonneren zich via een notificatiecomponent (zoals <a href="https://notificaties-api.vng.cloud/api/v1/schema/" rel="nofollow">https://notificaties-api.vng.cloud/api/v1/schema/</a>) op berichten.

Hieronder staan de kanalen beschreven die door deze component gebruikt worden, met de kenmerken bij elk bericht.

De architectuur van de notificaties staat beschreven op <a href="https://github.com/VNG-Realisatie/notificaties-api" rel="nofollow">https://github.com/VNG-Realisatie/notificaties-api</a>.


### zaken

**Kanaal**
`zaken`

**Main resource**

`zaak`



**Kenmerken**

* `bronorganisatie`: Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie die de zaak heeft gecreeerd. Dit moet een geldig RSIN zijn van 9 nummers en voldoen aan <a href="https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef" rel="nofollow">https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef</a>
* `zaaktype`: URL-referentie naar het ZAAKTYPE (in de Catalogi API) in de CATALOGUS waar deze voorkomt
* `vertrouwelijkheidaanduiding`: Aanduiding van de mate waarin het zaakdossier van de ZAAK voor de openbaarheid bestemd is.

**Resources en acties**


* <code>zaak</code>: create, update, destroy

* <code>status</code>: create

* <code>zaakobject</code>: create

* <code>zaakinformatieobject</code>: create

* <code>zaakeigenschap</code>: create, update, destroy

* <code>klantcontact</code>: create

* <code>rol</code>: create, destroy

* <code>resultaat</code>: create, update, destroy

* <code>zaakbesluit</code>: create

* <code>zaakcontactmoment</code>: create

* <code>zaakverzoek</code>: create



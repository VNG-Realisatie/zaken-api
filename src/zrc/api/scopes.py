from zds_schema.scopes import Scope

SCOPE_ZAKEN_CREATE = Scope(
    'zds.scopes.zaken.aanmaken',
    description="""
**Laat toe om**:

* een zaak aan te maken
* de eerste status bij een zaak te zetten
* zaakobjecten aan te maken
* rollen aan te maken
"""
)

SCOPE_STATUSSEN_TOEVOEGEN = Scope(
    'zds.scopes.statussen.toevoegen',
    description="""
**Laat toe om**:

* Statussen toe te voegen voor een zaak
"""
)

SCOPE_ZAKEN_ALLES_LEZEN = Scope(
    'zds.scopes.zaken.lezen',
    description="""
**Laat toe om**:

* zaken op te lijsten
* zaken te doorzoeken
* zaakdetails op te vragen
* statussen te lezen
* statusdetails op te vragen
* zaakobjecten te lezen
* zaakobjectdetails op te vragen
"""
)

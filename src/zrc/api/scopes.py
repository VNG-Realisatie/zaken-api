"""
Defines the scopes used in the ZRC component.

The Exxellence authorisation model is taken into consideration as well, see
https://wiki.exxellence.nl/display/KPORT/2.+Zaaktype+autorisaties
"""

from vng_api_common.scopes import Scope

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

SCOPE_ZAKEN_BIJWERKEN = Scope(
    'zds.scopes.zaken.bijwerken',
    description="""
**Laat toe om**:

* attributen van een zaak te wijzingen
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


SCOPE_ZAKEN_ALLES_VERWIJDEREN = Scope(
    'zds.scopes.zaken.verwijderen',
    description="""
**Laat toe om**:

* zaken te verwijderen
"""
)


SCOPE_ZAKEN_GEFORCEERD_BIJWERKEN = Scope(
    'zds.scopes.zaken.geforceerd-bijwerken',
    description="""
**Allows**:

* change attributes of all cases including closed ones    
"""
)

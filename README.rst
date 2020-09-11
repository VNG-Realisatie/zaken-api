========================
Zaakregistratiecomponent
========================

:Version: 1.0.1
:Source: https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent
:Keywords: zaken, zaakgericht werken, GEMMA, RGBZ, ZRC
:PythonVersion: 3.6

|build-status| |black|

Referentieimplementatie van de zaakregistratiecomponent (ZRC).

Inleiding
=========

Binnen het Nederlandse gemeentelandschap wordt zaakgericht werken nagestreefd.
Om dit mogelijk te maken is er gegevensuitwisseling nodig. De kerngegevens van
zaken moeten ergens geregistreerd worden en opvraagbaar zijn.

Deze referentieimplementatie toont aan dat de API specificatie voor de
zaakregistratiecomponent (hierna ZRC) implementeerbaar is, en vormt een
voorbeeld voor andere implementaties indien ergens twijfel bestaat.

Deze component heeft ook een `testomgeving`_ waar leveranciers tegenaan kunnen
testen.


Documentatie
============

Zie ``INSTALL.rst`` voor installatieinstructies, beschikbare instellingen en
commando's.

Indien je actief gaat ontwikkelen aan deze component raden we aan om niet van
Docker gebruik te maken. Indien je deze component als black-box wil gebruiken,
raden we aan om net wel van Docker gebruik te maken.

Referenties
===========

* `Issues <https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent/issues>`_
* `Code <https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent>`_


.. |build-status| image:: https://requires.io/github/VNG-Realisatie/gemma-zaakregistratiecomponent/requirements.svg?branch=master
    :alt: Build status
    :target: https://requires.io/github/VNG-Realisatie/gemma-zaakregistratiecomponent/requirements.svg?branch=master

.. |requirements| image:: https://requires.io/github/VNG-Realisatie/gemma-zaakregistratiecomponent/requirements.svg?branch=master
     :target: https://requires.io/github/VNG-Realisatie/gemma-zaakregistratiecomponent/requirements/?branch=master
     :alt: Requirements status

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. _testomgeving: https://ref.tst.vng.cloud/zrc/

Licentie
========

Copyright © VNG Realisatie 2018

Licensed under the EUPL_

.. _EUPL: LICENCE.md

~~~~~~~~~~~
What's new?
~~~~~~~~~~~

v1.3.0 -- Pacy Portrayal (Jul 15, 2024)
=======================================

New Features
------------

- Fast reload of precalculated state diagram isolines
- New refrigerant CO2 (R744)

Improvements
------------

- Improved state diagrams
- Better and more robust handling of errors and missing data during state
  diagram creation
- Extended usage example

Fixes
-----

- Total and specific investment cost calculation was missing the
  multiplication factor. Previous results where too low by a factor of 6.32
- Heat sink feed flow temperature was limited below the refrigerants
  critical temperature. This makes no sense for transcritical heat pumps and
  was therefore changed for those heat pump setups. Hence, this update is
  necessary for usage of transcritical heat pumps through the dashboard.
  The models themselves were not limited and are therefore not affected by
  this flaw.
- Fix some topology schemas that where missing labels

Contributors
------------

- `@jfreissmann <https://github.com/jfreissmann>`__
- `@bilwint <https://github.com/bilwint>`__
- `@fwitte <https://github.com/fwitte>`__


v1.2.0 -- Cool Cascading (Jun 28, 2024)
=======================================

New Features
-------------

- Existing stock of heat pump models was widely extended by two-cycle cascade
  heat pump model versions.

Tests
-----

- Basic framework for automated tests of models was created using ``pytest``.

Contributors
------------

- `@bilwint <https://github.com/bilwint>`__
- `@jfreissmann <https://github.com/jfreissmann>`__


v1.1.2 -- Stability Regained (Jun 21, 2024)
===========================================

- This version is a patch for v1.1.0 and v1.1.1, as the update of the
  underlying TESPy version introduced some instabilities at high heat sink
  return flow temperatures.

Contributors
------------

- `@bilwint <https://github.com/bilwint>`__


v1.1.1 -- Hotfix for v1.1.0 (Jun 19, 2024)
==========================================

- Hotfix for v1.1.0 TESPy Update. Heat pump model class ``HeatPumpFlash`` was
  left out in upgrading for TESPy v0.7.x and is fixed in this release.

Contributors
------------

- `@jfreissmann <https://github.com/jfreissmann>`__


v1.1.0 -- TESPy Update (Jun 19, 2024)
=====================================

- All heat pump models are updated to work with the latest TESPy version 0.7.5.
- Furthermore, an API is added to easily get the default parameter files of a
  specific heat pump model class.

Contributors
------------

- `@jfreissmann <https://github.com/jfreissmann>`__


v1.0.0 -- Initial Release (Jun 18, 2024)
========================================

- Initial release of the heatpumps package.
- It contains a comprehensive library of heat pump model classes, as well as a
  powerful dashboard to visualize, simulate and analyze them.

Contributors
------------

- `@jfreissmann <https://github.com/jfreissmann>`__
- `@maltefritz <https://github.com/maltefritz>`__
- `@bilwint <https://github.com/bilwint>`__

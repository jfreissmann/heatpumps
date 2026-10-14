~~~~~~~~~
heatpumps
~~~~~~~~~

Welcome to the official online documentation of **heatpumps**. Try it out right
now!

|streamlit_badge|

.. |streamlit_badge| image:: https://static.streamlit.io/badges/streamlit_badge_black_white.svg
   :target: https://heatpumps.streamlit.app/
   :alt: Streamlit App

Key Features
============

- Steady-state simulation of design and partload operation based on `TESPy <https://github.com/oemof/tespy>`__
- Parametrization and result visualisation through a `Streamlit <https://github.com/streamlit/streamlit>`__ dashboard
- Water-water and air-water heat pumps
- Industry standard, as well as topologies still in research and developement, supported
- Sub- and transcritical processes
- Wide variety of refrigerants due to the integration of `CoolProp <https://github.com/CoolProp/CoolProp>`__

.. figure:: /_static/images/landing_page/screenshot_main_window.png
    :align: center
    :alt: Screenshot of a browser window using the heatpumps dashboard
    :figclass: only-light

    Screenshot of a design simulation using the heatpumps dashboard

.. figure:: /_static/images/landing_page/screenshot_main_window_darkmode.png
    :align: center
    :alt: Screenshot of a browser window using the heatpumps dashboard
    :figclass: only-dark

    Screenshot of a design simulation using the heatpumps dashboard

Structure
=========

This documentation is grouped into the chapters below. It first introduces the
tool, followed by its methodology and a galary, before it is concluded by a
chapter on what and how to contribute to heatpumps.

Getting Started
---------------

This section introduces you to heatpumps' usage. It starts with an explanation
of how the installation of the tool works. Right after, you are shown how to
use the streamlit dashboard to simulate different heat pump topologies usind a
variety of refrigerants. If you would like to dive deeper, e.g. if you need
more granular control of the simulation(s) or to integrate it into a wider
workflow, you may want to use the python model classes directly. These heat
pump model classes are therefore introduced in the final section of this
chapter.

Documentation
-------------

The Documentation chapter goes deeper where the Getting Started one stops. It
contains a thorough explanation of the methodology used, a reference of all
available model setups with their topologies and default parameters, as well as
the full model API. Futhermore, a change log documents the developement process
and the Bibliography holds all references mentioned within the whole online
docs.

Galary
------

Example applications as well as scientific publications using heatpumps are
collected in the Galary chapter.

Development
-----------

The Development chapter contains information on what and how you can contribute
to the developement of heatpumps. This can be as easy as reporting a bug you
stumbled upon while using heatpumps or requesting a feature you feel is missing
currently.

Citing heatpumps
================

|doi_badge|

.. |doi_badge| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.23341865.svg
   :target: https://doi.org/10.5281/zenodo.23341865
   :alt: DOI

If you use heatpumps in your work, we kindly ask you to cite it. The DOI below 
always resolves to the latest version and  individual releases can be found on
`Zenodo <https://doi.org/10.5281/zenodo.23341865>`__. The citation metadata is
also available in the
`CITATION.cff <https://github.com/jfreissmann/heatpumps/blob/main/CITATION.cff>`__
file.

.. code-block:: bibtex

    @misc{heatpumps,
      author    = {Freißmann, Jonas and Fritz, Malte and Tuschy, Ilja and Thomas, Bilwin and Witte, Francesco and Schneider, Hannes},
      title     = {heatpumps: A heat pump simulation model library and dashboard},
      year      = {2026},
      publisher = {Zenodo},
      doi       = {10.5281/zenodo.23341865},
      url       = {https://doi.org/10.5281/zenodo.23341865}
    }

License
=======

.. dropdown:: Full License text
    :animate: fade-in-slide-down

    .. include:: ../LICENSE

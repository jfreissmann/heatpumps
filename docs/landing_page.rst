~~~~~~~~~
heatpumps
~~~~~~~~~

Welcome to the official online documentation of **heatpumps**. Try it out right
now!

.. image:: https://static.streamlit.io/badges/streamlit_badge_black_white.svg
   :target: https://heatpumps.streamlit.app/
   :alt: Streamlit App

Key Features
============

- Steady-state simulation of design and partload operation based on `TESPy <https://github.com/oemof/tespy>`__
- Parametrization and result visualisation through a `Streamlit <https://github.com/streamlit/streamlit>`__ dashboard
- Industry standard, as well as topologies still in research and developement, supported
- Sub- and transcritical processes
- Wide variety of refrigerants due to the integration of `CoolProp <https://github.com/CoolProp/CoolProp>`__

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
contains a thorough explanation of the methodology used, as well as the full
model API. Futhermore, a change log documents the developement process and the
Bibliography holds all references mentioned within the whole online docs.

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

License
=======

.. dropdown:: Full License text
    :animate: fade-in-slide-down

    .. include:: ../LICENSE

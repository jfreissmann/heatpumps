---
title: 'heatpumps: A heat pump simulation model library and dashboard.'
tags:
  - Python
  - TESPy
  - thermodynamics
  - techno-econonmic analysis
  - process analysis
authors:
  - name: Jonas Freißmann
    orcid: 0009-0007-6432-5479
    corresponding: true
    affiliation: 1
  - name: Malte Fritz
    orcid: 0009-0001-5843-0973
    affiliation: 1
  - name: Ilja Tuschy
    orcid: 0000-0003-3442-4170
    affiliation: 1
affiliations:
  - name: Center for Sustainable Energy Systems (ZNES), 24943 Flensburg, Munketoft 3b, Germany
    index: 1
    ror: 01xpfrc74
date: 13 October 2026
bibliography: paper.bib
---


# Summary

Heat pumps are a key technology for decarbonizing the heating sector, supplying 
heat from renewable electricity and low-temperature sources at high efficiency. 
Their performance and cost strongly depend on the design of the underlying 
thermodynamic cycle, of which many variants exist. Comparing these variants on 
a consistent basis requires detailed simulation models that are laborious to 
build and are often locked away in proprietary software.

`heatpumps` is an open-source Python package that makes such models readily 
available. It provides a broad collection of ready-to-run heat pump cycle 
topologies that can be simulated in both design and part-load operation and 
evaluated with respect to their efficiency, exergy destruction and investment 
cost on a transparent and comparable basis. The models build on the 
thermodynamic simulation framework TESPy [@Witte2020] and the fluid property 
library CoolProp [@Bell2014], giving access to a wide range of working fluids. 
All functionality is available through a documented model class API and 
through an interactive web dashboard, addressing users in research, education, 
and industry alike.


# Statement of need

Many studies in the heating sector emphasize the importance of large 
electrically driven mechanical compression heat pumps for future energy 
systems [@Paardekooper2018], [@Arpagaus2018], [@Jesper2021]. However, meta 
analyses indentified gaps in research of the integration and detailed modeling 
of large-scale heat pumps [@Sporleder2022]. Furthermore, a considerable share 
of studies are limited to simplified Carnot/Lorenz-COP or regression models 
[@Pieper2020], [@Jesper2021], therefore losing thermodynamic detail, such as 
cycle topology or component behavior. Studies employing component-based 
thermodynamic modeling often limit their scope to only one or a few cycle 
designs [@Vannoni2023].

`heatpumps` contributes to closing this research gap by providing a wide 
collection of simulation models and analysis features, based on the open-source 
simulation toolkit TESPy [@Witte2020]. It allows for the steady-state design 
and part-load simulation of air-to-water and water-to-water heat pumps via a 
model class API or a Streamlit web-dashboard. Furthermore, `heatpumps` 
provides the largest selection of cycle topologies available to date, 
including sub- and transcritical processes, which can be analyzed with the 
help of state diagrams generated with fluprodia [@FluProDia2025]. TESPy's 
integration of CoolProp [@Bell2014] as a fluid backend makes a wide variety of 
refrigerants available to users. Finally, techno-economic and exergy analyses 
are provided via a component-based cost estimation approach [@Kosmadakis2020], 
[@Bejan1996] and the integration of ExerPy [@ExerPy] respectively.

In conclusion, `heatpumps` can broaden the scope of heat pump research while 
not making compromises in modeling detail. It can support decision-making of 
planners as well as district heating system operators and engineers of 
industrial processes. For university education, the provided dashboard can 
improve accesibility of detailed thermodynamic modeling and strenghten 
learning with its broad analysis toolbox.


# State of the field

Open-source software for modeling heat pumps exists at several levels of 
abstraction, none of which supports a ready-to-use design-oriented comparison 
of a broad range of cycle topologies.

At the *system level*, energy system frameworks represent heat pumps in a 
deliberately reduced manner. `oemof.thermal` [@OemofThermal] derives the COP 
from the Carnot and a constant second-law efficiency, while data-driven 
libraries such as `hplib` [@HPLib] fit regression models to certification 
measurements of market-available units [@Jesper2021]. Such models are 
computationally cheap and well suited to time series simulation and dispatch 
optimization, but they are agnostic to the thermodynamic cycle itself and can 
therefore neither represent nor discriminate between process topologies.

At the *component level*, dedicated vapor compression libraries such as `VCLib` 
[@Vering2022], [@VCLibPy] and `ACHP` [@ACHP] resolve individual compressors and 
heat exchangers in considerable geometric and empirical detail. Their strength 
lies in accurately reproducing a specific machine, and they are correspondingly 
restricted to a small number of flowsheet configurations, predominantly 
single-stage cycles of residential scale, and provide no economic evaluation.

Between these levels, general-purpose process simulators supply the components 
from which arbitrary thermal cycles can be assembled. TESPy [@Witte2020], on 
which `heatpumps` is built, and the flowsheeting environment DWSIM [@DWSIM] 
belong to this category. So do the Modelica libraries AixLib [@Mueller2016], 
Buildings [@Wetter2014] and ThermoCycle [@Quoilin2014], whose emphasis lies on 
dynamic simulation and control design within building and district energy 
systems. These tools are general and powerful, but every heat pump topology has 
to be constructed, parametrized and numerically stabilized by the user. This 
effort scales with the number of setups to be compared and constitutes a 
considerable barrier to non-specialist use. The same applies to the proprietary 
environments frequently employed in heat pump design studies, which 
additionally limit reproducibility [@Wallerand2018].

`heatpumps` occupies the gap between these levels by adding a domain-specific 
layer on top of a general-purpose engine. Each topology is implemented as a 
model class encapsulating the component and connection network, dynamically 
generated starting values for numerically unstable parameters, consistency 
checks against strict thermodynamic limits and post-processing. Three 
properties follow from this architecture. First, the breadth of the model 
collection---comprising 72 ready-to-run configurations of simple, intercooler, 
economizer (open or closed, with serial or parallel compression) and flash 
tank base cycles, each available as a single-cycle or cascaded and as a sub- 
or transcritical variant---is to the authors' knowledge unmatched by any other 
open-source package. It thereby addresses the call for a systematic 
exploration of the available cycle configurations [@Adamson2022]. Second, 
thermodynamic simulation is coupled to a component-based cost estimation 
[@Kosmadakis2020], [@Bejan1996] and an exergy analysis [@ExerPy], so that 
cycle efficiency and the cost required to achieve it can be weighed against 
each other within a single tool on a comparable basis. Third, the deliberately 
superstructure-free formulation keeps every topology explicit and inspectable, 
and makes the library extensible by contributing further model classes instead 
of re-encoding a monolithic optimization problem.


# Software design

`heatpumps` follows a layered, object-oriented design that separates the user 
interface, the parametrization and the thermodynamic models 
(\autoref{fig:architecture}). The Streamlit dashboard and the Python API both 
pass a parameter set, derived from one of the bundled JSON presets, to the same 
model classes. As the dashboard adds no modeling capability of its own, both 
routes yield identical results, and the same models drive interactive 
exploration as well as large scripted batch studies without duplication.

At the core, the parent class `HeatPumpBase` implements everything common to 
all heat pumps, i.e., the design and part-load simulation workflow, the 
consistency checks and the analysis methods. Each topology is realized as a 
child class that only implements the aspects specific to it, namely its 
components, their connections, and its starting values and design 
specifications. New topologies can therefore be added by contributing a single 
child class without touching the shared workflow or the interface. The class 
names encode the topology, so that for example `HeatPumpEconIHX` denotes an 
economizer cycle with an internal heat exchanger and `HeatPumpEconIHXTrans` 
its transcritical counterpart.

A recurring challenge in the equation-based simulation of heat pump cycles is 
the numerical stability of the solver, which strongly depends on the quality of 
the starting values. `heatpumps` therefore solves each design in two stages: an 
initial simulation with robust starting values, generated dynamically from the 
user's specifications. This first simulation then initializes the final design 
simulation in which the actual target parameters are imposed. A subsequent 
consistency check against strict thermodynamic limits flags implausible 
solutions. The final simulation results can then be explored via a host of 
analysis methods or serve as the starting point of part-load investigation.

Rather than reimplementing established functionality, `heatpumps` builds on 
the surrounding open-source ecosystem (\autoref{fig:architecture}). It is 
distributed via PyPI under the MIT license, tested through an automated test 
suite and documented on Read the Docs.

![Software architecture of `heatpumps`. Dashboard and Python API pass a
parameter set to the same model classes. The parent class `HeatPumpBase`
implements the shared simulation workflow, whose topology-specific steps
(dashed box) are implemented by the child classes. The analysis methods
evaluate the solved model. Grey boxes indicate the open-source packages each
layer builds on.\label{fig:architecture}](./docs/_static/images/paper/heatpumps_scheme.pdf){ width=100% }


# Research impact statement

Although `heatpumps` is a young project, it is already being applied in 
research. Within the authors' research group it has supported several district 
heating research projects and provides the modeling basis for a comparative 
design study of heat pump topologies for district heating systems 
[@Freissmann2026]. Its dashboard was presented at the 2nd Conference of North 
German Heat Research [@Fritz2025], and the publicly hosted instance on 
Streamlit Community Cloud has recorded more than 1,000 unique visitors as of 
October 2026, indicating interest beyond the immediate developer circle.

Since its initial release on PyPI in May 2026, heatpumps has been downloaded 
over 2,000 times (according to pepy.tech, last checked October 2026). While 
adoption is still at an early stage, ongoing development is deliberately aimed 
at broadening the tool's reach: the latest release introduced 
English-language support to the previously German-only dashboard and expanded 
the documentation, lowering the barrier to entry for an international 
audience. Together with the growing research interest in large-scale heat pumps 
for the decarbonization of the heating sector, this positions heatpumps to make 
detailed, reproducible heat pump design studies more widely accessible.


# AI usage disclosure

The majority of `heatpumps` was developed without generative AI tools. Only 
recently (ca. `v1.4.0` onwards) have coding agents (Claude Code, Opus 5 
models) been slowly integrated into the developement process. The first draft 
of this manuscript was written solely by the authors and a second iteration 
was cleaned up with the help of AI language tools (as above; also: DeepL). All 
changes were reviewed and verified by the authors, who take full 
responsibility for the final manuscript.


# Acknowledgements

We acknowledge contributions from Bilwin Thomas and Francesco Witte. 
Furthermore, we want to thank Francesco Witte for the creation of TESPy and 
fluprodia as well as the discussions, feedback, and support he provided, 
without which `heatpumps` would not have been possible.


# References


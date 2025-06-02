[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://owp-inno-nord.streamlit.app/)

# heatpumps

Steady-state simulation of design and partload operation of a wide collection of heat pump topologies.

## Key Features

  - Steady-state simulation of design and partload operation based on [TESPy](https://github.com/oemof/tespy)
  - Parametrization and result visualisation through a [Streamlit](https://github.com/streamlit/streamlit) dashboard
  - Industry standard, as well as topologies still in research and developement, supported
  - Sub- and transcritical processes
  - Wide variety of refrigerants due to the integration of [CoolProp](https://github.com/CoolProp/CoolProp)

## Installation

For now, only direct download from the [GitHub Repository](https://github.com/jfreissmann/heatpumps) is supported, so just clone it locally or download a ZIP file of the code.  If you are using [Miniforge](https://github.com/conda-forge/miniforge), you can create and activate a clean environment like this:

```
conda create -n my_new_env python=3.11
```

```
conda activate my_new_env
```

If you want to build the package locally and install it, you should use these commands from the root directory of the repository:

```
python setup.py sdist bdist_wheel
```

```
python -m pip install .
```

If you want to use an editable version of the package, e.g. if you want to contribute to the project and test your own changes, skip the commands above and use this one:

```
python -m pip install -e "path/to/the/heatpumps/dir/"
```

## Run the dashboard

The heatpumps package comes with a command to run the dashboard directly from your terminal. Running the dashboard is as easy as typing the following command:

```
heatpumps-dashboard
```

## Using the heat pump model classes

To use the heat pump model classes in your own scripts, you can import them as follows:

```python
from heatpumps.models import HeatPumpSimple, HeatPumpEconIHX
from heatpumps.parameters import get_params

# Simple cycle model
params = get_params('HeatPumpSimple')

params['setup']['refrig'] = 'R1234yf'
params['fluids']['wf'] = 'R1234yf'

params['C3']['T'] = 85  # feed flow temperature of heat sink
params['C1']['T'] = 50  # return flow temperature of heat sink

hp = HeatPumpSimple(params=params)

hp.run_model()
hp.generate_state_diagram(diagram_type='logph', savefig=True, open_file=True)

# Serial compression with closed economizer and internal heat exchanger
econ_type = 'closed'
params = get_params('HeatPumpEconIHX', econ_type=econ_type)

params['ihx']['dT_sh'] = 7.5  # superheating by internal heat exchanger

hp = HeatPumpEconIHX(params=params, econ_type=econ_type)

hp.run_model()
hp.perform_exergy_analysis(print_results=True)
```

## License

Copyright (c) Jonas Freißmann and Malte Fritz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

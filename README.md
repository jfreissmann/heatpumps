# heatpumps

Steady-state simulation of design and partload operation of a wide collection of heat pump topologies.

## Key Features

  - Steady-state simulation of design and partload operation based on [TESPy](https://github.com/oemof/tespy)
  - Parametrization and result visualisation through a [Streamlit](https://github.com/streamlit/streamlit) dashboard
  - Industry standard, as well as topologies still in research and developement, supported
  - Sub- and transcritical processes
  - Wide variety of refrigerants due to the integration of [CoolProp](https://github.com/CoolProp/CoolProp)

## Installation

For now, only direct download from the [GitHub Repository](https://github.com/jfreissmann/heatpumps) is supported, so just clone it locally or download a ZIP file of the code. To use the heat pump model classes or visualization dashboard, the necessary dependencies have to be installed from the `requirements.txt` file. In a clean environment from the root directory the installation from this file could look like this:

```
conda create -n my_new_env python=3.11
```

```
conda activate my_new_env
```

```
python -m pip install -r requirements.txt
```

## Run the dashboard

Running the heat pump dashboard is as easy as running the following command from the root directory in your virtual environment with dependencies installed:

```
streamlit run src\heatpumps\hp_dashboard.py
```


## License

Copyright (c) 2023 Jonas Freißmann and Malte Fritz

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

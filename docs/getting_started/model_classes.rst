.. _model_classes_label:

~~~~~~~~~~~~~~~~~~~~~~~
Heat Pump Model Classes
~~~~~~~~~~~~~~~~~~~~~~~

Going beyond the dashboard and using the model API unlocks the full potential
of heatpumps. Here, you have full control over the model, its parametrization,
and how it is simulated. Adjust or extend the underlying TESPy network and use
it in sensitivity analyses as well as optimizations.

General usage
=============

To use the heat pump model classes in your own scripts, you can import them as follows:

.. code-block:: python

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


Get a model from the dashboard
==============================

After a succesful design simulation, heatpumps' dashboard gives you the option
to save your model configuration as a JSON file. The ``from_json`` method
included in the ``parameters`` submodule allows you to initialize a heat pump
model class according to your configuration as shown in the code snippet below.

.. code-block:: python

    from heatpumps.parameters import from_json

    hp = from_json('HeatPumpCascadeEcon_heatpumps.json')

    hp.run_model()
    print(f'{hp.cop = }')

.. tip::

    The dashboard also allows you to export the heat pump model in the JSON
    format used by TESPy. This way you can create a plain TESPy model from it
    as well.

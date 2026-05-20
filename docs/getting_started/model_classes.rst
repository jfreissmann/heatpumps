~~~~~~~~~~~~~~~~~~~~~~~
Heat Pump Model Classes
~~~~~~~~~~~~~~~~~~~~~~~

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

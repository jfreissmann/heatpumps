# Important variables for the heat pump dashboard

# hp_models = {
#     'cascade_2ihx': HeatPumpCascade2IHX.HeatPumpCascade2IHX,
#     'cascade': HeatPumpCascade.HeatPumpCascade,
#     'econ_closed_ihx': HeatPumpEconIHX.HeatPumpEconIHX,
#     'econ_closed': HeatPumpEcon.HeatPumpEcon,
#     'econ_open_ihx': HeatPumpEconIHX.HeatPumpEconIHX,
#     'econ_open': HeatPumpEcon.HeatPumpEcon,
#     'flash': HeatPumpFlash.HeatPumpFlash,
#     'ic': HeatPumpIC.HeatPumpIC,
#     'ihx_econ_closed': HeatPumpIHXEcon.HeatPumpIHXEcon,
#     'ihx_econ_open': HeatPumpIHXEcon.HeatPumpIHXEcon,
#     'ihx': HeatPumpIHX.HeatPumpIHX,
#     'pc_econ_closed_2ihx': HeatPumpPC2IHX.HeatPumpPC2IHX,
#     'pc_econ_closed_ihx': HeatPumpPCIHX.HeatPumpPCIHX,
#     'pc_econ_closed': HeatPumpPC.HeatPumpPC,
#     'pc_econ_open_2ihx': HeatPumpPC2IHX.HeatPumpPC2IHX,
#     'pc_econ_open_ihx': HeatPumpPCIHX.HeatPumpPCIHX,
#     'pc_econ_open': HeatPumpPC.HeatPumpPC,
#     'simple': HeatPumpSimple.HeatPumpSimple
#     }

hp_topologies = {
    'Einfacher Kreis': {
        'simple': {'nr_int_heatex': 0},
        'ihx': {'nr_int_heatex': 1}
        },
    'Zwischenkühlung': {
        'ic': {'nr_int_heatex': 0}
        },
    'Economizer': {
        'econ_closed': {
            'nr_int_heatex': 0, 'econ_type': 'closed', 'comp_var': 'series'
            },
        'econ_closed_ihx': {
            'nr_int_heatex': 1, 'econ_type': 'closed', 'comp_var': 'series'
            },
        'ihx_econ_closed': {
            'nr_int_heatex': 1, 'econ_type': 'closed', 'comp_var': 'series'
            },
        'econ_open': {
            'nr_int_heatex': 0, 'econ_type': 'open', 'comp_var': 'series'
            },
        'econ_open_ihx': {
            'nr_int_heatex': 1, 'econ_type': 'open', 'comp_var': 'series'
            },
        'ihx_econ_open': {
            'nr_int_heatex': 1, 'econ_type': 'open', 'comp_var': 'series'
            },
        'pc_econ_closed': {
            'nr_int_heatex': 0, 'econ_type': 'closed', 'comp_var': 'parallel'
            },
        'pc_econ_closed_ihx': {
            'nr_int_heatex': 1, 'econ_type': 'closed', 'comp_var': 'parallel'
            },
        'pc_econ_closed_2ihx': {
            'nr_int_heatex': 2, 'econ_type': 'closed', 'comp_var': 'parallel'
            },
        'pc_econ_open': {
            'nr_int_heatex': 0, 'econ_type': 'open', 'comp_var': 'parallel'
            },
        'pc_econ_open_ihx': {
            'nr_int_heatex': 1, 'econ_type': 'open', 'comp_var': 'parallel'
            },
        'pc_econ_open_2ihx': {
            'nr_int_heatex': 2, 'econ_type': 'open', 'comp_var': 'parallel'
            }
        },
    'Flashtank': {
        'flash': {'nr_int_heatex': 0}
        },
    'Kaskadierter Kreis': {
        'cascade': {'nr_int_heatex': 0},
        'cascade_2ihx': {'nr_int_heatex': 2}
        }
    }


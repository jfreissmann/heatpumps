import os
import json


base_topologies = (
    'Einfacher Kreis',
    'Zwischenkühlung',
    'Economizer',
    'Flashtank',
    'Kaskadierter Kreis'
)

model_names = [
    'cascade',
    'cascade_2ihx',
    'cascade_2ihx_trans',
    'cascade_econ_closed',
    'cascade_econ_closed_ihx',
    'cascade_econ_closed_ihx_trans',
    'cascade_econ_closed_trans',
    'cascade_econ_open',
    'cascade_econ_open_ihx',
    'cascade_econ_open_ihx_trans',
    'cascade_econ_open_trans',
    'cascade_flash',
    'cascade_flash_trans',
    'cascade_ic',
    'cascade_ic_trans',
    'cascade_ihx_econ_closed',
    'cascade_ihx_econ_closed_trans',
    'cascade_ihx_econ_open',
    'cascade_ihx_econ_open_trans',
    'cascade_ihx_pc_econ_closed',
    'cascade_ihx_pc_econ_closed_ihx',
    'cascade_ihx_pc_econ_closed_ihx_trans',
    'cascade_ihx_pc_econ_closed_trans',
    'cascade_ihx_pc_econ_open',
    'cascade_ihx_pc_econ_open_ihx',
    'cascade_ihx_pc_econ_open_ihx_trans',
    'cascade_ihx_pc_econ_open_trans',
    'cascade_pc_econ_closed',
    'cascade_pc_econ_closed_ihx',
    'cascade_pc_econ_closed_ihx_trans',
    'cascade_pc_econ_closed_trans',
    'cascade_pc_econ_open',
    'cascade_pc_econ_open_ihx',
    'cascade_pc_econ_open_ihx_trans',
    'cascade_pc_econ_open_trans',
    'cascade_trans',
    'econ_closed',
    'econ_closed_ihx',
    'econ_closed_ihx_trans',
    'econ_closed_trans',
    'econ_open',
    'econ_open_ihx',
    'econ_open_ihx_trans',
    'econ_open_trans',
    'flash',
    'flash_trans',
    'ic',
    'ic_trans',
    'ihx',
    'ihx_econ_closed',
    'ihx_econ_closed_trans',
    'ihx_econ_open',
    'ihx_econ_open_trans',
    'ihx_pc_econ_closed',
    'ihx_pc_econ_closed_ihx',
    'ihx_pc_econ_closed_ihx_trans',
    'ihx_pc_econ_closed_trans',
    'ihx_pc_econ_open',
    'ihx_pc_econ_open_ihx',
    'ihx_pc_econ_open_ihx_trans',
    'ihx_pc_econ_open_trans',
    'ihx_trans',
    'pc_econ_closed',
    'pc_econ_closed_ihx',
    'pc_econ_closed_ihx_trans',
    'pc_econ_closed_trans',
    'pc_econ_open',
    'pc_econ_open_ihx',
    'pc_econ_open_ihx_trans',
    'pc_econ_open_trans',
    'simple',
    'simple_trans'
]

hp_models = {}
for model in model_names:
    parampath = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 'models', 'input',
            f'params_hp_{model}.json'
        )
    )
    with open(parampath, 'r', encoding='utf-8') as file:
        hp_models[model] = json.load(file)

# %% Misc
econ_translate = {
    'offen': 'open',
    'geschlossen': 'closed'
}
comp_translate = {
    'Reihenschaltung': 'series',
    'Parallelschaltung': 'parallel'
}

# %% Styling
st_color_hex = '#ff4b4b'

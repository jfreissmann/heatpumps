import json
import os
from importlib import resources

from heatpumps.models import (
    HeatPumpSimple, HeatPumpSimpleTrans,
    HeatPumpIHX, HeatPumpIHXTrans,
    HeatPumpIC, HeatPumpICTrans,
    HeatPumpEcon, HeatPumpEconTrans, HeatPumpEconIHX, HeatPumpEconIHXTrans,
    HeatPumpIHXEcon, HeatPumpIHXEconTrans,
    HeatPumpPC, HeatPumpPCTrans, HeatPumpPCIHX, HeatPumpPCIHXTrans,
    HeatPumpIHXPC, HeatPumpIHXPCTrans, HeatPumpIHXPCIHX, HeatPumpIHXPCIHXTrans,
    HeatPumpFlash, HeatPumpFlashTrans,
    HeatPumpCascade, HeatPumpCascadeTrans,
    HeatPumpCascade2IHX, HeatPumpCascade2IHXTrans,
    HeatPumpCascadeIC, HeatPumpCascadeICTrans,
    HeatPumpCascadeFlash, HeatPumpCascadeFlashTrans,
    HeatPumpCascadeEcon, HeatPumpCascadeEconTrans,
    HeatPumpCascadeEconIHX, HeatPumpCascadeEconIHXTrans,
    HeatPumpCascadeIHXEcon, HeatPumpCascadeIHXEconTrans,
    HeatPumpCascadePC, HeatPumpCascadePCTrans,
    HeatPumpCascadePCIHX, HeatPumpCascadePCIHXTrans,
    HeatPumpCascadeIHXPC, HeatPumpCascadeIHXPCTrans,
    HeatPumpCascadeIHXPCIHX, HeatPumpCascadeIHXPCIHXTrans,
)

# Maps model_key → (class, econ_type or None)
_model_registry = {
    'simple':                           (HeatPumpSimple,            None),
    'simple_trans':                     (HeatPumpSimpleTrans,        None),
    'ihx':                              (HeatPumpIHX,               None),
    'ihx_trans':                        (HeatPumpIHXTrans,           None),
    'ic':                               (HeatPumpIC,                None),
    'ic_trans':                         (HeatPumpICTrans,            None),
    'econ_closed':                      (HeatPumpEcon,              'closed'),
    'econ_closed_trans':                (HeatPumpEconTrans,          'closed'),
    'econ_closed_ihx':                  (HeatPumpEconIHX,           'closed'),
    'econ_closed_ihx_trans':            (HeatPumpEconIHXTrans,       'closed'),
    'econ_open':                        (HeatPumpEcon,              'open'),
    'econ_open_trans':                  (HeatPumpEconTrans,          'open'),
    'econ_open_ihx':                    (HeatPumpEconIHX,           'open'),
    'econ_open_ihx_trans':              (HeatPumpEconIHXTrans,       'open'),
    'ihx_econ_closed':                  (HeatPumpIHXEcon,           'closed'),
    'ihx_econ_closed_trans':            (HeatPumpIHXEconTrans,       'closed'),
    'ihx_econ_open':                    (HeatPumpIHXEcon,           'open'),
    'ihx_econ_open_trans':              (HeatPumpIHXEconTrans,       'open'),
    'pc_econ_closed':                   (HeatPumpPC,                'closed'),
    'pc_econ_closed_trans':             (HeatPumpPCTrans,            'closed'),
    'pc_econ_closed_ihx':               (HeatPumpPCIHX,             'closed'),
    'pc_econ_closed_ihx_trans':         (HeatPumpPCIHXTrans,         'closed'),
    'pc_econ_open':                     (HeatPumpPC,                'open'),
    'pc_econ_open_trans':               (HeatPumpPCTrans,            'open'),
    'pc_econ_open_ihx':                 (HeatPumpPCIHX,             'open'),
    'pc_econ_open_ihx_trans':           (HeatPumpPCIHXTrans,         'open'),
    'ihx_pc_econ_closed':               (HeatPumpIHXPC,             'closed'),
    'ihx_pc_econ_closed_trans':         (HeatPumpIHXPCTrans,         'closed'),
    'ihx_pc_econ_closed_ihx':           (HeatPumpIHXPCIHX,          'closed'),
    'ihx_pc_econ_closed_ihx_trans':     (HeatPumpIHXPCIHXTrans,      'closed'),
    'ihx_pc_econ_open':                 (HeatPumpIHXPC,             'open'),
    'ihx_pc_econ_open_trans':           (HeatPumpIHXPCTrans,         'open'),
    'ihx_pc_econ_open_ihx':             (HeatPumpIHXPCIHX,          'open'),
    'ihx_pc_econ_open_ihx_trans':       (HeatPumpIHXPCIHXTrans,      'open'),
    'flash':                            (HeatPumpFlash,             None),
    'flash_trans':                      (HeatPumpFlashTrans,         None),
    'cascade':                          (HeatPumpCascade,           None),
    'cascade_trans':                    (HeatPumpCascadeTrans,       None),
    'cascade_2ihx':                     (HeatPumpCascade2IHX,       None),
    'cascade_2ihx_trans':               (HeatPumpCascade2IHXTrans,  None),
    'cascade_ic':                       (HeatPumpCascadeIC,         None),
    'cascade_ic_trans':                 (HeatPumpCascadeICTrans,     None),
    'cascade_flash':                    (HeatPumpCascadeFlash,      None),
    'cascade_flash_trans':              (HeatPumpCascadeFlashTrans,  None),
    'cascade_econ_closed':              (HeatPumpCascadeEcon,       'closed'),
    'cascade_econ_closed_trans':        (HeatPumpCascadeEconTrans,   'closed'),
    'cascade_econ_closed_ihx':          (HeatPumpCascadeEconIHX,    'closed'),
    'cascade_econ_closed_ihx_trans':    (HeatPumpCascadeEconIHXTrans,'closed'),
    'cascade_econ_open':                (HeatPumpCascadeEcon,       'open'),
    'cascade_econ_open_trans':          (HeatPumpCascadeEconTrans,   'open'),
    'cascade_econ_open_ihx':            (HeatPumpCascadeEconIHX,    'open'),
    'cascade_econ_open_ihx_trans':      (HeatPumpCascadeEconIHXTrans,'open'),
    'cascade_ihx_econ_closed':          (HeatPumpCascadeIHXEcon,    'closed'),
    'cascade_ihx_econ_closed_trans':    (HeatPumpCascadeIHXEconTrans,'closed'),
    'cascade_ihx_econ_open':            (HeatPumpCascadeIHXEcon,    'open'),
    'cascade_ihx_econ_open_trans':      (HeatPumpCascadeIHXEconTrans,'open'),
    'cascade_pc_econ_closed':           (HeatPumpCascadePC,         'closed'),
    'cascade_pc_econ_closed_trans':     (HeatPumpCascadePCTrans,     'closed'),
    'cascade_pc_econ_closed_ihx':       (HeatPumpCascadePCIHX,      'closed'),
    'cascade_pc_econ_closed_ihx_trans': (HeatPumpCascadePCIHXTrans,  'closed'),
    'cascade_pc_econ_open':             (HeatPumpCascadePC,         'open'),
    'cascade_pc_econ_open_trans':       (HeatPumpCascadePCTrans,     'open'),
    'cascade_pc_econ_open_ihx':         (HeatPumpCascadePCIHX,      'open'),
    'cascade_pc_econ_open_ihx_trans':   (HeatPumpCascadePCIHXTrans,  'open'),
    'cascade_ihx_pc_econ_closed':       (HeatPumpCascadeIHXPC,      'closed'),
    'cascade_ihx_pc_econ_closed_trans': (HeatPumpCascadeIHXPCTrans,  'closed'),
    'cascade_ihx_pc_econ_closed_ihx':   (HeatPumpCascadeIHXPCIHX,   'closed'),
    'cascade_ihx_pc_econ_closed_ihx_trans': (HeatPumpCascadeIHXPCIHXTrans, 'closed'),
    'cascade_ihx_pc_econ_open':         (HeatPumpCascadeIHXPC,      'open'),
    'cascade_ihx_pc_econ_open_trans':   (HeatPumpCascadeIHXPCTrans,  'open'),
    'cascade_ihx_pc_econ_open_ihx':     (HeatPumpCascadeIHXPCIHX,   'open'),
    'cascade_ihx_pc_econ_open_ihx_trans': (HeatPumpCascadeIHXPCIHXTrans, 'open'),
}

__model_names = {
    'HeatPumpSimple': 'simple',
    'HeatPumpSimpleTrans': 'simple_trans',
    'HeatPumpIHX': 'ihx',
    'HeatPumpIHXTrans': 'ihx_trans',
    'HeatPumpIC': 'ic',
    'HeatPumpICTrans': 'ic_trans',
    'HeatPumpEcon_closed': 'econ_closed',
    'HeatPumpEconTrans_closed': 'econ_closed_trans',
    'HeatPumpEconIHX_closed': 'econ_closed_ihx',
    'HeatPumpEconIHXTrans_closed': 'econ_closed_ihx_trans',
    'HeatPumpIHXEcon_closed': 'ihx_econ_closed',
    'HeatPumpIHXEconTrans_closed': 'ihx_econ_closed_trans',
    'HeatPumpEcon_open': 'econ_open',
    'HeatPumpEconTrans_open': 'econ_open_trans',
    'HeatPumpEconIHX_open': 'econ_open_ihx',
    'HeatPumpEconIHXTrans_open': 'econ_open_ihx_trans',
    'HeatPumpIHXEcon_open': 'ihx_econ_open',
    'HeatPumpIHXEconTrans_open': 'ihx_econ_open_trans',
    'HeatPumpPC_closed': 'pc_econ_closed',
    'HeatPumpPCTrans_closed': 'pc_econ_closed_trans',
    'HeatPumpIHXPC_closed': 'ihx_pc_econ_closed',
    'HeatPumpIHXPCTrans_closed': 'ihx_pc_econ_closed_trans',
    'HeatPumpPCIHX_closed': 'pc_econ_closed_ihx',
    'HeatPumpPCIHXTrans_closed': 'pc_econ_closed_ihx_trans',
    'HeatPumpIHXPCIHX_closed': 'ihx_pc_econ_closed_ihx',
    'HeatPumpIHXPCIHXTrans_closed': 'ihx_pc_econ_closed_ihx_trans',
    'HeatPumpPC_open': 'pc_econ_open',
    'HeatPumpPCTrans_open': 'pc_econ_open_trans',
    'HeatPumpIHXPC_open': 'ihx_pc_econ_open',
    'HeatPumpIHXPCTrans_open': 'ihx_pc_econ_open_trans',
    'HeatPumpPCIHX_open': 'pc_econ_open_ihx',
    'HeatPumpPCIHXTrans_open': 'pc_econ_open_ihx_trans',
    'HeatPumpIHXPCIHX_open': 'ihx_pc_econ_open_ihx',
    'HeatPumpIHXPCIHXTrans_open': 'ihx_pc_econ_open_ihx_trans',
    'HeatPumpFlash': 'flash',
    'HeatPumpFlashTrans': 'flash_trans',
    'HeatPumpCascade': 'cascade',
    'HeatPumpCascadeTrans': 'cascade_trans',
    'HeatPumpCascade2IHX': 'cascade_2ihx',
    'HeatPumpCascade2IHXTrans': 'cascade_2ihx_trans',
    'HeatPumpCascadeIC': 'cascade_ic',
    'HeatPumpCascadeICTrans': 'cascade_ic_trans',
    'HeatPumpCascadeEcon_closed': 'cascade_econ_closed',
    'HeatPumpCascadeEconTrans_closed': 'cascade_econ_closed_trans',
    'HeatPumpCascadeIHXEcon_closed': 'cascade_ihx_econ_closed',
    'HeatPumpCascadeIHXEconTrans_closed': 'cascade_ihx_econ_closed_trans',
    'HeatPumpCascadeEconIHX_closed': 'cascade_econ_closed_ihx',
    'HeatPumpCascadeEconIHXTrans_closed': 'cascade_econ_closed_ihx_trans',
    'HeatPumpCascadeEcon_open': 'cascade_econ_open',
    'HeatPumpCascadeEconTrans_open': 'cascade_econ_open_trans',
    'HeatPumpCascadeIHXEcon_open': 'cascade_ihx_econ_open',
    'HeatPumpCascadeIHXEconTrans_open': 'cascade_ihx_econ_open_trans',
    'HeatPumpCascadeEconIHX_open': 'cascade_econ_open_ihx',
    'HeatPumpCascadeEconIHXTrans_open': 'cascade_econ_open_ihx_trans',
    'HeatPumpCascadePC_closed': 'cascade_pc_econ_closed',
    'HeatPumpCascadePCTrans_closed': 'cascade_pc_econ_closed_trans',
    'HeatPumpCascadeIHXPC_closed': 'cascade_ihx_pc_econ_closed',
    'HeatPumpCascadeIHXPCTrans_closed': 'cascade_ihx_pc_econ_closed_trans',
    'HeatPumpCascadePCIHX_closed': 'cascade_pc_econ_closed_ihx',
    'HeatPumpCascadePCIHXTrans_closed': 'cascade_pc_econ_closed_ihx_trans',
    'HeatPumpCascadeIHXPCIHX_closed': 'cascade_ihx_pc_econ_closed_ihx',
    'HeatPumpCascadeIHXPCIHXTrans_closed': 'cascade_ihx_pc_econ_closed_ihx_trans',
    'HeatPumpCascadePC_open': 'cascade_pc_econ_open',
    'HeatPumpCascadePCTrans_open': 'cascade_pc_econ_open_trans',
    'HeatPumpCascadeIHXPC_open': 'cascade_ihx_pc_econ_open',
    'HeatPumpCascadeIHXPCTrans_open': 'cascade_ihx_pc_econ_open_trans',
    'HeatPumpCascadePCIHX_open': 'cascade_pc_econ_open_ihx',
    'HeatPumpCascadePCIHXTrans_open': 'cascade_pc_econ_open_ihx_trans',
    'HeatPumpCascadeIHXPCIHX_open': 'cascade_ihx_pc_econ_open_ihx',
    'HeatPumpCascadeIHXPCIHXTrans_open': 'cascade_ihx_pc_econ_open_ihx_trans',
    'HeatPumpCascadeFlash': 'cascade_flash',
    'HeatPumpCascadeFlashTrans': 'cascade_flash_trans'
}

def get_params(heat_pump_model, econ_type=None):
    """Get params dict for heat pump model class.
    
    Parameters
    ----------
    
    heat_pump_model : str
        Name of heat pump model class (e.g. 'HeatPumpEconIHX')

    econ_type : str or None
        If heat pump model class has an economizer, the econ_type has to be
        set. Either 'closed' or 'open'. Default is `None`.
    """
    if econ_type is not None and econ_type.lower() not in ['closed', 'open']:
        raise ValueError(
            f"Parameter '{econ_type}' is not a valid econ_type. "
            + "Supported values are 'open' and 'closed'."
            )

    if econ_type is not None:
        hpfilename = __model_names[f'{heat_pump_model}_{econ_type.lower()}']
    else:
        hpfilename = __model_names[heat_pump_model]
    parampath = resources.files('heatpumps').joinpath(
        'models', 'input', f'params_hp_{hpfilename}.json'
    )
    with open(parampath, 'r', encoding='utf-8') as file:
        params = json.load(file)

    return params


def from_json(filepath):
    """Instantiate and run a heat pump model from a debug JSON file.

    Parameters
    ----------
    filepath : str or path-like
        Path to a JSON file in the format produced by the dashboard on a
        failed design simulation: ``{"model_key": "<key>", "params": {...}}``.

    Returns
    -------
    HeatPumpBase subclass instance
        The fully constructed (but not yet simulated) heat pump object.

    Example
    -------
    >>> from heatpumps.parameters import from_json
    >>> hp = from_json("HeatPumpSimple_debug.json")
    >>> hp.run_model()
    """
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    model_key = data['model_key']
    params = data['params']

    if model_key not in _model_registry:
        raise ValueError(
            f"Unknown model_key '{model_key}'. "
            f"Valid keys: {sorted(_model_registry)}"
        )

    cls, econ_type = _model_registry[model_key]
    if econ_type is not None:
        return cls(params, econ_type=econ_type)
    return cls(params)

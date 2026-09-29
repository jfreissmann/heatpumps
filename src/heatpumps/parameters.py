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

# Single source of truth: maps model_key → {'cls': class, 'econ_type': str or None}.
# ``get_params`` reverse-looks-up this table (class name + econ_type → key) and
# ``from_json`` looks it up directly.
_model_registry = {
    'simple': {
        'cls': HeatPumpSimple,
        'econ_type': None
    },
    'simple_trans': {
        'cls': HeatPumpSimpleTrans,
        'econ_type': None
    },
    'ihx': {
        'cls': HeatPumpIHX,
        'econ_type': None
    },
    'ihx_trans': {
        'cls': HeatPumpIHXTrans,
        'econ_type': None
    },
    'ic': {
        'cls': HeatPumpIC,
        'econ_type': None
    },
    'ic_trans': {
        'cls': HeatPumpICTrans,
        'econ_type': None
    },
    'econ_closed': {
        'cls': HeatPumpEcon,
        'econ_type': 'closed'
    },
    'econ_closed_trans': {
        'cls': HeatPumpEconTrans,
        'econ_type': 'closed'
    },
    'econ_closed_ihx': {
        'cls': HeatPumpEconIHX,
        'econ_type': 'closed'
    },
    'econ_closed_ihx_trans': {
        'cls': HeatPumpEconIHXTrans,
        'econ_type': 'closed'
    },
    'econ_open': {
        'cls': HeatPumpEcon,
        'econ_type': 'open'
    },
    'econ_open_trans': {
        'cls': HeatPumpEconTrans,
        'econ_type': 'open'
    },
    'econ_open_ihx': {
        'cls': HeatPumpEconIHX,
        'econ_type': 'open'
    },
    'econ_open_ihx_trans': {
        'cls': HeatPumpEconIHXTrans,
        'econ_type': 'open'
    },
    'ihx_econ_closed': {
        'cls': HeatPumpIHXEcon,
        'econ_type': 'closed'
    },
    'ihx_econ_closed_trans': {
        'cls': HeatPumpIHXEconTrans,
        'econ_type': 'closed'
    },
    'ihx_econ_open': {
        'cls': HeatPumpIHXEcon,
        'econ_type': 'open'
    },
    'ihx_econ_open_trans': {
        'cls': HeatPumpIHXEconTrans,
        'econ_type': 'open'
    },
    'pc_econ_closed': {
        'cls': HeatPumpPC,
        'econ_type': 'closed'
    },
    'pc_econ_closed_trans': {
        'cls': HeatPumpPCTrans,
        'econ_type': 'closed'
    },
    'pc_econ_closed_ihx': {
        'cls': HeatPumpPCIHX,
        'econ_type': 'closed'
    },
    'pc_econ_closed_ihx_trans': {
        'cls': HeatPumpPCIHXTrans,
        'econ_type': 'closed'
    },
    'pc_econ_open': {
        'cls': HeatPumpPC,
        'econ_type': 'open'
    },
    'pc_econ_open_trans': {
        'cls': HeatPumpPCTrans,
        'econ_type': 'open'
    },
    'pc_econ_open_ihx': {
        'cls': HeatPumpPCIHX,
        'econ_type': 'open'
    },
    'pc_econ_open_ihx_trans': {
        'cls': HeatPumpPCIHXTrans,
        'econ_type': 'open'
    },
    'ihx_pc_econ_closed': {
        'cls': HeatPumpIHXPC,
        'econ_type': 'closed'
    },
    'ihx_pc_econ_closed_trans': {
        'cls': HeatPumpIHXPCTrans,
        'econ_type': 'closed'
    },
    'ihx_pc_econ_closed_ihx': {
        'cls': HeatPumpIHXPCIHX,
        'econ_type': 'closed'
    },
    'ihx_pc_econ_closed_ihx_trans': {
        'cls': HeatPumpIHXPCIHXTrans,
        'econ_type': 'closed'
    },
    'ihx_pc_econ_open': {
        'cls': HeatPumpIHXPC,
        'econ_type': 'open'
    },
    'ihx_pc_econ_open_trans': {
        'cls': HeatPumpIHXPCTrans,
        'econ_type': 'open'
    },
    'ihx_pc_econ_open_ihx': {
        'cls': HeatPumpIHXPCIHX,
        'econ_type': 'open'
    },
    'ihx_pc_econ_open_ihx_trans': {
        'cls': HeatPumpIHXPCIHXTrans,
        'econ_type': 'open'
    },
    'flash': {
        'cls': HeatPumpFlash,
        'econ_type': None
    },
    'flash_trans': {
        'cls': HeatPumpFlashTrans,
        'econ_type': None
    },
    'cascade': {
        'cls': HeatPumpCascade,
        'econ_type': None
    },
    'cascade_trans': {
        'cls': HeatPumpCascadeTrans,
        'econ_type': None
    },
    'cascade_2ihx': {
        'cls': HeatPumpCascade2IHX,
        'econ_type': None
    },
    'cascade_2ihx_trans': {
        'cls': HeatPumpCascade2IHXTrans,
        'econ_type': None
    },
    'cascade_ic': {
        'cls': HeatPumpCascadeIC,
        'econ_type': None
    },
    'cascade_ic_trans': {
        'cls': HeatPumpCascadeICTrans,
        'econ_type': None
    },
    'cascade_flash': {
        'cls': HeatPumpCascadeFlash,
        'econ_type': None
    },
    'cascade_flash_trans': {
        'cls': HeatPumpCascadeFlashTrans,
        'econ_type': None
    },
    'cascade_econ_closed': {
        'cls': HeatPumpCascadeEcon,
        'econ_type': 'closed'
    },
    'cascade_econ_closed_trans': {
        'cls': HeatPumpCascadeEconTrans,
        'econ_type': 'closed'
    },
    'cascade_econ_closed_ihx': {
        'cls': HeatPumpCascadeEconIHX,
        'econ_type': 'closed'
    },
    'cascade_econ_closed_ihx_trans': {
        'cls': HeatPumpCascadeEconIHXTrans,
        'econ_type': 'closed'
    },
    'cascade_econ_open': {
        'cls': HeatPumpCascadeEcon,
        'econ_type': 'open'
    },
    'cascade_econ_open_trans': {
        'cls': HeatPumpCascadeEconTrans,
        'econ_type': 'open'
    },
    'cascade_econ_open_ihx': {
        'cls': HeatPumpCascadeEconIHX,
        'econ_type': 'open'
    },
    'cascade_econ_open_ihx_trans': {
        'cls': HeatPumpCascadeEconIHXTrans,
        'econ_type': 'open'
    },
    'cascade_ihx_econ_closed': {
        'cls': HeatPumpCascadeIHXEcon,
        'econ_type': 'closed'
    },
    'cascade_ihx_econ_closed_trans': {
        'cls': HeatPumpCascadeIHXEconTrans,
        'econ_type': 'closed'
    },
    'cascade_ihx_econ_open': {
        'cls': HeatPumpCascadeIHXEcon,
        'econ_type': 'open'
    },
    'cascade_ihx_econ_open_trans': {
        'cls': HeatPumpCascadeIHXEconTrans,
        'econ_type': 'open'
    },
    'cascade_pc_econ_closed': {
        'cls': HeatPumpCascadePC,
        'econ_type': 'closed'
    },
    'cascade_pc_econ_closed_trans': {
        'cls': HeatPumpCascadePCTrans,
        'econ_type': 'closed'
    },
    'cascade_pc_econ_closed_ihx': {
        'cls': HeatPumpCascadePCIHX,
        'econ_type': 'closed'
    },
    'cascade_pc_econ_closed_ihx_trans': {
        'cls': HeatPumpCascadePCIHXTrans,
        'econ_type': 'closed'
    },
    'cascade_pc_econ_open': {
        'cls': HeatPumpCascadePC,
        'econ_type': 'open'
    },
    'cascade_pc_econ_open_trans': {
        'cls': HeatPumpCascadePCTrans,
        'econ_type': 'open'
    },
    'cascade_pc_econ_open_ihx': {
        'cls': HeatPumpCascadePCIHX,
        'econ_type': 'open'
    },
    'cascade_pc_econ_open_ihx_trans': {
        'cls': HeatPumpCascadePCIHXTrans,
        'econ_type': 'open'
    },
    'cascade_ihx_pc_econ_closed': {
        'cls': HeatPumpCascadeIHXPC,
        'econ_type': 'closed'
    },
    'cascade_ihx_pc_econ_closed_trans': {
        'cls': HeatPumpCascadeIHXPCTrans,
        'econ_type': 'closed'
    },
    'cascade_ihx_pc_econ_closed_ihx': {
        'cls': HeatPumpCascadeIHXPCIHX,
        'econ_type': 'closed'
    },
    'cascade_ihx_pc_econ_closed_ihx_trans': {
        'cls': HeatPumpCascadeIHXPCIHXTrans,
        'econ_type': 'closed'
    },
    'cascade_ihx_pc_econ_open': {
        'cls': HeatPumpCascadeIHXPC,
        'econ_type': 'open'
    },
    'cascade_ihx_pc_econ_open_trans': {
        'cls': HeatPumpCascadeIHXPCTrans,
        'econ_type': 'open'
    },
    'cascade_ihx_pc_econ_open_ihx': {
        'cls': HeatPumpCascadeIHXPCIHX,
        'econ_type': 'open'
    },
    'cascade_ihx_pc_econ_open_ihx_trans': {
        'cls': HeatPumpCascadeIHXPCIHXTrans,
        'econ_type': 'open'
    },
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

    econ = econ_type.lower() if econ_type is not None else None
    for model_key, entry in _model_registry.items():
        if entry['cls'].__name__ == heat_pump_model and entry['econ_type'] == econ:
            break
    else:
        raise ValueError(
            f"No parameter set found for model '{heat_pump_model}' "
            f"with econ_type '{econ_type}'."
            )

    parampath = resources.files('heatpumps').joinpath(
        'models', 'input', f'params_hp_{model_key}.json'
    )
    with open(parampath, 'r', encoding='utf-8') as file:
        params = json.load(file)

    return params


def from_json(filepath):
    """Instantiate a heat pump model class from a JSON save file.

    Parameters
    ----------
    filepath : str or path-like
        Path to a JSON save file in the format produced by the dashboard
        after a design simulation: ``{"model_key": "<key>", "params": {...}}``.

    Returns
    -------
    heat pump model calss instance
        The fully constructed (but not yet simulated) heat pump instance.

    Example
    -------
    >>> from heatpumps.parameters import from_json
    >>> hp = from_json("HeatPumpSimple.json")
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

    entry = _model_registry[model_key]
    cls, econ_type = entry['cls'], entry['econ_type']

    if econ_type is not None:
        return cls(params, econ_type=econ_type)

    return cls(params)

import json
import os

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
    parampath = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 'models', 'input',
            f'params_hp_{hpfilename}.json'
        )
    )
    with open(parampath, 'r', encoding='utf-8') as file:
        params = json.load(file)

    return params

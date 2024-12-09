if __name__ == "__main__":
    from variables import hp_models
    from models.HeatPumpBase import model_registry
else:
    from .variables import hp_models
    from .models.HeatPumpBase import model_registry


__models_parameter_names__ = {
    'HeatPumpSimple': 'simple',
    'HeatPumpSimpleTrans': 'simple_trans',
    'HeatPumpIHX': 'ihx',
    'HeatPumpIHXTrans': 'ihx_trans',
    'HeatPumpIC': 'ic',
    'HeatPumpICTrans': 'ic_trans',
    'HeatPumpEconClosed': 'econ_closed',
    'HeatPumpEconTransClosed': 'econ_closed_trans',
    'HeatPumpEconIHXClosed': 'econ_closed_ihx',
    'HeatPumpEconIHXTransClosed': 'econ_closed_ihx_trans',
    'HeatPumpIHXEconClosed': 'ihx_econ_closed',
    'HeatPumpIHXEconTransClosed': 'ihx_econ_closed_trans',
    'HeatPumpEconOpen': 'econ_open',
    'HeatPumpEconTransOpen': 'econ_open_trans',
    'HeatPumpEconIHXOpen': 'econ_open_ihx',
    'HeatPumpEconIHXTransOpen': 'econ_open_ihx_trans',
    'HeatPumpIHXEconOpen': 'ihx_econ_open',
    'HeatPumpIHXEconTransOpen': 'ihx_econ_open_trans',
    'HeatPumpPCClosed': 'pc_econ_closed',
    'HeatPumpPCTransClosed': 'pc_econ_closed_trans',
    'HeatPumpIHXPCClosed': 'ihx_pc_econ_closed',
    'HeatPumpIHXPCTransClosed': 'ihx_pc_econ_closed_trans',
    'HeatPumpPCIHXClosed': 'pc_econ_closed_ihx',
    'HeatPumpPCIHXTransClosed': 'pc_econ_closed_ihx_trans',
    'HeatPumpIHXPCIHXClosed': 'ihx_pc_econ_closed_ihx',
    'HeatPumpIHXPCIHXTransClosed': 'ihx_pc_econ_closed_ihx_trans',
    'HeatPumpPCOpen': 'pc_econ_open',
    'HeatPumpPCTransOpen': 'pc_econ_open_trans',
    'HeatPumpIHXPCOpen': 'ihx_pc_econ_open',
    'HeatPumpIHXPCTransOpen': 'ihx_pc_econ_open_trans',
    'HeatPumpPCIHXOpen': 'pc_econ_open_ihx',
    'HeatPumpPCIHXTransOpen': 'pc_econ_open_ihx_trans',
    'HeatPumpIHXPCIHXOpen': 'ihx_pc_econ_open_ihx',
    'HeatPumpIHXPCIHXTransOpen': 'ihx_pc_econ_open_ihx_trans',
    'HeatPumpFlash': 'flash',
    'HeatPumpFlashTrans': 'flash_trans',
    'HeatPumpCascade': 'cascade',
    'HeatPumpCascadeTrans': 'cascade_trans',
    'HeatPumpCascade2IHX': 'cascade_2ihx',
    'HeatPumpCascade2IHXTrans': 'cascade_2ihx_trans',
    'HeatPumpCascadeIC': 'cascade_ic',
    'HeatPumpCascadeICTrans': 'cascade_ic_trans',
    'HeatPumpCascadeEconClosed': 'cascade_econ_closed',
    'HeatPumpCascadeEconTransClosed': 'cascade_econ_closed_trans',
    'HeatPumpCascadeIHXEconClosed': 'cascade_ihx_econ_closed',
    'HeatPumpCascadeIHXEconTransClosed': 'cascade_ihx_econ_closed_trans',
    'HeatPumpCascadeEconIHXClosed': 'cascade_econ_closed_ihx',
    'HeatPumpCascadeEconIHXTransClosed': 'cascade_econ_closed_ihx_trans',
    'HeatPumpCascadeEconOpen': 'cascade_econ_open',
    'HeatPumpCascadeEconTransOpen': 'cascade_econ_open_trans',
    'HeatPumpCascadeIHXEconOpen': 'cascade_ihx_econ_open',
    'HeatPumpCascadeIHXEconTransOpen': 'cascade_ihx_econ_open_trans',
    'HeatPumpCascadeEconIHXOpen': 'cascade_econ_open_ihx',
    'HeatPumpCascadeEconIHXTransOpen': 'cascade_econ_open_ihx_trans',
    'HeatPumpCascadePCClosed': 'cascade_pc_econ_closed',
    'HeatPumpCascadePCTransClosed': 'cascade_pc_econ_closed_trans',
    'HeatPumpCascadeIHXPCClosed': 'cascade_ihx_pc_econ_closed',
    'HeatPumpCascadeIHXPCTransClosed': 'cascade_ihx_pc_econ_closed_trans',
    'HeatPumpCascadePCIHXClosed': 'cascade_pc_econ_closed_ihx',
    'HeatPumpCascadePCIHXTransClosed': 'cascade_pc_econ_closed_ihx_trans',
    'HeatPumpCascadeIHXPCIHXClosed': 'cascade_ihx_pc_econ_closed_ihx',
    'HeatPumpCascadeIHXPCIHXTransClosed': 'cascade_ihx_pc_econ_closed_ihx_trans',
    'HeatPumpCascadePCOpen': 'cascade_pc_econ_open',
    'HeatPumpCascadePCTransOpen': 'cascade_pc_econ_open_trans',
    'HeatPumpCascadeIHXPCPpen': 'cascade_ihx_pc_econ_open',
    'HeatPumpCascadeIHXPCTransOpen': 'cascade_ihx_pc_econ_open_trans',
    'HeatPumpCascadePCIHXOpen': 'cascade_pc_econ_open_ihx',
    'HeatPumpCascadePCIHXTransOpen': 'cascade_pc_econ_open_ihx_trans',
    'HeatPumpCascadeIHXPCIHXOpen': 'cascade_ihx_pc_econ_open_ihx',
    'HeatPumpCascadeIHXPCIHXTransOpen': 'cascade_ihx_pc_econ_open_ihx_trans',
    'HeatPumpCascadeFlash': 'cascade_flash',
    'HeatPumpCascadeFlashTrans': 'cascade_flash_trans'
}

def get_params(heat_pump_model):
    """Get params dict for heat pump model class.

    Parameters
    ----------

    heat_pump_model : str
        Name of heat pump model class (e.g. 'HeatPumpEconIHX')
    """
    return hp_models[__models_parameter_names__[heat_pump_model]]


def get_model(params):
    if "econ_type" in params["setup"]:
        return model_registry.items[params["setup"]["type"]](params, econ_type=params["setup"]["econ_type"])
    else:
        return model_registry.items[params["setup"]["type"]](params)
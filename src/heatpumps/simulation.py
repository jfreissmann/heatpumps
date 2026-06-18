import variables as var


def run_design(hp_model_name, params):
    """Run TESPy design simulation of heat pump."""
    if 'econ' in hp_model_name:
        hp = var.hp_model_classes[hp_model_name](
            params, econ_type=var.hp_models[hp_model_name]['econ_type']
            )
    else:
        hp = var.hp_model_classes[hp_model_name](params)

    hp.run_model()

    return hp


def run_partload(hp):
    """Run TESPy offdesign simulation of heat pump."""
    hp.offdesign_simulation()
    partload_char = hp.calc_partload_char()

    return hp, partload_char

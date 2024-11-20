if __name__ == "__main__":
    from .models.HeatPumpBase import model_registry
else:
    from models.HeatPumpBase import model_registry


def run_design(params):
    """Run TESPy design simulation of heat pump."""
    if 'econ' in params["setup"]:
        hp = model_registry.items[params["setup"]["type"]](params, params["setup"]["econ"])
    else:
        hp = model_registry.items[params["setup"]["type"]](params)

    hp.run_model()

    return hp


def run_partload(hp):
    """Run TESPy offdesign simulation of heat pump."""
    hp.offdesign_simulation()
    partload_char = hp.calc_partload_char()

    return hp, partload_char

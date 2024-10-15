
import pytest

from heatpumps.parameters import __models_parameter_names__
from heatpumps.parameters import get_params
from heatpumps.models.HeatPumpBase import model_registry


@pytest.mark.parametrize("model", list(__models_parameter_names__.keys()))
def test_all_models(model):
        specs = model.split("_")
        if len(specs) == 2:
            econ_type = specs[1]
        else:
            econ_type = None

        params = get_params(model, econ_type=econ_type)
        model = model_registry.items[params["setup"]["type"]](params)
        model.run_model()
        model.nw._convergence_check()

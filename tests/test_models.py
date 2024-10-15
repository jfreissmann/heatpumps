
import pytest

from heatpumps.variables import hp_models
from heatpumps.parameters import get_params
from heatpumps.models.HeatPumpBase import model_registry


@pytest.mark.parametrize("model", list(hp_models.keys()))
def test_all_models(model):

        params = hp_models[model]
        if params["setup"].get("econ"):
            model = model_registry.items[params["setup"]["type"]](params, econ_type=params["setup"]["econ"])
        else:
            model = model_registry.items[params["setup"]["type"]](params)

        model.run_model()
        model.nw._convergence_check()

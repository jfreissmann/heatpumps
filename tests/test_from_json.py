"""Round-trip tests for ``parameters.from_json``: rebuild a heat pump instance
from the dashboard's ``{"model_key": ..., "params": ...}`` save file."""
import json

import pytest

from heatpumps import parameters as P
from heatpumps.models import HeatPumpEcon, HeatPumpSimple


def _save_file(tmp_path, model_key, cls_name, econ_type):
    """Write a dashboard-style save file and return its path."""
    params = P.get_params(cls_name, econ_type=econ_type)
    path = tmp_path / f'{model_key}.json'
    path.write_text(
        json.dumps({'model_key': model_key, 'params': params}),
        encoding='utf-8'
    )
    return path


def test_from_json_non_econ(tmp_path):
    path = _save_file(tmp_path, 'simple', 'HeatPumpSimple', None)
    hp = P.from_json(path)
    assert isinstance(hp, HeatPumpSimple)
    assert getattr(hp, 'econ_type', None) is None


@pytest.mark.parametrize('econ_type', ['closed', 'open'])
def test_from_json_econ(tmp_path, econ_type):
    model_key = f'econ_{econ_type}'
    path = _save_file(tmp_path, model_key, 'HeatPumpEcon', econ_type)
    hp = P.from_json(path)
    assert isinstance(hp, HeatPumpEcon)
    assert hp.econ_type == econ_type


def test_from_json_unknown_model_key(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text(
        json.dumps({'model_key': 'NopeModel', 'params': {}}),
        encoding='utf-8'
    )
    with pytest.raises(ValueError):
        P.from_json(path)

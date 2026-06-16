"""Pytest-parametrized compatibility matrix: every model from
``parameters.__model_names`` against every refrigerant listed in
``static/refrigerants.json``, asserting the design solve actually
converged (``hp.nw.status == 0``), not just that it ran without raising.

Models with two refrigerant slots (cascades) get the same candidate
refrigerant in both slots for a given test case -- a simplification to
keep this a single-dimension matrix instead of combinatorial, not a
physically-tuned cascade pairing.

Usage
-----
    pytest tests/test_refrigerant_compatibility.py -q
    pytest tests/test_refrigerant_compatibility.py -k "HeatPumpSimple"
    pytest tests/test_refrigerant_compatibility.py -k "R717"
"""
import json
import logging
import os

import pytest

import heatpumps.models as M
from heatpumps import parameters as P

logging.disable(logging.CRITICAL)


def _load_refrigerants():
    path = os.path.join(
        os.path.dirname(__file__), '..', 'src', 'heatpumps', 'static',
        'refrigerants.json'
    )
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {label: entry['CP'] for label, entry in data.items()}


def _set_refrigerant(params, cp_name):
    if 'wf' in params['fluids']:
        params['fluids']['wf'] = cp_name
        params['setup']['refrig'] = cp_name
    else:
        params['fluids']['wf1'] = cp_name
        params['fluids']['wf2'] = cp_name
        params['setup']['refrig1'] = cp_name
        params['setup']['refrig2'] = cp_name


REFRIGERANTS = _load_refrigerants()
MODEL_KEYS = sorted(P.__dict__['__model_names'])

CASES = [
    (model_key, refrig_label)
    for model_key in MODEL_KEYS
    for refrig_label in REFRIGERANTS
]
CASE_IDS = [
    f'{model_key}-{refrig_label}' for model_key, refrig_label in CASES
]


@pytest.mark.parametrize('model_key,refrig_label', CASES, ids=CASE_IDS)
def test_model_refrigerant_converges(model_key, refrig_label):
    if '_closed' in model_key or '_open' in model_key:
        base, econ = model_key.rsplit('_', 1)
    else:
        base, econ = model_key, None

    params = P.get_params(base, econ_type=econ)
    _set_refrigerant(params, REFRIGERANTS[refrig_label])

    cls = getattr(M, base)
    hp = cls(params, econ_type=econ) if econ else cls(params)
    hp.run_model(iterinfo=False, exergy_analysis=False)

    assert hp.nw.status == 0, (
        f'{model_key} with {refrig_label} did not converge '
        f'(status={hp.nw.status})'
    )

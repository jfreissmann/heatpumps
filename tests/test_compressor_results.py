"""Regression tests for ``HeatPumpBase.get_compressor_results``.

The method used to select compressors by label substring, which also
matched the ``Motor`` labelled after each compressor. A ``Motor`` carries
no material ports, so ``c.inl[0]`` raised ``IndexError`` and the method
was unusable on every model. Selection is by component type now, which
additionally requires skipping the heat source recirculation device: it
is a ``Compressor`` when the source is gaseous, and was never part of
these results.

Usage
-----
    pytest tests/test_compressor_results.py -q
"""
import logging
import math

import pytest
from tespy.components import Compressor

from heatpumps.models import HeatPumpCascade, HeatPumpSimple
from heatpumps.parameters import get_params

logging.disable(logging.CRITICAL)

VARIABLES = ('V_dot', 'p_in', 'p_out', 'PI', 'T_in', 'T_out')

CASES = [
    (HeatPumpSimple, None, ['Compressor']),
    (
        HeatPumpCascade, None,
        ['Low Temperature Compressor', 'High Temperature Compressor']
    ),
    # Gaseous source: 'hs_pump' is a Compressor here, so a plain type
    # check would return it alongside the cycle compressor.
    (HeatPumpSimple, 'Air', ['Compressor']),
]
CASE_IDS = [
    cls.__name__ if source is None else f'{cls.__name__}-{source}'
    for cls, source, _ in CASES
]


@pytest.mark.parametrize('cls,source,expected_labels', CASES, ids=CASE_IDS)
def test_get_compressor_results(cls, source, expected_labels):
    params = get_params(cls.__name__)
    if source is not None:
        params['fluids']['so'] = source

    hp = cls(params=params)
    hp.run_model(iterinfo=False, exergy_analysis=False)

    assert hp.nw.status == 0, (
        f'{cls.__name__} did not converge (status={hp.nw.status})'
    )
    if source is not None:
        assert isinstance(hp.comps['hs_pump'], Compressor), (
            'this case is meant to cover a gaseous heat source, where the '
            'recirculation device is a Compressor'
        )

    results = hp.get_compressor_results()

    assert sorted(results) == sorted(expected_labels)
    assert not any(label.endswith(' Motor') for label in results)
    assert 'Heat Source Recirculation Fan' not in results

    for label, res in results.items():
        assert sorted(res) == sorted(VARIABLES), (
            f'unexpected variables for {label}: {sorted(res)}'
        )
        assert math.isfinite(res['PI']), f'{label} has non-finite PI'
        assert res['PI'] > 1, f'{label} has PI = {res["PI"]}'

"""Intercooler outlet specification of the intercooled heat pump models.

Cooling the first compressor's discharge by the full ``dT_ic`` is only
possible while that leaves superheated vapour. Dry refrigerants are discharged
only a few K above the dew line, so cooling them by 10 K would hand the second
compressor liquid, and the solver could only balance that with a cycle running
backwards. See ``HeatPumpBase._solve_with_intercoolers``.
"""
import pytest

from heatpumps.models import HeatPumpCascadeIC, HeatPumpIC
from heatpumps.models.HeatPumpBase import (IC_MIN_SUPERHEAT,
                                           IntercoolerBypassWarning)
from heatpumps.parameters import get_params


def _set_temperatures(params, source, sink):
    """Set heat source and sink as (feed flow, back flow) in °C."""
    params['B1']['T'], params['B2']['T'] = source
    params['C3']['T'], params['C1']['T'] = sink


@pytest.mark.parametrize('refrig', ['R600', 'R1234YF', 'R1233ZDE'])
def test_ic_dry_refrigerant_stays_superheated(refrig):
    params = get_params('HeatPumpIC')
    params['setup']['refrig'] = refrig
    params['fluids']['wf'] = refrig
    _set_temperatures(params, source=(20, 10), sink=(80, 50))

    hp = HeatPumpIC(params=params)
    hp.run_model(exergy_analysis=False)

    assert (hp.nw.results['Connection']['m'] > 0).all()
    assert hp.conns['A5'].td_dew.val_SI >= IC_MIN_SUPERHEAT - 1e-6
    assert hp.comps['ic'].Q.val_SI <= 0
    assert hp.model_warnings == []


def test_ic_wet_refrigerant_is_cooled_by_dT_ic():
    params = get_params('HeatPumpIC')
    _set_temperatures(params, source=(20, 10), sink=(80, 50))

    hp = HeatPumpIC(params=params)
    hp.run_model(exergy_analysis=False)

    dT = hp.conns['A5'].T.val_SI - hp.conns['A4'].T.val_SI
    assert dT == pytest.approx(params['ic']['dT_ic'])
    assert hp.model_warnings == []


def test_ic_bypasses_intercooler_without_superheat():
    # An efficient first compressor leaves pentane only ~0.2 K superheated:
    # too little to cool, but not yet wet.
    params = get_params('HeatPumpIC')
    params['setup']['refrig'] = params['fluids']['wf'] = 'R601'
    params['comp1']['eta_s'] = 0.79
    _set_temperatures(params, source=(20, 10), sink=(80, 50))

    hp = HeatPumpIC(params=params)
    with pytest.warns(IntercoolerBypassWarning, match='Intercooler'):
        hp.run_model()

    assert hp.comps['ic'].Q.val_SI == 0
    assert hp.comps['ic'].pr.val_SI == 1
    assert hp.conns['A5'].td_dew.val_SI > 0
    assert len(hp.model_warnings) == 1
    assert (hp.nw.results['Connection']['m'] > 0).all()


def test_cascade_ic_rejects_wet_compressor_discharge():
    # Butane compressed from saturated vapour ends inside the two-phase
    # region here. No intercooler setting makes that a plausible cycle.
    params = get_params('HeatPumpCascadeIC')
    params['setup']['refrig1'] = params['fluids']['wf1'] = 'R290'
    params['setup']['refrig2'] = params['fluids']['wf2'] = 'R600'
    _set_temperatures(params, source=(20, 10), sink=(90, 50))

    hp = HeatPumpCascadeIC(params=params)
    with pytest.raises(ValueError, match='discharges wet vapour'):
        hp.run_model()

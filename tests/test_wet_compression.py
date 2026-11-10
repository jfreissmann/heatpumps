"""Checks against compressors taking in or discharging wet vapour.

Dry refrigerants (e.g. pentane, butane) have an overhanging dew line:
compressing them from saturated vapour, as the models specify the evaporator
outlet, can end inside the two-phase region. See
``HeatPumpBase.check_thermodynamic_results`` and ``find_wet_compression``.
"""
import pytest

from heatpumps.models import HeatPumpIC, HeatPumpSimple
from heatpumps.models.HeatPumpBase import (PLAUSIBILITY_HINT,
                                           WetCompressionError,
                                           WetCompressionWarning)
from heatpumps.parameters import get_params


def _simple_params(refrig, source, sink):
    """Simple-cycle parameters, heat source and sink as (feed, back) in °C."""
    params = get_params('HeatPumpSimple')
    params['setup']['refrig'] = params['fluids']['wf'] = refrig
    params['B1']['T'], params['B2']['T'] = source
    params['C3']['T'], params['C1']['T'] = sink
    params['evap']['ttd_l'] = params['cond']['ttd_u'] = 5
    params['offdesign']['save_results'] = False
    return params


def test_dry_refrigerant_wet_discharge_is_rejected():
    hp = HeatPumpSimple(params=_simple_params('R601', (10, 5), (90, 50)))
    with pytest.raises(WetCompressionError, match='discharge wet vapour') as e:
        hp.run_model(exergy_analysis=False)

    # Callers handling the other plausibility errors handle this one, too.
    assert isinstance(e.value, ValueError)
    assert PLAUSIBILITY_HINT in str(e.value)
    assert "'Compressor' (x = 0.9" in str(e.value)


def test_wet_discharge_after_intercooler_is_rejected():
    # The intercooler holds the second compressor's inlet 1 K above the dew
    # line (here bypassed), which is not enough for pentane: compressing it
    # from there ends inside the two-phase region, too.
    params = get_params('HeatPumpIC')
    params['setup']['refrig'] = params['fluids']['wf'] = 'R601'
    params['comp1']['eta_s'] = 0.79
    params['B1']['T'], params['B2']['T'] = 20, 10
    params['C3']['T'], params['C1']['T'] = 80, 50

    hp = HeatPumpIC(params=params)
    with pytest.raises(WetCompressionError, match="'Compressor 2'"):
        hp.run_model(exergy_analysis=False)


@pytest.mark.parametrize('refrig', ['R717', 'R290', 'R1233zd(E)'])
def test_superheated_discharge_passes(refrig):
    hp = HeatPumpSimple(params=_simple_params(refrig, (10, 5), (90, 50)))
    hp.run_model(exergy_analysis=False)

    assert hp.find_wet_compression() == {'inlet': {}, 'outlet': {}}


def test_offdesign_wet_compression_is_flagged():
    # Butane leaves the compressor ~1.3 K superheated in the design case,
    # but raising the sink temperature in offdesign makes it discharge wet.
    params = _simple_params('R600', (20, 10), (70, 40))
    params['offdesign'].update({
        'T_hs_ff_start': 20, 'T_hs_ff_end': 20, 'T_hs_ff_steps': 1,
        'T_cons_ff_start': 70, 'T_cons_ff_end': 100, 'T_cons_ff_steps': 4,
        'partload_min': 1.0, 'partload_max': 1.0, 'partload_steps': 1,
    })
    hp = HeatPumpSimple(params=params)
    hp.run_model(exergy_analysis=False)
    assert hp.offdesign_warnings == []

    with pytest.warns(WetCompressionWarning, match='Wet compression in'):
        hp.offdesign_simulation()

    assert len(hp.offdesign_warnings) == 1
    assert 'Compressor outlet' in hp.offdesign_warnings[0]

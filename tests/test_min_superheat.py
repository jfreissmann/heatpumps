"""Minimum superheat of every compressor discharge.

Dry refrigerants (e.g. pentane, butane) compressed from saturated vapour can
be discharged inside the two-phase region. Where a compressor is fed by an
evaporator, a cascade's intermediate heat exchanger or a closed economizer,
that outlet is superheated by the minimum needed to discharge
``DIS_MIN_SUPERHEAT`` above the dew line; otherwise the model is rejected.
See ``HeatPumpBase._ensure_min_discharge_superheat``.
"""
import pytest

from heatpumps.models import (HeatPumpCascade, HeatPumpEcon, HeatPumpFlash,
                              HeatPumpIC, HeatPumpIHX, HeatPumpSimple)
from heatpumps.models.HeatPumpBase import (DIS_MIN_SUPERHEAT,
                                           PLAUSIBILITY_HINT,
                                           WetCompressionError, superheat)
from heatpumps.parameters import get_params


def _params(model, refrig, source=None, sink=None, ttd=None, **kwargs):
    """Parameters with a refrigerant (HT cycle of cascades) and boundaries.

    Heat source and sink are given as (feed flow, back flow) in °C.
    """
    params = get_params(model, **kwargs)
    if 'wf' in params['fluids']:
        params['setup']['refrig'] = params['fluids']['wf'] = refrig
    else:
        params['setup']['refrig2'] = params['fluids']['wf2'] = refrig
    if source is not None:
        params['B1']['T'], params['B2']['T'] = source
    if sink is not None:
        params['C3']['T'], params['C1']['T'] = sink
    if ttd is not None:
        params['evap']['ttd_l'] = params['cond']['ttd_u'] = ttd
    params['offdesign']['save_results'] = False
    return params


def _discharges_at_minimum(hp, comp_key):
    return superheat(hp.comps[comp_key].outl[0]) == pytest.approx(
        DIS_MIN_SUPERHEAT, abs=1e-3
        )


def test_dry_refrigerant_gets_minimum_evaporator_superheat():
    params = _params('HeatPumpSimple', 'R601', (45, 15), (70, 40), ttd=5)
    hp = HeatPumpSimple(params=params)
    hp.run_model(exergy_analysis=False)

    sh = hp.superheat_adjustments['Evaporator']
    assert 0 < sh < 30
    assert _discharges_at_minimum(hp, 'comp')
    # The evaporator outlet is held at that superheat, which keeps the
    # evaporation temperature at the specified terminal temperature
    # difference.
    assert not hp.conns['A3'].x.is_set
    assert hp.conns['A3'].td_dew.val == pytest.approx(sh)
    assert superheat(hp.conns['A3']) == pytest.approx(sh)
    T_evap = hp.conns['A2'].T.val
    assert params['B2']['T'] - T_evap == pytest.approx(5)


def test_superheated_discharge_needs_no_superheat():
    params = _params('HeatPumpSimple', 'R717', (45, 15), (70, 40), ttd=5)
    hp = HeatPumpSimple(params=params)
    hp.run_model(exergy_analysis=False)

    assert hp.superheat_adjustments == {}
    assert hp.conns['A3'].x.is_set
    assert not hp.conns['A3'].td_dew.is_set


def test_superheat_beyond_heat_source_is_rejected():
    # Pentane would need ~7.8 K suction superheat, but sea water at 10 °C
    # allows only ~5 K above an evaporation temperature of 0 °C.
    params = _params('HeatPumpSimple', 'R601', (10, 5), (90, 50), ttd=5)
    hp = HeatPumpSimple(params=params)
    with pytest.raises(WetCompressionError, match='Evaporator') as e:
        hp.run_model(exergy_analysis=False)

    assert e.value.reason == 'superheat_bound'
    assert isinstance(e.value, ValueError)
    assert PLAUSIBILITY_HINT in str(e.value)


def test_ihx_superheat_adds_to_evaporator_superheat():
    params = _params('HeatPumpIHX', 'R601')
    hp = HeatPumpIHX(params=params)
    hp.run_model(exergy_analysis=False)

    assert hp.superheat_adjustments['Evaporator'] > 0
    assert _discharges_at_minimum(hp, 'comp')
    dT_ihx = hp.conns['A5'].T.val - hp.conns['A4'].T.val
    assert dT_ihx == pytest.approx(params['ihx']['dT_sh'])


def test_cascade_superheat_lowers_ht_evaporation_temperature():
    params = _params('HeatPumpCascade', 'R600')
    hp = HeatPumpCascade(params=params)
    hp.run_model(exergy_analysis=False)

    sh = hp.superheat_adjustments['Intermediate Heat Exchanger']
    assert sh > 0
    assert _discharges_at_minimum(hp, 'HT_comp')
    # The intermediate heat exchanger keeps its terminal temperature
    # difference at the cold side outlet, so the outlet temperature stays and
    # the evaporation temperature of the high temperature cycle drops.
    T_mid = (params['B2']['T'] + params['C3']['T']) / 2
    T_out = T_mid - params['inter']['ttd_u'] / 2
    assert hp.conns['A3'].T.val == pytest.approx(T_out)
    assert hp.comps['inter'].ttd_u.val == pytest.approx(
        params['inter']['ttd_u']
        )
    assert hp.conns['A3'].T_dew.val == pytest.approx(T_out - sh)


def test_closed_economizer_superheats_injection_vapour():
    params = _params('HeatPumpEcon', 'R601', econ_type='closed')
    hp = HeatPumpEcon(params=params, econ_type='closed')
    hp.run_model(exergy_analysis=False)

    assert hp.superheat_adjustments['Economizer'] > 0
    assert _discharges_at_minimum(hp, 'comp2')
    assert hp.comps['econ'].ttd_l.val == pytest.approx(
        params['econ']['ttd_l']
        )


def test_flash_tank_vapour_is_rejected():
    hp = HeatPumpFlash(params=_params('HeatPumpFlash', 'R601'))
    with pytest.raises(WetCompressionError, match="'Compressor 2'") as e:
        hp.run_model(exergy_analysis=False)

    assert e.value.reason == 'no_superheat_dof'


def test_intercooler_cools_less():
    # Butane leaves the second compressor wet when the intercooler cools its
    # inlet down to 1 K above the dew line.
    params = _params('HeatPumpIC', 'R600', (20, 10), (80, 50))
    hp = HeatPumpIC(params=params)
    hp.run_model(exergy_analysis=False)

    sh = hp.superheat_adjustments['Intercooler']
    assert sh > 1
    assert superheat(hp.conns['A5']) == pytest.approx(sh)
    assert _discharges_at_minimum(hp, 'comp2')
    assert hp.comps['ic'].Q.val_SI < 0
    assert hp.model_warnings == []


def test_offdesign_holds_superheat():
    params = _params('HeatPumpSimple', 'R601', (45, 15), (70, 40), ttd=5)
    params['offdesign'].update({
        'T_hs_ff_start': 45, 'T_hs_ff_end': 45, 'T_hs_ff_steps': 1,
        'T_cons_ff_start': 65, 'T_cons_ff_end': 75, 'T_cons_ff_steps': 3,
        'partload_min': 0.6, 'partload_max': 1.0, 'partload_steps': 2,
    })
    hp = HeatPumpSimple(params=params)
    hp.run_model(exergy_analysis=False)
    sh = hp.superheat_adjustments['Evaporator']

    hp.offdesign_simulation()

    assert superheat(hp.conns['A3']) == pytest.approx(sh)
    assert hp.offdesign_warnings == []

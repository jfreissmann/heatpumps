"""Export design and offdesign results for every heat pump model.

This script is meant to be run twice against two different code/dependency
states (e.g. once on this branch with tespy 0.10, once after ``git stash``
with tespy 0.8) so the two result sets can be diffed to check that the
tespy migration did not change model behavior.

Only relies on the public ``HeatPumpBase`` API that is stable across both
code states: ``run_model``, ``offdesign_simulation``, ``.cop``,
``.cop_lorenz``, ``.eta_lorenz``, ``.cop_carnot``, ``.eta_carnot``,
``.epsilon``, ``.m_design``, ``.Q_array``, ``.P_array``, ``.epsilon_array``
and the corresponding range attributes.

Usage
-----
    python tests/export_model_results.py [output_dir]

Defaults to ``tests/_model_export`` relative to the repo root if no output
directory is given.
"""
import json
import math
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from heatpumps import parameters as P  # noqa: E402
import heatpumps.models as M  # noqa: E402

# Small, fixed offdesign grid used for every model so the export stays fast
# and deterministic/comparable between the two code states. T_hs_ff_steps
# is deliberately not overridden: most models default to
# T_hs_ff_start == T_hs_ff_end (a single fixed source temperature), and
# forcing steps=2 there makes np.linspace produce a duplicate value
# (e.g. [10, 10]), which makes the offdesign results MultiIndex match two
# rows for the same point instead of one -- raising "The truth value of a
# Series is ambiguous" deep in HeatPumpBase.offdesign_simulation.
OFFDESIGN_OVERRIDES = {
    'T_cons_ff_steps': 2,
    'partload_min': 0.8,
    'partload_max': 1.0,
    'partload_steps': 2,
    'save_results': False,
}


def sanitize(value):
    """Convert NaN/inf to None so the result is valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def nested_sanitize(value):
    if isinstance(value, list):
        return [nested_sanitize(v) for v in value]
    return sanitize(value)


def export_one(model_key):
    if '_closed' in model_key or '_open' in model_key:
        base, econ = model_key.rsplit('_', 1)
    else:
        base, econ = model_key, None

    result = {'model': base, 'econ_type': econ}

    cls = getattr(M, base, None)
    if cls is None:
        result['error'] = f'no class {base} in heatpumps.models'
        return result

    hp = None
    try:
        params = P.get_params(base, econ_type=econ)
        params['offdesign'] = {**params['offdesign'], **OFFDESIGN_OVERRIDES}

        # Most models default to T_hs_ff_start == T_hs_ff_end (a single
        # fixed source temperature). Give it a real spread so it's
        # actually exercised by T_hs_ff_steps=2 instead of np.linspace
        # producing a duplicate value (which breaks the offdesign results
        # MultiIndex, see OFFDESIGN_OVERRIDES' comment history).
        if (
            params['offdesign']['T_hs_ff_start']
            == params['offdesign']['T_hs_ff_end']
        ):
            params['offdesign']['T_hs_ff_end'] = (
                params['offdesign']['T_hs_ff_start'] + 5
            )
        params['offdesign']['T_hs_ff_steps'] = 2

        # T_cons_ff's own default range can be wide (e.g. 70 to 124),
        # which is a much bigger jump than intended for this small,
        # fast smoke grid. Keep the model's own start value but cap the
        # spread at 5 degrees instead of using its full default range.
        params['offdesign']['T_cons_ff_end'] = (
            params['offdesign']['T_cons_ff_start'] + 5
        )

        if econ is not None:
            hp = cls(params, econ_type=econ)
        else:
            hp = cls(params)

        hp.run_model(iterinfo=False)

        result['design'] = {
            'cop': sanitize(hp.cop),
            'cop_lorenz': sanitize(hp.cop_lorenz),
            'eta_lorenz': sanitize(hp.eta_lorenz),
            'cop_carnot': sanitize(hp.cop_carnot),
            'eta_carnot': sanitize(hp.eta_carnot),
            'epsilon': sanitize(hp.epsilon),
            'm_design': sanitize(hp.m_design),
        }
    except Exception as e:
        result['error'] = f'design failed: {type(e).__name__}: {e}'
        result['traceback'] = traceback.format_exc()
        _cleanup_cache_files(hp)
        return result

    try:
        hp.offdesign_simulation()
        result['offdesign'] = {
            'T_hs_ff_range': nested_sanitize(list(hp.T_hs_ff_range)),
            'T_cons_ff_range': nested_sanitize(list(hp.T_cons_ff_range)),
            'pl_range': nested_sanitize(list(hp.pl_range)),
            'Q_array': nested_sanitize(hp.Q_array),
            'P_array': nested_sanitize(hp.P_array),
            'epsilon_array': nested_sanitize(hp.epsilon_array),
        }
    except Exception as e:
        result['offdesign_error'] = f'{type(e).__name__}: {e}'
        result['offdesign_traceback'] = traceback.format_exc()
    finally:
        _cleanup_cache_files(hp)

    return result


def _cleanup_cache_files(hp):
    """Remove this model's cached design/init state from disk.

    `design_path`/the offdesign init cache are named after
    ``params['setup']['type']`` + refrigerant (see
    `HeatPumpBase._init_dir_paths`), which different econ-type variants of
    the same model can share. Without removing them between models, a
    stale file from a previous model can leak into the next one's
    offdesign read (e.g. if that next model's own save is ever skipped).
    """
    if hp is None:
        return
    for path in [
        getattr(hp, 'design_path', None),
        os.path.join(
            os.path.dirname(getattr(hp, 'design_path', '') or ''),
            f'{getattr(hp, "subdirname", "")}_init.json'
        ),
    ]:
        if path and os.path.exists(path):
            os.remove(path)


def main():
    import logging
    logging.disable(logging.CRITICAL)

    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), '_model_export'
    )
    os.makedirs(out_dir, exist_ok=True)

    model_names = P.__dict__['__model_names']

    summary = {}
    for key in sorted(model_names):
        print(f'Exporting {key} ...', flush=True)
        result = export_one(key)
        path = os.path.join(out_dir, f'{key}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        if 'error' in result:
            summary[key] = f"DESIGN FAILED: {result['error']}"
        elif 'offdesign_error' in result:
            summary[key] = f"OFFDESIGN FAILED: {result['offdesign_error']}"
        else:
            summary[key] = 'OK'

    summary_path = os.path.join(out_dir, '_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    n_ok = sum(1 for v in summary.values() if v == 'OK')
    print(f'\n{n_ok}/{len(summary)} OK. Results written to {out_dir}')
    for key, status in summary.items():
        if status != 'OK':
            print(f'  {key}: {status}')


if __name__ == '__main__':
    main()

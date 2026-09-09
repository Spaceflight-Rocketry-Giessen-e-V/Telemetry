# -*- coding: utf-8 -*-
"""Guard: the single source of truth cannot silently drift.

Two authoritative sources:
  * config.py           - the LOCKED design inputs (geometry, substrate, mounting).
  * fab/results.json    - the VALIDATED sim outputs (metrics), written by an openEMS run.

Everything else (board, gerbers, enclosure, silk, datasheet) derives from these. This test
fails if they disagree, or if the datasheet stops quoting the locked numbers - so a change
in one place that is not propagated is caught HERE instead of shipping a mismatched board.

    python tests/test_no_drift.py     # standalone PASS/FAIL (exit 1 on drift)
    pytest tests/test_no_drift.py     # or under pytest
"""
import _bootstrap  # noqa: F401  - project root on sys.path (no openEMS solve needed)
import json
import os
import sys

import config

_HERE    = os.path.dirname(os.path.abspath(__file__))
_ROOT    = os.path.dirname(_HERE)
_RESULTS = os.path.join(_ROOT, 'fab', 'results.json')


def _results():
    with open(_RESULTS, encoding='utf-8') as f:
        return json.load(f)


# config.py (source of truth)  <->  results.json key  (validated record)
_GEOM = [
    ('W',         config.W_CP_INIT,           'W_mm'),
    ('trunc',     config.TRUNC_INIT,          'trunc_mm'),
    ('inset',     config.INSET_Y,             'inset_y_mm'),
    ('sub_hw',    config.SUB_HW_DEFAULT,      'sub_hw_mm'),
    ('epsR',      config.substrate_epsR,      'substrate_epsR'),
    ('thickness', config.substrate_thickness, 'substrate_h_mm'),
    ('f_MHz',     config.f_target / 1e6,      'f_target_MHz'),
]


def test_config_matches_results_json():
    """The board/enclosure geometry (config) must equal what was simulated (results.json)."""
    r = _results()
    bad = []
    for name, cfg, key in _GEOM:
        if key not in r:
            bad.append(f'{name}: results.json has no "{key}"')
        elif abs(float(cfg) - float(r[key])) > 1e-3:
            bad.append(f'{name}: config={cfg} != results.json={r[key]}')
    assert not bad, 'config.py <-> results.json DRIFT (re-run the sim or refreeze config):\n  ' \
                    + '\n  '.join(bad)


def test_datasheet_quotes_locked_numbers():
    """docs/research.md (the datasheet) must quote the current locked dimensions/substrate."""
    tokens = [f'{config.W_CP_INIT:g}', f'{config.TRUNC_INIT:g}', f'{config.INSET_Y:g}',
              f'{2 * config.SUB_HW_DEFAULT:g}', f'{config.substrate_epsR:g}',
              f'{config.f_target / 1e6:g}', config.substrate_material]
    txt = open(os.path.join(_ROOT, 'docs', 'research.md'), encoding='utf-8').read()
    missing = [t for t in tokens if t not in txt]
    assert not missing, 'docs/research.md no longer quotes the locked design: ' + ', '.join(missing)


if __name__ == '__main__':
    fails = 0
    for fn in (test_config_matches_results_json, test_datasheet_quotes_locked_numbers):
        try:
            fn()
            print(f'PASS  {fn.__name__}')
        except AssertionError as e:
            fails += 1
            print(f'FAIL  {fn.__name__}\n  {e}')
    print('\nno-drift:', 'OK' if not fails else f'{fails} FAILURE(S)')
    sys.exit(1 if fails else 0)

# -*- coding: utf-8 -*-
"""Stage 3 — optimizer-machinery smoke test (tiny NrTS — NOT a physics result).

Runs the REAL grid + confirm search through the actual ProcessPoolExecutor / spawned
worker / coverage-cost / record path, but with a tiny grid at tiny NrTS so it finishes
in minutes. Validates the parallel pool, PatchParams pickling across spawn, the
worker's build+run+NF2FF+metrics chain, _screen_cost / _cost / _record, and the
GRID->CONFIRM selection — the parts not exercised by the per-sim harnesses — before
committing the machine to the full run. The reported metrics are meaningless (sims
unconverged); only "did it run cleanly and pick a best without exceptions" matters.

    python tests/stage3_optimizer.py
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import sys
import time

import config

# Tiny machinery test: shrink the grid AND the fidelity BEFORE importing the optimizer.
config.NrTS_screen = 3000
config.NrTS_opt    = 3000          # CONFIRM fidelity (== final); tiny here
config.NrTS_final  = 3000
config.GRID_W_FRAC   = (0.98, 1.02)  # 2 W
config.GRID_TRUNC_MM = (7.0, 9.0)    # 2 truncation  -> 4 grid sims
config.N_CONFIRM     = 1             # + 1 confirm = 5 sims total

from src.optimizer import Optimizer, _cost, n_opt
from src.params import default_params


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print('=' * 64)
    print(f'OPTIMIZER SMOKE TEST  (grid {len(config.GRID_W_FRAC)}x{len(config.GRID_TRUNC_MM)}'
          f' + {config.N_CONFIRM} confirm = {n_opt()} sims, NrTS={config.NrTS_screen}, '
          f'machinery only)')
    print('=' * 64)

    opt = Optimizer(default_params().with_(W_mm=84.6))
    t0 = time.monotonic()
    p_best, log = opt.run()
    dt = time.monotonic() - t0

    n_ok   = sum(1 for x in log if x.get('ok', False))
    n_fail = sum(1 for x in log if not x.get('ok', True))
    n_grid = sum(1 for x in log if x['phase'] == 'GRID')
    n_conf = sum(1 for x in log if x['phase'] == 'CONF')
    print('\n' + '=' * 64)
    print(f'  records: {len(log)}  (GRID {n_grid}, CONF {n_conf})   ok: {n_ok}   '
          f'failed: {n_fail}')
    print(f'  best   : W={p_best.W_mm:.2f} mm  trunc={p_best.trunc_mm:.2f} mm  '
          f'cost {_cost(min(log, key=_cost)):+.3f}')
    print(f'  wall-clock: {dt:.0f}s  ->  implies ~{dt/60:.1f} min at NrTS={config.NrTS_screen}')
    # GRID count is the invariant; the CONFIRM count is data-dependent (one per arm
    # column that produced a usable result, capped at N_CONFIRM), so don't assert the
    # constant n_opt() total — only that the full grid ran and at least one confirm did.
    expected_grid = len(config.GRID_W_FRAC) * len(config.GRID_TRUNC_MM)
    ok = (n_grid == expected_grid and 1 <= n_conf <= config.N_CONFIRM and n_ok >= 1)
    print(f'  MACHINERY: '
          f'{"OK — pool/worker/grid/confirm/cost/record all ran" if ok else "PROBLEM — see failures"}')
    print('=' * 64)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

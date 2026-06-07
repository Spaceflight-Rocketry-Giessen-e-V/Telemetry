# -*- coding: utf-8 -*-
"""Fixed-dims board-size sweep: AR<=3 beamwidth vs ground-plane size on NP-140F.

W / truncation / inset are FROZEN at the single-feed seed; only sub_hw varies. Board
size barely moves resonance / CP but sets the far-field beamwidth, so this isolates
the COVERAGE-vs-board curve. Full 150k fidelity per point (beamwidth does NOT converge
at the cheap 60k screen). Re-run after the optimiser settles the final dims.

Reuses src.optimizer._run_sim_worker (build_patch_sim -> FDTD -> coverage metrics),
no KiCad / graphs. Run:  python tests/board_sweep.py
"""
import _bootstrap  # noqa: F401 - openEMS DLL discovery + project root on sys.path (keep first)

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import config
from src.params import PatchParams
from src.optimizer import _run_sim_worker

# Single-feed seed dims (config synthesis); only sub_hw varies.
BASE = dict(W_mm=config.W_CP_INIT, trunc_mm=config.TRUNC_INIT, inset_y_mm=config.INSET_Y)
SUB_HW = [80.0, 85.0, 90.0]          # -> 160 / 170 / 180 mm boards
NrTS   = config.NrTS_final            # 150000 (beamwidth-converged fidelity)


def main():
    cores = os.cpu_count() or 1
    nthreads = max(1, cores // len(SUB_HW))
    jobs = []
    for hw in SUB_HW:
        p = PatchParams.from_dict({**BASE, 'sub_hw_mm': hw})
        jobs.append((hw, {'p': p, 'NrTS': NrTS,
                          'sim_suffix': f'BW{int(2 * hw)}', 'num_threads': nthreads}))

    print(f'Board sweep {[int(2 * hw) for hw in SUB_HW]} mm @ NrTS={NrTS}  '
          f'({len(jobs)} concurrent, {nthreads} threads/sim)', flush=True)
    t0 = time.monotonic()
    results = {}
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        fut = {ex.submit(_run_sim_worker, kw): hw for hw, kw in jobs}
        for f in as_completed(fut):
            hw = fut[f]
            r = f.result()
            results[hw] = r
            tag = 'RHCP' if r.get('rhcp', True) else 'LHCP'
            note = f'  ERROR: {r.get("_exc")}' if r.get('_exc') else ''
            print(f'  [{int(2 * hw)} mm done +{(time.monotonic() - t0) / 60:.0f}m]  '
                  f'f_res={r["f_res"] / 1e6:6.1f}  S11={r["s11_dB"]:+6.1f}  '
                  f'AR={r["ar_dB"]:5.2f} {tag}  BW={r.get("ar_bw_deg", 0):3.0f}deg  '
                  f'worstAR={r.get("ar_cone_dB", 99):5.1f}  '
                  f'D={r["Dmax"]:+5.2f}dBi  eta={r.get("eta_rad", 0)*100:4.1f}%{note}',
                  flush=True)

    # Dmax is now peak directivity in dBi (10*log10 of openEMS Dmax); eta_rad = Prad/P_acc.
    print('\n=== BOARD SWEEP (NP-140F, er 4.15, W=72.5/arm=40 fixed) ===')
    print(f'{"board":>7} {"f_res":>8} {"S11":>7} {"AR0":>6} {"AR<=3 BW":>9} '
          f'{"worstAR@cone":>12} {"D_dBi":>6} {"eta_r":>6}  hand')
    for hw in SUB_HW:
        r = results[hw]
        tag = 'RHCP' if r.get('rhcp', True) else 'LHCP'
        print(f'{int(2 * hw):>5}mm {r["f_res"] / 1e6:>7.1f} {r["s11_dB"]:>6.1f} '
              f'{r["ar_dB"]:>6.2f} {r.get("ar_bw_deg", 0):>7.0f}deg '
              f'{r.get("ar_cone_dB", 99):>11.1f} {r["Dmax"]:>6.2f} '
              f'{r.get("eta_rad", 0)*100:>5.1f}%  {tag}')

    with open('board_sweep_results.json', 'w', encoding='utf-8') as f:
        json.dump({int(2 * hw): results[hw] for hw in SUB_HW}, f, indent=2)
    print(f'\nTotal {(time.monotonic() - t0) / 60:.0f} min. Saved board_sweep_results.json')


if __name__ == '__main__':
    main()

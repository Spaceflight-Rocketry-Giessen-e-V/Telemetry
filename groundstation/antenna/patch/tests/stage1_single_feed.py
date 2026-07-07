# -*- coding: utf-8 -*-
"""Stage 1 — single-feed corner-truncated patch resonance scan.

Builds the single-feed CP patch (build_patch_sim) at the default truncation, runs a
short FDTD per candidate patch side W, and reports resonance / S11 / Dmax — a quick
way to centre the resonance on f_target before the full W×truncation optimise. AR is
NOT judged here (it needs full fidelity + the truncation grid); use the optimiser /
run.py for the converged CP metrics.

Gate: S11 <= -10 dB and resonance within +-a few MHz of f_target; Dmax ~5-7 dBi.

Usage:
    python tests/stage1_single_feed.py                 # one sim at the analytical seed W
    python tests/stage1_single_feed.py 80 83 86        # explicit patch sides W (mm)
    STAGE1_NRTS=40000 python tests/stage1_single_feed.py   # override time steps (speed)
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import shutil
import sys
import tempfile

import numpy as np

import config
from src.metrics import s11_db, directivity_dbi
from src.model import build_patch_sim
from src.params import default_params

NrTS = int(os.environ.get('STAGE1_NRTS', '50000'))


def run_one(W: float) -> dict:
    p  = default_params().with_(W_mm=W)
    sp = tempfile.mkdtemp(prefix=f'stage1_W{W:.1f}_')
    try:
        FDTD, _CSX, port, nf2ff = build_patch_sim(p, NrTS)
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))

        f = np.linspace(max(100e6, config.f_target - config.fc),
                        config.f_target + config.fc, 401)
        port.CalcPort(sp, f)
        s11 = s11_db(port.uf_ref, port.uf_inc)
        mask = s11 < -10
        f_res = (float(np.average(f[mask], weights=-s11[mask])) if mask.any()
                 else float(f[np.argmin(s11)]))
        i_ft   = int(np.argmin(np.abs(f - config.f_target)))
        zin    = port.uf_tot[i_ft] / port.if_tot[i_ft]
        # full sphere → trustworthy Dmax/Prad (a single θ=0 point cannot integrate Prad,
        # so its Dmax would be meaningless); report directivity in dBi (10·log10).
        res    = nf2ff.CalcNF2FF(sp, f_res, theta=np.arange(0.0, 180.1, 5.0),
                                 phi=np.arange(0.0, 360.0, 20.0), center=[0, 0, 1e-3])
        return dict(W=W, f_res=f_res,
                    s11_ft=float(np.interp(config.f_target, f, s11)),
                    s11_res=float(np.interp(f_res, f, s11)),
                    Dmax=float(directivity_dbi(res.Dmax[0])), zin=zin)
    finally:
        shutil.rmtree(sp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    seed = default_params()
    Ws = [float(a) for a in sys.argv[1:]] or [round(seed.W_mm, 1)]

    print(f'Stage-1 single-feed square patch  (NrTS={NrTS}  '
          f'f_target={config.f_target/1e6:.2f} MHz  eps_r={config.substrate_epsR}  '
          f'tand={config.substrate_tanD})')
    print(f'  seeds: W={seed.W_mm:.2f} mm  inset_y={seed.inset_y_mm:.1f} mm  '
          f'sub_hw={seed.sub_hw_mm:.0f} mm  feed_w={config.FEED_W} mm  '
          f'mesh_res={config.mesh_res:.2f} mm')
    print(f'{"W mm":>7} {"f_res":>9} {"off MHz":>8} {"S11@ft":>8} '
          f'{"S11@res":>8} {"Dmax":>7} {"Zin @ ft":>16}')
    for W in Ws:
        r = run_one(W)
        print(f'{r["W"]:>7.2f} {r["f_res"]/1e6:>8.2f} '
              f'{(r["f_res"]-config.f_target)/1e6:>+8.2f} {r["s11_ft"]:>8.1f} '
              f'{r["s11_res"]:>8.1f} {r["Dmax"]:>7.2f}  '
              f'{r["zin"].real:>6.1f}{r["zin"].imag:+.1f}j', flush=True)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""Stage 2 — full dual-feed model: convergence + RHCP + coverage read-out.

Runs build_full_sim at a chosen NrTS with verbose=1 so the energy-decay trace is
visible (did the sim reach EndCriteria, or run out of timesteps?), then reports
S11/f_res at the MSL input and the coverage metrics (boresight AR + handedness,
AR<=3 dB beamwidth, worst AR over the cone, min RHCP gain over the cone, Dmax) AT
f_target — exactly the quantities the optimiser and post-processor select on.

This is both the Stage-2 gate (does the locked coupler topology actually produce
RHCP?) and the general "simulate smart" workhorse — one sim answers "is it
converging, where is resonance, is it RHCP, how good is the AR". (Supersedes the
former full_check, which evaluated only at f_res.)

    python tests/stage2_dual_feed.py                 # default W, NrTS=120000
    python tests/stage2_dual_feed.py 84.9 150000     # W=84.9 mm, NrTS=150000
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import shutil
import sys
import tempfile

import numpy as np

import config
from src.metrics import (s11_db, axial_ratio_db, cp_center_freq, ar_beamwidth_deg,
                         worst_ar_over_cone, min_gain_over_cone)
from src.model import build_full_sim
from src.params import default_params


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    W    = float(sys.argv[1]) if len(sys.argv) > 1 else default_params().W_mm
    NrTS = int(sys.argv[2]) if len(sys.argv) > 2 else config.NrTS_opt
    arm  = float(sys.argv[3]) if len(sys.argv) > 3 else default_params().cpl_arm_mm
    ins  = float(sys.argv[4]) if len(sys.argv) > 4 else default_params().inset_x_mm
    p = default_params().with_(W_mm=W, cpl_arm_mm=arm, inset_x_mm=ins, inset_y_mm=ins)

    print('=' * 70)
    print(f'STAGE-2 DUAL-FEED  W={W:.2f}  arm={arm:.2f}  inset={ins:.2f}  NrTS={NrTS}'
          f'  f_target={config.f_target/1e6:.2f} MHz')
    print('=' * 70)

    sp = tempfile.mkdtemp(prefix='stage2_')
    try:
        FDTD, _CSX, port, nf = build_full_sim(p, NrTS)
        FDTD.Run(sp, verbose=1, cleanup=True, numThreads=(os.cpu_count() or 0))

        # ── S11 / resonance ──
        f = np.linspace(max(100e6, config.f_target - config.fc),
                        config.f_target + config.fc, 401)
        port.CalcPort(sp, f)
        s11 = s11_db(port.uf_ref, port.uf_inc)
        f_res = cp_center_freq(f, s11)
        s11_ft  = float(np.interp(config.f_target, f, s11))
        s11_res = float(np.interp(f_res, f, s11))
        Zin_ft  = complex(np.interp(config.f_target, f, np.real(port.uf_tot/port.if_tot)),
                          np.interp(config.f_target, f, np.imag(port.uf_tot/port.if_tot)))

        # ── coverage NF2FF at f_target ──
        th = np.arange(0.0, 90.1, 2.0)
        ph = [0.0, 45.0, 90.0, 135.0]
        res = nf.CalcNF2FF(sp, config.f_target, theta=th, phi=ph, center=[0, 0, 1e-3])
        Dmax = float(res.Dmax[0])
        E_rh = res.E_cprh[0]; E_lh = res.E_cplh[0]; Emax = float(np.max(res.E_norm[0]))
        ar0, is_rhcp = axial_ratio_db(E_rh[1, :], E_lh[1, :])
        ar_th, g_th = [], []
        for i in range(len(th)):
            j0 = 1 if i == 0 else i
            ar_th.append(max(axial_ratio_db(np.array([E_rh[j0, k]]),
                                            np.array([E_lh[j0, k]]))[0]
                             for k in range(len(ph))))
            g_th.append(Dmax + 20.0*np.log10(min(abs(E_rh[i, k]) for k in range(len(ph)))/Emax + 1e-12))
        ar_th = np.array(ar_th); g_th = np.array(g_th)
        bw3   = ar_beamwidth_deg(th, ar_th)
        worst = worst_ar_over_cone(th, ar_th, config.COVER_CONE_DEG)
        gmin  = min_gain_over_cone(th, g_th, config.COVER_CONE_DEG)

        print('\n' + '=' * 70)
        print('RESULT')
        print('=' * 70)
        print(f'  f_res         : {f_res/1e6:8.2f} MHz   (offset {(f_res-config.f_target)/1e6:+.2f} MHz)')
        print(f'  S11 @ f_target: {s11_ft:7.1f} dB    @ f_res: {s11_res:.1f} dB')
        print(f'  Zin @ f_target: {Zin_ft.real:.1f} {Zin_ft.imag:+.1f}j ohm')
        print(f'  AR boresight  : {ar0:7.2f} dB    sense: {"RHCP" if is_rhcp else "LHCP (SWAP!)"}')
        print(f'  AR<=3 beamwid : {bw3:6.1f} deg   worst AR / {config.COVER_CONE_DEG:.0f} cone: {worst:.2f} dB')
        print(f'  min RHCP gain : {gmin:6.2f} dBic   Dmax: {Dmax:.2f} dBi')
        print('  AR vs theta   :', '  '.join(f'{t:.0f}:{a:.1f}' for t, a in zip(th[::3], ar_th[::3])))
        gate = (s11_res <= -10 and ar0 <= 3.0 and is_rhcp
                and abs(f_res - config.f_target) <= 5e6)
        print(f'  STAGE-2 GATE  : {"PASS" if gate else "needs work"}'
              f'  (S11<=-10, AR<=3, RHCP, |df|<=5 MHz)')
        print('=' * 70)
    finally:
        shutil.rmtree(sp, ignore_errors=True)


if __name__ == '__main__':
    main()

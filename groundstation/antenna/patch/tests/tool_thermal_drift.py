# -*- coding: utf-8 -*-
"""Tool — THERMAL drift of the CP null across the ground-station temperature swing.

The repo's "cold-AR" per-board gate is a ROOM-TEMPERATURE RF acceptance test — it measures
manufacturing/SMA/radome scatter, NOT temperature. But FR-4-class laminates have a temperature
coefficient of permittivity (TCDk) of order a few hundred ppm/degC, so a board trimmed to land
CP in-channel at 25 degC drifts off-channel when the station bakes in the sun or runs on a cold
dawn. Over a 50-70 degC swing the null can walk several-to-many MHz — comparable to or larger
than the eps-lot budget AND the ~7.5 MHz AR<=3 band itself — and a one-time room-temp tune
CANNOT cancel a moving target. This quantifies it: at fixed design dims it sweeps temperature,
applying BOTH levers that move resonance with T:

    eps_r(T) = eps_r0 * (1 + TCDk*1e-6*(T - T_ref))        # dominant (datasheet TCDk)
    W(T), trunc(T) = dims0 * (1 + CTE*1e-6*(T - T_ref))    # in-plane thermal expansion (CTE)

and reports, per T, where the AR null lands, AR AT the channel, and whether AR<=3 holds across
869.4-869.65 MHz — i.e. over what temperature window the board still ships CP.

!! TCDk / CTE here are PLACEHOLDERS (representative FR-4-class values). Get NP-140F's actual
   TCDk + CTE from the datasheet/fab IN WRITING (alongside the eps confirmation) and pass them
   in; this tool then gives the true thermal CP window. It shows SENSITIVITY, not a precise
   prediction, until those numbers are confirmed.

    python tests/tool_thermal_drift.py
    THERMAL_TCDK=-300 THERMAL_TMIN=-10 THERMAL_TMAX=45 python tests/tool_thermal_drift.py
    THERMAL_W=82.7 THERMAL_TR=11.0 python tests/tool_thermal_drift.py   # point at a candidate
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import json
import os
import shutil
import sys
import tempfile

import numpy as np
from openEMS.physical_constants import EPS0

import config
from src.params import PatchParams
from src.metrics import axial_ratio_db, s11_db
from src.model import build_patch_sim

NrTS = int(os.environ.get('THERMAL_NRTS', str(config.NrTS_final)))

# Design dims under test (default = current deliverable; override to test a candidate).
W0   = float(os.environ.get('THERMAL_W',  '82.5'))
TR0  = float(os.environ.get('THERMAL_TR', '8.25'))
INS0 = float(os.environ.get('THERMAL_INSET', '5.8'))

# Material thermal coefficients — PLACEHOLDER FR-4-class values, CONFIRM for NP-140F.
TCDK = float(os.environ.get('THERMAL_TCDK', '-300'))   # ppm/degC, d(eps_r)/dT  (neg: eps falls as T rises)
CTE  = float(os.environ.get('THERMAL_CTE',  '15'))     # ppm/degC, in-plane dimensional expansion
T_REF = float(os.environ.get('THERMAL_TREF', '25'))    # degC, the dims/eps were defined at

# Ground-station operating envelope (a sheltered ground antenna, not the rocket's altitude swing).
T_MIN = float(os.environ.get('THERMAL_TMIN', '-15'))
T_MAX = float(os.environ.get('THERMAL_TMAX', '55'))
T_STEP = float(os.environ.get('THERMAL_TSTEP', '17.5'))

EPS0_R = config.substrate_epsR     # nominal eps at T_REF (4.15)
CHAN_LO, CHAN_HI = 869.4e6, 869.65e6
F_TARGET = config.f_target
OUT = os.path.join(os.getcwd(), 'thermal_drift_results.json')


def _contiguous_band(f, ar, f0, thr=3.0):
    """[lo, hi] (Hz) of the contiguous AR<=thr band containing f0, edges interpolated."""
    i0 = int(np.argmin(np.abs(f - f0)))
    if ar[i0] > thr:
        return None, None
    lo = f[0]
    for i in range(i0, 0, -1):
        if ar[i - 1] > thr:
            lo = np.interp(thr, [ar[i], ar[i - 1]], [f[i], f[i - 1]]); break
    hi = f[-1]
    for i in range(i0, len(f) - 1):
        if ar[i + 1] > thr:
            hi = np.interp(thr, [ar[i], ar[i + 1]], [f[i], f[i + 1]]); break
    return float(lo), float(hi)


def run_T(T: float) -> dict:
    """One FDTD with eps and dims scaled to temperature T; return CP-at-channel metrics."""
    dT  = T - T_REF
    eps = EPS0_R * (1 + TCDK * 1e-6 * dT)
    k   = 1 + CTE * 1e-6 * dT
    p   = PatchParams.from_dict({'W_mm': W0 * k, 'trunc_mm': TR0 * k, 'inset_y_mm': INS0 * k})

    config.substrate_epsR  = eps
    config.substrate_kappa = config.substrate_tanD * 2 * np.pi * F_TARGET * EPS0 * eps

    sp = tempfile.mkdtemp(prefix='thsw_')
    try:
        FDTD, _CSX, port, nf2ff = build_patch_sim(p, NrTS)
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))
        f_scan = np.linspace(F_TARGET - 50e6, F_TARGET + 50e6, 201)
        of = os.path.join(tempfile.gettempdir(), f'thsw_ar_{T:+.0f}.h5')
        res = nf2ff.CalcNF2FF(sp, list(f_scan), theta=[2.0], phi=[0., 90., 180., 270.],
                              center=[0, 0, 1e-3], outfile=of)
        ar = np.array([axial_ratio_db(res.E_cprh[n][0, :], res.E_cplh[n][0, :])[0]
                       for n in range(len(f_scan))])
        ar_s = np.convolve(ar, np.ones(3) / 3.0, mode='same'); ar_s[0], ar_s[-1] = ar[0], ar[-1]
        i = int(np.argmin(ar_s))
        f_null = float(f_scan[i]); ar_min = float(ar_s[i])
        ar_at_ft = float(np.interp(F_TARGET, f_scan, ar_s))
        _, rhcp = axial_ratio_db(res.E_cprh[i][0, :], res.E_cplh[i][0, :])
        lo, hi = _contiguous_band(f_scan, ar_s, F_TARGET)
        cp_chan = bool(lo is not None and lo <= CHAN_LO and hi >= CHAN_HI)
        ar_chan_hi = float(max(np.interp(CHAN_LO, f_scan, ar_s), np.interp(CHAN_HI, f_scan, ar_s)))
        port.CalcPort(sp, np.array([F_TARGET]))
        s11 = float(s11_db(port.uf_ref, port.uf_inc)[0])
        return dict(T_C=T, eps_r=round(eps, 4), ok=True,
                    f_null_MHz=round(f_null / 1e6, 2), ar_min_dB=round(ar_min, 2),
                    ar_at_ft_dB=round(ar_at_ft, 2), ar_worst_chan_dB=round(ar_chan_hi, 2),
                    cp_chan=cp_chan, s11_at_ft_dB=round(s11, 1), rhcp=bool(rhcp))
    except Exception as exc:
        return dict(T_C=T, ok=False, error=str(exc))
    finally:
        config.substrate_epsR = EPS0_R
        config.substrate_kappa = config.substrate_tanD * 2 * np.pi * F_TARGET * EPS0 * EPS0_R
        shutil.rmtree(sp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    temps = list(np.arange(T_MIN, T_MAX + 1e-6, T_STEP))
    print(f'THERMAL drift sweep  dims W={W0}/trunc={TR0}/inset={INS0}, eps0={EPS0_R}@{T_REF}C, '
          f'TCDk={TCDK} ppm/C, CTE={CTE} ppm/C, NrTS={NrTS}', flush=True)
    print(f'  !! TCDk/CTE are PLACEHOLDER FR-4 values — confirm NP-140F datasheet before trusting absolute MHz')
    print(f'  channel {CHAN_LO/1e6:.2f}-{CHAN_HI/1e6:.2f} MHz, T {T_MIN}..{T_MAX} C\n', flush=True)
    print(f'{"T(C)":>6} {"eps_r":>7} | {"f_null":>8} {"AR_min":>7} {"AR@f0":>6} '
          f'{"AR@chan":>8} {"S11":>6} {"RHCP":>5} {"CP@chan":>8}', flush=True)
    rows = []
    for T in temps:
        r = run_T(float(T))
        rows.append(r)
        json.dump(rows, open(OUT, 'w', encoding='utf-8'), indent=2)
        if r.get('ok'):
            print(f'{r["T_C"]:>6.1f} {r["eps_r"]:>7.4f} | {r["f_null_MHz"]:>8.2f} '
                  f'{r["ar_min_dB"]:>7.2f} {r["ar_at_ft_dB"]:>6.2f} {r["ar_worst_chan_dB"]:>8.2f} '
                  f'{r["s11_at_ft_dB"]:>5.1f} {"RHCP" if r["rhcp"] else "LHCP":>5} '
                  f'{"YES" if r["cp_chan"] else "** NO **":>8}', flush=True)
        else:
            print(f'{T:>6.1f} {"":>7} | FAILED: {r.get("error","")}', flush=True)

    ok = [r for r in rows if r.get('ok')]
    passing = [r for r in ok if r['cp_chan']]
    print(f'\nSUMMARY: CP holds across the channel at {len(passing)}/{len(ok)} temperatures.')
    if passing:
        print(f'  CP-in-channel temperature window: {min(p["T_C"] for p in passing):.0f} .. '
              f'{max(p["T_C"] for p in passing):.0f} C (of {T_MIN:.0f}..{T_MAX:.0f} swept)')
    print(f'  null walk: {min(r["f_null_MHz"] for r in ok):.2f} .. '
          f'{max(r["f_null_MHz"] for r in ok):.2f} MHz over the swept range.')
    print(f'  -> wider AR<=3 band (bigger truncation, the drift-margin sweep) widens this window.')
    print(f'  results -> {OUT}', flush=True)


if __name__ == '__main__':
    main()

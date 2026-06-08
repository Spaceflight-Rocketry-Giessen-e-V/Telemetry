# -*- coding: utf-8 -*-
"""Tool — εr / thickness ROBUSTNESS sweep of the locked patch (the #1 pre-fab de-risk).

The single-feed corner-truncated CP null is only ~7.5 MHz wide, but the laminate εr alone
shifts it ~±10 MHz per ±0.1 εr (f ∝ 1/√εr_eff) — WIDER than the band. This sweeps εr (and a
±0.1 mm thickness tolerance) at the FIXED design dims (W=82.5 / Δ=8.25 / inset=5.8, 160 mm)
and reports, per point, where the AR null lands, the AR AT f_target, whether AR≤3 holds across
the 869.4–869.65 MHz channel, and S11 — i.e. which boards still ship CP and which run linear.

It does NOT re-tune; it answers "across the real material spread, does this ONE board still
have CP at 869.525?". Run as a background job (~2 h at 150k × 7 points, single-sim all-cores).

    python tests/tool_eps_sweep.py
    EPS_SWEEP_NRTS=100000 python tests/tool_eps_sweep.py     # faster / coarser
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
from src.model import build_patch_sim   # reads config.substrate_* at CALL time, so runtime patch is fine

NrTS = int(os.environ.get('EPS_SWEEP_NRTS', str(config.NrTS_final)))

# Locked design dims (the deliverable), held FIXED while the material varies.
DESIGN = PatchParams.from_dict({'W_mm': 82.5, 'trunc_mm': 8.25, 'inset_y_mm': 5.8})

# (εr, thickness_mm). εr brackets NP-140F (4.0–4.2 datasheet, design 4.15) up to the
# KB-6164-class fallback (~4.6); the two off-nominal thicknesses are a ±0.1 mm fab tolerance.
POINTS = [(e, 1.6) for e in (4.00, 4.05, 4.15, 4.30, 4.60)] + [(4.15, 1.5), (4.15, 1.7)]

CHAN_LO, CHAN_HI = 869.4e6, 869.65e6   # EU 869 g3 high-power channel edges


def run_point(eps: float, h: float) -> dict:
    """Run one FDTD at fixed dims with patched εr/thickness; return CP/match metrics."""
    config.substrate_epsR      = eps
    config.substrate_thickness = h
    config.substrate_kappa     = config.substrate_tanD * 2 * np.pi * config.f_target * EPS0 * eps

    sp = tempfile.mkdtemp(prefix='epssw_')
    try:
        FDTD, _CSX, port, nf2ff = build_patch_sim(DESIGN, NrTS)
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))

        # AR vs frequency at the θ=2° near-axis ring (mean over φ — matches postproc/optimizer).
        f_scan = np.linspace(config.f_target - 60e6, config.f_target + 60e6, 121)  # 1 MHz/pt
        of = os.path.join(tempfile.gettempdir(), f'epssw_ar_{eps:.2f}_{h:.1f}.h5')
        res = nf2ff.CalcNF2FF(sp, list(f_scan), theta=[2.0], phi=[0., 90., 180., 270.],
                              center=[0, 0, 1e-3], outfile=of)
        ar = np.array([axial_ratio_db(res.E_cprh[n][0, :], res.E_cplh[n][0, :])[0]
                       for n in range(len(f_scan))])
        ar_s = np.convolve(ar, np.ones(3) / 3.0, mode='same'); ar_s[0], ar_s[-1] = ar[0], ar[-1]
        i = int(np.argmin(ar_s))
        f_null = float(f_scan[i]); ar_min = float(ar_s[i])
        ar_at_ft = float(np.interp(config.f_target, f_scan, ar_s))
        _, rhcp = axial_ratio_db(res.E_cprh[i][0, :], res.E_cplh[i][0, :])

        chan = (f_scan >= CHAN_LO) & (f_scan <= CHAN_HI)
        cp_ok = bool(chan.any() and np.all(ar_s[chan] <= 3.0))
        inb = f_scan[ar_s <= 3.0]
        band = float((inb.max() - inb.min()) / 1e6) if inb.size else 0.0

        port.CalcPort(sp, np.array([config.f_target]))
        s11 = float(s11_db(port.uf_ref, port.uf_inc)[0])
        return dict(eps=eps, h=h, f_null_MHz=round(f_null / 1e6, 2), ar_min_dB=round(ar_min, 2),
                    ar_at_ft_dB=round(ar_at_ft, 2), cp_ok=cp_ok, ar3_bw_MHz=round(band, 1),
                    s11_at_ft_dB=round(s11, 1), rhcp=bool(rhcp), ok=True)
    except Exception as exc:
        return dict(eps=eps, h=h, ok=False, error=str(exc))
    finally:
        shutil.rmtree(sp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f'eps/thickness robustness sweep  (dims W={DESIGN.W_mm}/trunc={DESIGN.trunc_mm}/'
          f'inset={DESIGN.inset_y_mm}, NrTS={NrTS}, f0={config.f_target/1e6:.3f} MHz, '
          f'channel {CHAN_LO/1e6:.2f}-{CHAN_HI/1e6:.2f})', flush=True)
    print(f'{"eps":>5} {"h":>4} | {"f_null":>8} {"AR_min":>7} {"AR@f0":>6} {"AR<=3 BW":>9} '
          f'{"S11@f0":>7} {"RHCP":>5} {"CP@chan?":>9}', flush=True)
    rows = []
    for eps, h in POINTS:
        r = run_point(eps, h)
        rows.append(r)
        if r.get('ok'):
            print(f'{eps:>5.2f} {h:>4.1f} | {r["f_null_MHz"]:>8.2f} {r["ar_min_dB"]:>7.2f} '
                  f'{r["ar_at_ft_dB"]:>6.2f} {r["ar3_bw_MHz"]:>8.1f}M {r["s11_at_ft_dB"]:>6.1f}dB '
                  f'{"RHCP" if r["rhcp"] else "LHCP":>5} {"YES" if r["cp_ok"] else "** NO **":>9}',
                  flush=True)
        else:
            print(f'{eps:>5.2f} {h:>4.1f} | FAILED: {r.get("error","")}', flush=True)

    ok = [r for r in rows if r.get('ok')]
    npass = sum(1 for r in ok if r['cp_ok'])
    print(f'\nSUMMARY: {npass}/{len(ok)} points keep AR<=3 across the whole 869.4-869.65 channel.')
    nominal = next((r for r in ok if r['eps'] == 4.15 and r['h'] == 1.6), None)
    if nominal:
        print(f'  nominal (eps 4.15, h 1.6): null {nominal["f_null_MHz"]} MHz, '
              f'AR@f0 {nominal["ar_at_ft_dB"]} dB, CP@chan={nominal["cp_ok"]}')
    print('  -> If only the nominal point passes, per-unit cold-AR tuning is mandatory (the '
          'CP\n     null moves out of the channel across the real material spread).')

    out = os.path.join(os.getcwd(), 'eps_sweep_results.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)
    print(f'  results -> {out}')


if __name__ == '__main__':
    main()

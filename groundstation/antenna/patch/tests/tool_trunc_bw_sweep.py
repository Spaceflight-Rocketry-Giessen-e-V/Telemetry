# -*- coding: utf-8 -*-
"""Tool — (W x corner-truncation) DRIFT-MARGIN sweep on the locked 1.6 mm board.

The single-feed corner-truncated CP null is only ~7.5 MHz wide, but the laminate eps
(and thermal TCDk) slide it ~+-10 MHz per +-0.1 eps. The deliverable trunc came from the
0.10*W seed, NOT from any frequency-bandwidth optimum, and the optimiser only rewards the
spatial AR<=3 BEAMWIDTH (W_AR_BW), never the AR<=3 FREQUENCY bandwidth. So this sweeps the
two coupled resonance/CP levers - patch side W and corner truncation Delta - at the NOMINAL
material (eps 4.15, h 1.6 mm, fixed inset), and scores each design by its DRIFT MARGIN:

    contiguous AR<=3 band [band_lo, band_hi] that contains f_target, then
    margin_lo = CHAN_LO - band_lo   (MHz the band extends BELOW the channel)
    margin_hi = band_hi  - CHAN_HI  (MHz the band extends ABOVE the channel)
    drift_margin = min(margin_lo, margin_hi)        (the tighter side)

Because eps drift just shifts the whole AR-vs-f curve (f ~ 1/sqrt(eps_eff)), drift_margin in
MHz maps directly to an eps tolerance (~0.01 eps per MHz). MAXIMISING drift_margin = the most
eps/thermal-tolerant 1.6 mm CP design = exactly the fragility lever. A wider, flatter band
(bigger Delta, shallower null) that stays centred on the channel beats a deep but narrow null.

It does NOT compute realised gain (cheap theta=2 deg AR + S11 only, like tool_eps_sweep) -
the winner is re-run at full fidelity for gain / RHCP / honest AR. Background job (~17-27
min/point at 150k, single-sim all-cores).

    python tests/tool_trunc_bw_sweep.py
    TRUNC_SWEEP_NRTS=100000 python tests/tool_trunc_bw_sweep.py   # faster / coarser
    TRUNC_SWEEP_W=82.5,82.8 TRUNC_SWEEP_TR=8.25,10.5 python tests/tool_trunc_bw_sweep.py
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import json
import os
import shutil
import sys
import tempfile

import numpy as np

import config
from src.params import PatchParams
from src.metrics import axial_ratio_db, s11_db
from src.model import build_patch_sim

NrTS = int(os.environ.get('TRUNC_SWEEP_NRTS', str(config.NrTS_final)))

# Nominal material — LOCKED 1.6 mm NP-140F (no eps/thickness variation here; this sweep is
# about the GEOMETRY that best survives the eps drift the eps-sweep already characterised).
INSET = 5.8                                 # fixed 50 ohm inset (sets match, not resonance/AR)

# Grid of the two coupled levers. W centres the AR null (resonance); Delta sets the CP mode
# split (wider Delta -> wider but shallower AR band). Bigger Delta raises the null (less
# copper), bigger W lowers it - so the 2-D grid lets W re-centre each Delta on the channel.
def _floats(env, default):
    v = os.environ.get(env)
    return [float(x) for x in v.split(',')] if v else default

W_GRID  = _floats('TRUNC_SWEEP_W',  [82.2, 82.5, 82.8])
TR_GRID = _floats('TRUNC_SWEEP_TR', [8.25, 10.5, 12.75])

CHAN_LO, CHAN_HI = 869.4e6, 869.65e6        # EU 869 g3 high-power channel edges
F_TARGET = config.f_target
BASE_W, BASE_TR = 82.5, 8.25                 # the current deliverable (reference row)

OUT = os.path.join(os.getcwd(), 'trunc_bw_sweep_results.json')


def _contiguous_band(f, ar, f0, thr=3.0):
    """[lo, hi] (Hz) of the contiguous AR<=thr band that CONTAINS f0, edges linearly
    interpolated at the thr crossing. Returns (None, None) if AR(f0) already exceeds thr."""
    i0 = int(np.argmin(np.abs(f - f0)))
    if ar[i0] > thr:
        return None, None
    # walk down
    lo = f[0]
    for i in range(i0, 0, -1):
        if ar[i - 1] > thr:
            lo = np.interp(thr, [ar[i], ar[i - 1]], [f[i], f[i - 1]])
            break
    # walk up
    hi = f[-1]
    for i in range(i0, len(f) - 1):
        if ar[i + 1] > thr:
            hi = np.interp(thr, [ar[i], ar[i + 1]], [f[i], f[i + 1]])
            break
    return float(lo), float(hi)


def run_point(W: float, tr: float) -> dict:
    """One FDTD at (W, trunc) with nominal material; return CP-band / drift-margin metrics."""
    p = PatchParams.from_dict({'W_mm': W, 'trunc_mm': tr, 'inset_y_mm': INSET})
    sp = tempfile.mkdtemp(prefix='trsw_')
    try:
        FDTD, _CSX, port, nf2ff = build_patch_sim(p, NrTS)
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))

        # AR vs frequency at the theta=2 deg near-axis ring (mean over phi — matches
        # postproc/optimizer/eps-sweep). Fine 0.5 MHz grid over +-50 MHz for clean band edges.
        f_scan = np.linspace(F_TARGET - 50e6, F_TARGET + 50e6, 201)
        of = os.path.join(tempfile.gettempdir(), f'trsw_ar_{W:.2f}_{tr:.2f}.h5')
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
        if lo is None:
            band = m_lo = m_hi = drift = 0.0
            cp_chan = False
        else:
            band  = (hi - lo) / 1e6
            m_lo  = (CHAN_LO - lo) / 1e6        # band extends this far BELOW channel low edge
            m_hi  = (hi - CHAN_HI) / 1e6        # band extends this far ABOVE channel high edge
            drift = min(m_lo, m_hi)             # tighter side = symmetric drift tolerance
            cp_chan = bool(lo <= CHAN_LO and hi >= CHAN_HI)

        port.CalcPort(sp, np.array([F_TARGET]))
        s11 = float(s11_db(port.uf_ref, port.uf_inc)[0])
        return dict(W=W, trunc=tr, inset=INSET, ok=True,
                    f_null_MHz=round(f_null / 1e6, 2), ar_min_dB=round(ar_min, 2),
                    ar_at_ft_dB=round(ar_at_ft, 2), ar3_bw_MHz=round(band, 1),
                    band_lo_MHz=round(lo / 1e6, 2) if lo else None,
                    band_hi_MHz=round(hi / 1e6, 2) if hi else None,
                    margin_lo_MHz=round(m_lo, 2), margin_hi_MHz=round(m_hi, 2),
                    drift_margin_MHz=round(drift, 2), eps_margin=round(drift / 100.0, 3),
                    cp_chan=cp_chan, s11_at_ft_dB=round(s11, 1), rhcp=bool(rhcp))
    except Exception as exc:
        return dict(W=W, trunc=tr, ok=False, error=str(exc))
    finally:
        shutil.rmtree(sp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    pts = [(W, tr) for W in W_GRID for tr in TR_GRID]
    print(f'(W x trunc) drift-margin sweep  (inset={INSET}, eps={config.substrate_epsR}, '
          f'h={config.substrate_thickness}, NrTS={NrTS}, f0={F_TARGET/1e6:.3f} MHz, '
          f'channel {CHAN_LO/1e6:.2f}-{CHAN_HI/1e6:.2f}, {len(pts)} points)', flush=True)
    print(f'  ranking metric = drift_margin = min(band beyond channel lo, band beyond channel hi)\n')
    print(f'{"W":>6} {"tr":>6} | {"f_null":>8} {"AR_min":>7} {"AR@f0":>6} {"AR<=3 BW":>9} '
          f'{"band":>13} {"m_lo":>6} {"m_hi":>6} {"DRIFT":>6} {"S11":>6} {"RHCP":>5} {"CP@ch":>6}',
          flush=True)
    rows = []
    for W, tr in pts:
        r = run_point(W, tr)
        rows.append(r)
        json.dump(rows, open(OUT, 'w', encoding='utf-8'), indent=2)   # incremental save
        if r.get('ok'):
            tag = '  <== BASELINE' if (abs(W - BASE_W) < 1e-6 and abs(tr - BASE_TR) < 1e-6) else ''
            print(f'{W:>6.2f} {tr:>6.2f} | {r["f_null_MHz"]:>8.2f} {r["ar_min_dB"]:>7.2f} '
                  f'{r["ar_at_ft_dB"]:>6.2f} {r["ar3_bw_MHz"]:>7.1f}M '
                  f'{str(r["band_lo_MHz"])+"-"+str(r["band_hi_MHz"]):>13} '
                  f'{r["margin_lo_MHz"]:>6.2f} {r["margin_hi_MHz"]:>6.2f} '
                  f'{r["drift_margin_MHz"]:>6.2f} {r["s11_at_ft_dB"]:>5.1f} '
                  f'{"RHCP" if r["rhcp"] else "LHCP":>5} {"YES" if r["cp_chan"] else "no":>6}{tag}',
                  flush=True)
        else:
            print(f'{W:>6.2f} {tr:>6.2f} | FAILED: {r.get("error","")}', flush=True)

    ok = [r for r in rows if r.get('ok')]
    cands = [r for r in ok if r['rhcp'] and r['ar_at_ft_dB'] <= 3.0]
    cands.sort(key=lambda r: (-r['drift_margin_MHz'], r['ar_at_ft_dB']))
    base = next((r for r in ok if abs(r['W'] - BASE_W) < 1e-6 and abs(r['trunc'] - BASE_TR) < 1e-6),
                None)
    print('\n=== RANKED by drift margin (RHCP & AR@f0<=3 only) ===')
    for r in cands[:6]:
        print(f'  W={r["W"]:.2f} tr={r["trunc"]:.2f}: drift {r["drift_margin_MHz"]:+.2f} MHz '
              f'(~{r["eps_margin"]:+.3f} eps), AR@f0 {r["ar_at_ft_dB"]:.2f} dB, '
              f'band {r["ar3_bw_MHz"]:.1f} MHz, S11 {r["s11_at_ft_dB"]:.1f} dB')
    if base:
        print(f'\n  BASELINE W=82.5 tr=8.25: drift {base["drift_margin_MHz"]:+.2f} MHz, '
              f'AR@f0 {base["ar_at_ft_dB"]:.2f} dB, band {base["ar3_bw_MHz"]:.1f} MHz')
        if cands:
            w = cands[0]
            d = w['drift_margin_MHz'] - base['drift_margin_MHz']
            print(f'  WINNER vs baseline: drift {d:+.2f} MHz  '
                  f'({"IMPROVEMENT" if d > 0.3 else "no meaningful gain — keep baseline"})')
    print(f'\n  results -> {OUT}', flush=True)


if __name__ == '__main__':
    main()

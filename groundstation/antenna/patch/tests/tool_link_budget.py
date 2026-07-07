# -*- coding: utf-8 -*-
"""Tool — downlink budget check for the ground PATCH vs its REALISED gain (no FDTD).

Single-feed corner-truncated patch (current design, results.json): REALISED gain
**+0.84 dBic boresight**, **≈ −2.0 dBic at the 45° cone edge** (directivity 6.60 dBi ×
η_tot 26.5 %; the cone-edge directivity 3.79 dBic − 5.77 dB). This is the WIDE-BEAM BACKUP
behind the separately-tracked 16.5 dBi helical — the helical's own budget is the 869 row of
docs/linkbudget.ipynb (G_RX 16.5 → 18.4 km @ 30 dB). Polarisation is matched RHCP↔RHCP
(0 dB), BUT the patch CP null is narrow/drift-sensitive, so a fab/εr CP failure (AR>3 →
near-linear) costing ~3 dB is a real backup-failure mode — pass --pol 3 to stack it.

Defaults MATCH linkbudget.ipynb so the two artefacts agree (the notebook is the single
source of truth for the radio params): P_TX 27 dBm, G_TX −5 dBic (QFH worst-angle estimate),
L_TX+L_RX = 6 dB, P_RX −114 dBm (min; −118 dBm typ → +4 dB). Override on the CLI for other
mission numbers. (Was previously the RETIRED dual-feed coupler at η_rad ~3 % / −9.6 dBic.)

    python tests/tool_link_budget.py
    python tests/tool_link_budget.py --grx -2.0 --range_km 18.4 --pol 3   # worst-ish backup case
    python tests/tool_link_budget.py --sens -118                          # typ sensitivity (+4 dB)
"""

import _bootstrap  # noqa: F401  — project root on sys.path (keep first; no openEMS needed)

import argparse
import math

import config


def fspl_db(d_m: float, f_hz: float) -> float:
    """Free-space path loss [dB] = 20·log10(4π d / λ)."""
    lam = config.C0 / f_hz
    return 20.0 * math.log10(4.0 * math.pi * d_m / lam)


def budget(ptx_dbm, gtx, grx, range_km, sens_dbm, misc_db, pol_db, f_hz, erp_capped):
    # EU e.r.p. cap: if the 27 dBm limit is INCLUSIVE of TX-antenna gain, radiated EIRP is
    # capped at ptx (gtx already "spent"); else EIRP = ptx + gtx (the notebook's convention).
    eirp = ptx_dbm if erp_capped else ptx_dbm + gtx
    L = fspl_db(range_km * 1e3, f_hz)
    prx = eirp - L + grx - misc_db - pol_db
    return dict(eirp=eirp, fspl=L, prx=prx, margin=prx - sens_dbm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ptx', type=float, default=27.0, help='TX power dBm (notebook: 27)')
    ap.add_argument('--gtx', type=float, default=-5.0, help='rocket QFH gain dBic (notebook: -5, worst-angle)')
    ap.add_argument('--grx', type=float, default=None, help='patch REALISED gain dBic (default: scenarios)')
    ap.add_argument('--range_km', type=float, default=10.0)
    ap.add_argument('--sens', type=float, default=-114.0, help='RX sensitivity dBm (notebook: -114 min, -118 typ)')
    ap.add_argument('--misc', type=float, default=6.0, help='L_TX+L_RX dB (notebook: 3+3)')
    ap.add_argument('--pol', type=float, default=0.0, help='polarisation loss dB (0 matched; ~3 if CP fails to linear)')
    ap.add_argument('--erp_capped', action='store_true',
                    help='treat --ptx as total e.r.p. INCLUDING gtx (EU cap)')
    a = ap.parse_args()
    f = config.f_target

    print(f'Downlink budget @ {f/1e6:.1f} MHz, {a.range_km:.1f} km   '
          f'(Ptx={a.ptx} dBm, Gtx={a.gtx} dBic, sens={a.sens} dBm, '
          f'L_TX+L_RX={a.misc} dB, pol={a.pol} dB, erp_capped={a.erp_capped})')
    print(f'  FSPL({a.range_km:.1f} km) = {fspl_db(a.range_km*1e3, f):.1f} dB   '
          f'(notebook helical: 18.4 km @ 30 dB with G_RX 16.5)')
    print(f'{"scenario":>40} {"Grx dBic":>9} {"Prx dBm":>9} {"margin dB":>10}')

    if a.grx is not None:
        scenarios = [(f'custom Grx={a.grx:+.1f}', a.grx)]
    else:
        scenarios = [
            ('patch boresight  realised +0.84',   0.84),
            ('patch 45deg cone-edge  realised -2.0', -2.0),
            ('helical (PRIMARY, reference)',       16.5),
        ]
    for name, grx in scenarios:
        b = budget(a.ptx, a.gtx, grx, a.range_km, a.sens, a.misc, a.pol, f, a.erp_capped)
        # tiers per linkbudget.ipynb: >30 reliable target, >20 reliable, >10 floor, else marginal/fail
        flag = ('RELIABLE(>30)' if b['margin'] > 30 else 'reliable(>20)' if b['margin'] > 20
                else 'CLOSES(>10)' if b['margin'] > 10 else 'marginal' if b['margin'] > 0 else 'FAILS')
        print(f'{name:>40} {grx:>+9.1f} {b["prx"]:>9.1f} {b["margin"]:>+9.1f}  {flag}')
    print('\n  Patch is the wide-beam BACKUP: it clears the 10 dB floor across the helical\'s '
          '18.4 km range\n  (~14 dB boresight / ~11 dB cone-edge @ 18.4 km) but does NOT meet the '
          '30 dB target the\n  helical does - expected for a backup. Stack --pol 3 (CP->linear) for '
          'the worst case.')


if __name__ == '__main__':
    main()

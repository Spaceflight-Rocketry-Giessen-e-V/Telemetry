# -*- coding: utf-8 -*-
"""Tool — downlink budget check for the ground patch vs its REALISED gain (no FDTD).

WIP parked item: the "~20-30 dB margin" was figured assuming the patch delivered its
~4 dBic directivity. The dipole-validated efficiency shows the as-built design radiates
only η_rad ≈ 3 %, so its REALISED gain is ≈ -9.6 dBic boresight (directivity 5.9 dBi +
10·log10(η_tot)). This recomputes the 10 km downlink margin at the realised gain so we
can confirm the link still closes — and quantify how much margin a feed-match re-tune
would recover.

NOTE: this repo carries NO numeric link budget, so the TX power / TX-antenna gain /
RX sensitivity / misc-loss below are STATED ASSUMPTIONS (EU 869.4-869.65 g3 high-power
sub-band: 500 mW = 27 dBm e.r.p.; RC1780HP/RC232 class RX). Override them on the command
line to match the real mission numbers. Polarisation loss = 0 (matched RHCP↔RHCP).

    python tests/tool_link_budget.py
    python tests/tool_link_budget.py --grx -9.6 --range_km 10 --sens -110 --ptx 27
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
    # EU e.r.p. cap: if the 27 dBm limit is INCLUSIVE of TX-antenna gain, the radiated
    # EIRP is capped at ptx (gtx already "spent"); else EIRP = ptx + gtx.
    eirp = ptx_dbm if erp_capped else ptx_dbm + gtx
    L = fspl_db(range_km * 1e3, f_hz)
    prx = eirp - L + grx - misc_db - pol_db
    return dict(eirp=eirp, fspl=L, prx=prx, margin=prx - sens_dbm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ptx', type=float, default=27.0, help='TX power dBm (500 mW e.r.p. = 27)')
    ap.add_argument('--gtx', type=float, default=2.0, help='rocket QFH RHCP gain dBic')
    ap.add_argument('--grx', type=float, default=None, help='patch REALISED gain dBic (default: scenarios)')
    ap.add_argument('--range_km', type=float, default=10.0)
    ap.add_argument('--sens', type=float, default=-110.0, help='RX sensitivity dBm')
    ap.add_argument('--misc', type=float, default=2.0, help='cable/connector/impl loss dB')
    ap.add_argument('--pol', type=float, default=0.0, help='polarisation loss dB (0 = matched RHCP)')
    ap.add_argument('--erp_capped', action='store_true',
                    help='treat --ptx as total e.r.p. INCLUDING gtx (EU cap)')
    a = ap.parse_args()
    f = config.f_target

    print(f'Downlink budget @ {f/1e6:.1f} MHz, {a.range_km:.0f} km   '
          f'(ASSUMED: Ptx={a.ptx} dBm, Gtx={a.gtx} dBic, sens={a.sens} dBm, '
          f'misc={a.misc} dB, pol={a.pol} dB, erp_capped={a.erp_capped})')
    print(f'  FSPL({a.range_km:.0f} km) = {fspl_db(a.range_km*1e3, f):.1f} dB')
    print(f'{"scenario":>34} {"Grx dBic":>9} {"Prx dBm":>9} {"margin dB":>10}')

    if a.grx is not None:
        scenarios = [(f'custom Grx={a.grx:+.1f}', a.grx)]
    else:
        scenarios = [
            ('OLD assumption (~directivity 4 dBic)',  4.0),
            ('AS-BUILT realised boresight (-9.6)',    -9.6),
            ('AS-BUILT realised cone-edge (-13.5)',   -13.5),
            ('re-tuned target (~+2 dBic realised)',    2.0),
        ]
    for name, grx in scenarios:
        b = budget(a.ptx, a.gtx, grx, a.range_km, a.sens, a.misc, a.pol, f, a.erp_capped)
        flag = 'CLOSES' if b['margin'] > 10 else ('marginal' if b['margin'] > 0 else 'FAILS')
        print(f'{name:>34} {grx:>+9.1f} {b["prx"]:>9.1f} {b["margin"]:>+9.1f}  {flag}')
    print('\n  Even the as-built -9.6 dBic closes 10 km on the assumed budget (the original '
          '~30 dB\n  margin absorbs the ~13 dB realised-gain deficit), but a feed-match '
          're-tune recovers it.')


if __name__ == '__main__':
    main()

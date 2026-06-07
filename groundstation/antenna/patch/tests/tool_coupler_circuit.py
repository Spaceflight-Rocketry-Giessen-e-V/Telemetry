# -*- coding: utf-8 -*-
"""Tool — fast circuit-model tuner for the branch-line coupler (no FDTD).

Models the four ring arms as LOSSY microstrip transmission lines (Hammerstad
eps_eff + dielectric loss on FR-4) and assembles the 4-port S-matrix, so the arm
length can be tuned for best match + isolation in milliseconds instead of via
slow FDTD. It also reports the REALISTIC lossy output balance / isolation, which
sets the axial-ratio ceiling the coupler can deliver on lossy FR-4.

Node order [BL, BR, TL, TR]. Arms (match geometry.branch_line_rects with
w_h=CPL_W50 horizontal=50 ohm, w_v=CPL_W35 vertical=35.36 ohm):
  bottom BL-BR = 50 ohm, top TL-TR = 50 ohm (horizontal)
  left  BL-TL = 35.36 ohm, right BR-TR = 35.36 ohm (vertical)
Input = BL. Locked topology: outputs TL & TR, isolated BR.

    python tests/tool_coupler_circuit.py
"""

import _bootstrap  # noqa: F401  — project root on sys.path (keep first; no openEMS needed here)

import numpy as np

import config

C0 = 2.99792458e8
ER = config.substrate_epsR
H  = config.substrate_thickness * 1e-3      # m
TD = config.substrate_tanD
F0 = config.f_target


def eps_eff(w_mm):
    """Hammerstad effective permittivity for a microstrip of width w (W/h > 1)."""
    wh = (w_mm * 1e-3) / H
    return (ER + 1) / 2 + (ER - 1) / 2 * (1 + 12 / wh) ** -0.5


def gamma(w_mm, f):
    """Complex propagation constant gamma = alpha_d + j*beta for a microstrip line."""
    ee = eps_eff(w_mm)
    k0 = 2 * np.pi * f / C0
    beta = k0 * np.sqrt(ee)
    alpha_d = k0 * ER * (ee - 1) * TD / (2 * np.sqrt(ee) * (ER - 1))   # Np/m, dielectric
    return alpha_d + 1j * beta


def arm_Y(w_mm, Zc, L_mm, f):
    """2x2 Y-matrix entries (y11=y22, y12=y21) of a lossy TL arm."""
    th = gamma(w_mm, f) * (L_mm * 1e-3)
    y11 = np.cosh(th) / (Zc * np.sinh(th))
    y12 = -1.0 / (Zc * np.sinh(th))
    return y11, y12


def sparams(L_mm, f, w50=config.CPL_W50, w35=config.CPL_W35):
    """4-port S-matrix (50 ohm ref) of the branch-line ring at length L_mm, freq f."""
    Y0 = 1 / 50.0
    Y = np.zeros((4, 4), complex)
    # (node_i, node_j, width, Zc)
    arms = [(0, 1, w50, 50.0),       # bottom BL-BR (50)
            (2, 3, w50, 50.0),       # top    TL-TR (50)
            (0, 2, w35, 35.36),      # left   BL-TL (35.36)
            (1, 3, w35, 35.36)]      # right  BR-TR (35.36)
    for i, j, w, Zc in arms:
        y11, y12 = arm_Y(w, Zc, L_mm, f)
        Y[i, i] += y11; Y[j, j] += y11
        Y[i, j] += y12; Y[j, i] += y12
    I = np.eye(4)
    return (Y0 * I - Y) @ np.linalg.inv(Y0 * I + Y)


def report(L_mm, f=F0):
    S = sparams(L_mm, f)
    db = lambda s: 20 * np.log10(abs(s) + 1e-30)
    ph = lambda s: np.degrees(np.angle(s))
    s11, sBR, sTL, sTR = S[0, 0], S[1, 0], S[2, 0], S[3, 0]
    dphi = (ph(sTL) - ph(sTR) + 180) % 360 - 180
    bal = db(sTL) - db(sTR)
    return dict(L=L_mm, s11=db(s11), iso=db(sBR), tl=db(sTL), tr=db(sTR),
                dphi=dphi, bal=bal)


def main():
    print(f'Branch-line coupler circuit model  (FR-4 eps_r={ER} tand={TD} h={H*1e3:.1f}mm, '
          f'f0={F0/1e6:.2f} MHz)')
    print(f'  eps_eff: 50ohm(w={config.CPL_W50})={eps_eff(config.CPL_W50):.3f}  '
          f'35ohm(w={config.CPL_W35})={eps_eff(config.CPL_W35):.3f}')
    lam_g50 = C0 / (F0 * np.sqrt(eps_eff(config.CPL_W50))) * 1e3
    lam_g35 = C0 / (F0 * np.sqrt(eps_eff(config.CPL_W35))) * 1e3
    print(f'  lambda_g/4: 50ohm={lam_g50/4:.2f}mm  35ohm={lam_g35/4:.2f}mm  '
          f'(single-ring compromise ~{(lam_g50/4+lam_g35/4)/2:.2f}mm)')

    # sweep arm length, score = best (deepest) max(|S11|,|iso|) at f0
    best, bestscore = None, 1e9
    print(f'\n{"arm mm":>7} {"S11 dB":>8} {"iso dB":>8} {"TL dB":>7} {"TR dB":>7} '
          f'{"bal dB":>7} {"dphi":>7}')
    for L in np.arange(44.0, 50.01, 0.5):
        r = report(L)
        score = max(r['s11'], r['iso'])      # want both deep (negative)
        if score < bestscore:
            bestscore, best = score, r
        print(f'{L:>7.1f} {r["s11"]:>8.1f} {r["iso"]:>8.1f} {r["tl"]:>7.2f} '
              f'{r["tr"]:>7.2f} {r["bal"]:>7.2f} {r["dphi"]:>7.1f}')
    print(f'\nBEST arm length ~ {best["L"]:.1f} mm:  S11={best["s11"]:.1f} dB  '
          f'isolation={best["iso"]:.1f} dB  outputs {best["tl"]:.2f}/{best["tr"]:.2f} dB  '
          f'balance={best["bal"]:.2f} dB  phase diff={best["dphi"]:.1f} deg')
    print('  -> output imbalance + phase error set the achievable axial ratio; '
          'feed both edges equal-length and tune arm to keep balance tight.')


if __name__ == '__main__':
    main()

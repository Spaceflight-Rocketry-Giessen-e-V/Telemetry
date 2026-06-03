# -*- coding: utf-8 -*-
"""Shared pure-numeric helpers for S-parameter, axial-ratio, and frequency math.

No FDTD / openEMS calls live here — only array math on results that openEMS has
already produced.  Both the optimizer worker (in a spawned child process) and the
post-processor import from this module so the metric definitions stay in one place
and the optimiser selects on exactly the quantities the final run reports.
"""

import numpy as np

import config


def cp_center_freq(f_arr, s11_dB_arr, threshold_dB=-10.0):
    """CP operating frequency as the -S11-weighted centroid of the matched bandwidth.

    Works for both single-mode patches (centroid ≈ argmin) and split-mode CP
    patches (centroid ≈ midpoint of the two modes).  Robust at coarse frequency
    grids where individual mode minima may not resolve as distinct local minima.
    Falls back to argmin when nothing is below threshold.
    """
    mask = s11_dB_arr < threshold_dB
    if not mask.any():
        return float(f_arr[np.argmin(s11_dB_arr)])
    weights = -s11_dB_arr[mask]  # positive; deeper S11 → higher weight
    return float(np.average(f_arr[mask], weights=weights))


def axial_ratio_db(E_rhcp, E_lhcp):
    """True axial ratio [dB, ≥0] and handedness from circular field components.

    E_rhcp / E_lhcp: complex RHCP / LHCP field samples over a small boresight
    cone (openEMS res.E_cprh / res.E_cplh).  Reduced to scalar magnitudes by
    averaging, then combined with the rigorous polarisation-ellipse formula

        AR = (R + L) / |R − L|        (linear, ≥1)
        AR_dB = 20·log10(AR)          (0 dB = perfect circular)

    This is NOT the same as 20·log10(L/R) (the cross-pol ratio): an AR of 3 dB
    corresponds to a cross-pol ratio of only ≈ −15 dB, so optimising the ratio
    with a −3 dB threshold accepts essentially linear polarisation.

    Returns (ar_dB, is_rhcp) where is_rhcp is True when RHCP dominates.
    """
    R = float(np.mean(np.abs(E_rhcp)))
    L = float(np.mean(np.abs(E_lhcp)))
    ar = (R + L) / (abs(R - L) + 1e-30)
    return 20.0 * np.log10(ar), (R >= L)


def s11_db(uf_ref, uf_inc):
    """|S11| in dB from a port's reflected / incident voltage phasors.

    Accepts scalars or arrays; returns the same shape.  The 1e-30 floor keeps
    log10 finite at a perfect match.
    """
    return 20.0 * np.log10(np.abs(uf_ref / uf_inc) + 1e-30)


def freq_eval_grid():
    """Frequency grid for the optimiser's per-candidate S11 / NF2FF evaluation.

    Index 0 is exactly f_target (so callers can read S11 at the design frequency
    directly); the remaining points span the full Gaussian excitation band
    f_target ± fc — the same band the post-processor sweeps — so the optimiser
    scores resonance over the band the final run will confirm.
    """
    return np.concatenate([
        [config.f_target],
        np.linspace(max(100e6, config.f_target - config.fc),
                    config.f_target + config.fc, 25)
    ])


def failure_result():
    """Sentinel result dict for a simulation that failed to produce metrics.

    Costed as strongly infeasible (AR 99 dB, gain -99 dBi) so a failed sim is
    never selected, while keeping the same keys a successful result carries.
    """
    return {'s11_dB': 0.0, 'f_res': config.f_target, 'ar_dB': 99.0,
            'Dmax': -99.0, 'rhcp': True,
            'zin_re': 0.0, 'zin_im': 0.0, 'ok': False}

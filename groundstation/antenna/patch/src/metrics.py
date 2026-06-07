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


def directivity_dbi(dmax_linear):
    """Convert openEMS ``nf2ff.Dmax`` (LINEAR directivity ratio) to dBi.

    openEMS returns Dmax = 4·π·U_max / P_rad — a dimensionless ratio ≥ 1 (1 =
    isotropic), NOT decibels. Directivity in dBi is 10·log10(Dmax). Reporting the
    raw ratio AS dBi under-reads directivity by exactly this log (e.g. a linear
    3.89 is 5.90 dBi, not "3.9 dBi"). Validated against a lossless half-wave dipole:
    openEMS Dmax = 1.656 → 2.19 dBi, matching the textbook 2.15 dBi. Accepts a
    scalar or array; the 1e-30 floor keeps log10 finite.
    """
    return 10.0 * np.log10(np.asarray(dmax_linear, dtype=float) + 1e-30)


def radiation_efficiency(P_rad, P_acc):
    """η_rad = radiated / ACCEPTED power (excludes feed mismatch). 0..1.

    ``P_rad`` is the openEMS NF2FF total radiated power (integrate the far field
    over a full sphere); ``P_acc`` is the port accepted power 0.5·Re(V·I*). Both
    are dipole-validated (a lossless dipole gives η_rad ≈ 1.00). η_rad captures the
    dielectric (and any conductor) loss plus the fraction of accepted power lost to
    a feed mismatch, so it can fall below 1 even when S11 is good. Realised gain (dBi)
    = directivity_dbi(Dmax) + 10·log10(η_tot), with η_tot = P_rad / P_inc.
    """
    return np.asarray(P_rad, dtype=float) / (np.asarray(P_acc, dtype=float) + 1e-30)


def failure_result():
    """Sentinel result dict for a simulation that failed to produce metrics.

    Costed as strongly infeasible (AR 99 dB, gain -99 dBi) so a failed sim is
    never selected, while keeping the same keys a successful result carries.
    """
    return {'s11_dB': 0.0, 'f_res': config.f_target, 'ar_dB': 99.0,
            'Dmax': -99.0, 'rhcp': True,
            'zin_re': 0.0, 'zin_im': 0.0, 'ok': False}


# ── Coverage metrics (wide-beam single-feed design) ───────────────────────────
# The backup patch is judged on AR / gain held over an elevation CONE, not at
# boresight. These reduce an AR(theta) / gain(theta) elevation cut to the three
# scalars the coverage cost uses. Pass the WORST AR over phi (and MIN gain over
# phi) at each theta so the metric reflects the worst azimuth cut, not an average.

def ar_beamwidth_deg(theta_deg, ar_db, ar_max_db=None):
    """AR <= ar_max FULL beamwidth [deg] from a boresight-outward AR(theta) cut.

    `theta_deg` increases from ~0. Returns 2 * theta_edge, where theta_edge is the
    largest angle for which AR stays <= ar_max over the whole contiguous interval
    [0, theta_edge] from boresight (so a good null at boresight that breaks up at
    wide angles is measured honestly). 0 if AR already exceeds ar_max on-axis.
    """
    if ar_max_db is None:
        ar_max_db = config.AR_MAX_DB
    theta = np.asarray(theta_deg, dtype=float)
    ar    = np.asarray(ar_db, dtype=float)
    order = np.argsort(theta)
    theta, ar = theta[order], ar[order]
    edge = 0.0
    for t, a in zip(theta, ar):
        if a <= ar_max_db:
            edge = float(t)
        else:
            break
    return 2.0 * edge


def worst_ar_over_cone(theta_deg, ar_db, cone_half_deg):
    """Max (worst) axial ratio [dB] over theta in [0, cone_half_deg]."""
    theta = np.asarray(theta_deg, dtype=float)
    ar    = np.asarray(ar_db, dtype=float)
    m = theta <= cone_half_deg + 1e-9
    return float(np.max(ar[m])) if m.any() else float(np.max(ar))


def min_gain_over_cone(theta_deg, gain_dbic, cone_half_deg):
    """Min RHCP gain [dBic] over theta in [0, cone_half_deg]."""
    theta = np.asarray(theta_deg, dtype=float)
    g     = np.asarray(gain_dbic, dtype=float)
    m = theta <= cone_half_deg + 1e-9
    return float(np.min(g[m])) if m.any() else float(np.min(g))

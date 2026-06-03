# -*- coding: utf-8 -*-
"""
Simulation constants for the RHCP patch antenna.

All physical parameters and derived mesh/sim settings live here.
No switches, no side effects — safe to import from any module.
"""

import numpy as np
from openEMS.physical_constants import C0, EPS0

# ── Antenna target ────────────────────────────────────────────────
f_target = 869.52e6   # Hz — operating frequency
fc       = 250e6      # Hz — Gaussian excitation half-bandwidth / post-proc sweep half-width
feed_R   = 50         # Ω  — lumped port impedance

# ── Substrate: Nan Ya NP-140F ─────────────────────────────────────
substrate_epsR      = 4.1    # relative permittivity @ 1 GHz (datasheet: 4.0–4.2)
substrate_tanD      = 0.013  # loss tangent @ 1 GHz (datasheet: 0.012–0.014)
substrate_thickness = 1.6    # mm
substrate_cells     = 4      # FDTD cells through substrate thickness

# ── FDTD domain ───────────────────────────────────────────────────
SimBox   = np.array([560, 560, 420])  # simulation domain [mm]
NrTS_opt   = 120000  # time steps per optimisation run (was 80000). Raised so the
                     # coarse opt runs reach (nearly) the same energy-decay
                     # convergence as NrTS_final; at 80000 a high-Q CP patch
                     # stopped short, its resonance landing ~1.8 MHz off the
                     # final value, which slid the razor-thin AR null off
                     # f_target (AR read ~2 dB in opt but ~7 dB in the final).
NrTS_final = 150000  # time steps for the final high-fidelity run  (was 80000)

# Parallel FDTD workers (within-phase). 0 = use os.cpu_count().
# Each worker spawns one openEMS subprocess; OMP_NUM_THREADS is set to 1
# per worker so openEMS doesn't itself try to claim all cores.
# Lower this if RAM is tight (~200–500 MB per concurrent sim).
num_workers = 0

# Hard ceiling on concurrent workers, applied on top of num_workers/cpu_count.
# Caps peak RAM (each concurrent sim is ~200–500 MB) and keeps the wall-clock
# estimate honest. Both the optimiser pool and the ETA derive from this via
# optimizer.resolve_workers(), so they can never disagree.
#
# NOTE: the optimizer's per-phase candidate counts (optimizer.PHASES and
# SUB_HW_N below) are aligned to this value so each phase is a single FULL wave
# (no straggler wave, no idle cores). If you change MAX_WORKERS, consider
# re-aligning those counts for best utilisation.
MAX_WORKERS = 9

# Per-phase hang guard. optimizer._run_batch waits at most this long for a
# phase's sims via as_completed(timeout=...); a wedged/diverged openEMS child is
# then recorded as a failure and the worker pool rebuilt, instead of freezing the
# whole run. Generous vs a healthy ~3–4 min phase — raise it on slow hardware.
PHASE_TIMEOUT_S = 1800

# ── Derived constants (no side effects, computed once on import) ──
substrate_kappa = substrate_tanD * 2 * np.pi * f_target * EPS0 * substrate_epsR

# Mesh resolution: λ/20 at the highest simulation frequency [mm]
mesh_res = C0 / (f_target + fc) / 1e-3 / 20

# ── Analytical initial dimensions ─────────────────────────────────
# LP width — Bahl & Trivedi equal-ripple formula
W_lp = C0 / (2 * f_target) * np.sqrt(2 / (substrate_epsR + 1)) * 1e3  # mm

# Effective permittivity — Hammerstad-Jensen
eps_eff = ((substrate_epsR + 1) / 2
           + (substrate_epsR - 1) / 2
           / np.sqrt(1 + 12 * substrate_thickness / W_lp))

# Fringing-field extension — Schneider
dL = (0.412 * substrate_thickness
      * (eps_eff + 0.3)  * (W_lp / substrate_thickness + 0.264)
      / ((eps_eff - 0.258) * (W_lp / substrate_thickness + 0.8)))

# LP resonant length
L_lp = C0 / (2 * f_target * np.sqrt(eps_eff)) * 1e3 - 2 * dL  # mm

# CP square side: average of LP width and length, calibrated shrink factor
# k_shrink=0.86 calibrated from first-sim result of reference design
W_cp = (W_lp + L_lp) / 2.0 * 0.86  # mm — Phase 0 will refine this

# Analytical starting fractions (Phase 0 / 1 / 2 use these unless warm-started)
_delta_frac   = 0.10  # 10% of W — literature starting point for truncation
_y_inset_frac = 0.07  # 7% of W  — shallow inset for 1.6 mm substrate

# ── Optimizer cost weights (lower cost = better candidate) ────────
# Each term is normalized so weight ≈ 1 makes them comparable in magnitude.
# Penalties are 0 inside the "good" region; gain reward grows above 5 dBi but
# saturates at GAIN_CAP so it can never buy past a poor axial ratio.
W_FREQ  = 1.0   # |f_res - f_target| / fc          (1.0 at edge of band)
W_MATCH = 1.0   # max(0, s11_dB + 10)  in dB       (0 once matched to -10 dB)
W_CP    = 1.0   # max(0, AR - AR_MAX)/AR_MAX       (0 once true AR ≤ AR_MAX_DB)
W_GAIN  = 1.0   # min(Dmax - 5, GAIN_CAP)  in dBi  (reward gain above 5 dBi)
W_AREA  = 0.5   # (sub_hw / SUB_HW_DEFAULT)^2  ∝ board area  (penalise big GP)

# AR is the TRUE axial ratio (dB, ≥0; 0 = perfect circular). 3 dB is the
# conventional CP spec edge. WRONG_HAND_PENALTY is added to the AR term when a
# candidate comes out LHCP-dominant (we want RHCP) so the wrong sense is never
# selected on a fluke. GAIN_CAP bounds the gain reward (dBi above 5).
AR_MAX_DB          = 3.0
WRONG_HAND_PENALTY = 3.0
GAIN_CAP           = 3.0

# AR robustness margin. The optimiser evaluates axial ratio not only at f_target
# but at f_target ± AR_MARGIN_MHZ and selects on the WORST value over that band
# (see optimizer._run_sim_worker / _cost). A single-feed corner-truncated patch
# has a razor-thin AR null; selecting at one frequency picks a design that is
# perfect in the coarse sim but collapses once the resonance drifts a MHz or two
# (fab tolerance, εr spread, or the coarse→final convergence shift). Sampling a
# band forces a flatter, drift-tolerant AR. ±1.5 MHz covers the observed
# coarse→final drift plus a little board tolerance; widen it for more margin (at
# the cost of being harder for a single-feed patch to satisfy).
AR_MARGIN_MHZ = 1.5

# ── Ground-plane / substrate half-width sweep (Phase 4) ───────────
# sub_hw_mm = half-width of the square copper ground plane AND substrate plate
# (board edge = 2 × sub_hw). At 869.52 MHz λ₀ ≈ 345 mm.
#
# Physics: a patch ground plane only needs to reach ~0.5–0.6 λ; beyond that the
# gain curve flattens and merely ripples with edge diffraction. Measured here:
# 150→375 mm board bought only ~+1.4 dBi (≈6× the area for ~1 dB), and most of
# that is already won by ~250 mm. So the board is kept SMALL: the enclosure caps
# it at 170 mm, and the cost function's area penalty (W_AREA) drives the Phase-4
# sweep to the smallest board that still meets the match / AR / frequency spec.
SUB_HW_DEFAULT = 60.0    # 120 mm board — GP used in the non-GP tuning phases and
                         # the reference size for the W_AREA area penalty.
SUB_HW_MIN     = 55.0    # 110 mm board — smallest swept GP. Leaves ≳ patch+6h of
                         # ground around the ~83 mm patch (Lg ≳ Lp+6h guideline).
SUB_HW_MAX     = 85.0    # 170 mm board — hard upper limit set by the enclosure.
SUB_HW_N       = 9       # == MAX_WORKERS: Phase-4 GP sweep fits one full wave

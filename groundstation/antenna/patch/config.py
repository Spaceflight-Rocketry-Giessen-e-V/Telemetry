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
NrTS_opt   = 80000   # time steps per optimisation run  (was 60000)
NrTS_final = 150000  # time steps for the final high-fidelity run  (was 80000)

# Parallel FDTD workers (within-phase). 0 = use os.cpu_count().
# Each worker spawns one openEMS subprocess; OMP_NUM_THREADS is set to 1
# per worker so openEMS doesn't itself try to claim all cores.
# Lower this if RAM is tight (~200–500 MB per concurrent sim).
num_workers = 0

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

# AR is the TRUE axial ratio (dB, ≥0; 0 = perfect circular). 3 dB is the
# conventional CP spec edge. WRONG_HAND_PENALTY is added to the AR term when a
# candidate comes out LHCP-dominant (we want RHCP) so the wrong sense is never
# selected on a fluke. GAIN_CAP bounds the gain reward (dBi above 5).
AR_MAX_DB          = 3.0
WRONG_HAND_PENALTY = 3.0
GAIN_CAP           = 3.0

# ── Ground-plane / substrate half-width sweep (Phase 4) ───────────
# sub_hw_mm = half-width of the square copper ground plane AND substrate plate.
# Default 75 → 150 × 150 mm board (legacy). At 869 MHz λ₀ ≈ 345 mm.
#
# Empirical: 150→250 mm board bought ~+0.9 dBi. The curve flattens fast;
# 250→400 mm typically adds another ~0.3 dBi. Upper bound 200 mm half-width
# (=400 mm board) keeps ≥80 mm clearance to the MUR boundary on each side
# with the default SimBox = 560×560 mm (guardrail in build_sim checks this).
SUB_HW_DEFAULT = 75.0
SUB_HW_MIN     = 100.0
SUB_HW_MAX     = 200.0
SUB_HW_N       = 8

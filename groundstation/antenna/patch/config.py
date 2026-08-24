# -*- coding: utf-8 -*-
"""
Simulation constants for the RHCP patch antenna.

All physical parameters and derived mesh/sim settings live here.
No switches, no side effects — safe to import from any module.
"""

import numpy as np
from openEMS.physical_constants import C0, EPS0

# ── Antenna target ────────────────────────────────────────────────
f_target = 869.525e6  # Hz — operating frequency (EU 868 g3 high-power sub-band centre)
fc       = 250e6      # Hz — Gaussian excitation half-bandwidth / post-proc sweep half-width
feed_R   = 50         # Ω  — lumped port impedance

# ── Substrate: Nan Ya NP-140F, 2-layer 1.6 mm (datasheet-specified) ──
# Switched BACK to NP-140F from generic stock FR-4 because the fab guarantees the
# laminate at EQUAL cost: we design to its DATASHEET εr (4.0–4.2 @ 1 GHz, ±0.1) instead
# of stock FR-4's unspecified ~4.2–4.6 spread (the real stock part, KingBoard KB-6164,
# measures ~4.6 / 0.0155 @ 1 GHz). Known + tighter εr means the simulated resonance lands
# on the bench (~±10 MHz batch scatter vs ~±20 MHz on KB-6164) and the patch sees a
# lower-Q, wider-band dielectric. The ~0.3–0.5 dB loss edge is irrelevant (22–30 dB link
# margin) — predictability is the reason. εr nudged to 4.15 (rises slightly below 1 GHz,
# toward 869.52 MHz); tanδ ~0.014. See docs/NP-140F-Datasheets.pdf.
substrate_material  = 'NP-140F'
substrate_epsR      = 4.15   # relative permittivity @ ~870 MHz (NP-140F datasheet 4.0–4.2 @ 1 GHz)
substrate_tanD      = 0.014  # loss tangent @ ~870 MHz (NP-140F datasheet 0.012–0.014 @ 1 GHz)
substrate_thickness = 1.6    # mm
substrate_cells     = 4      # FDTD cells through substrate thickness

# ── FDTD domain ───────────────────────────────────────────────────
SimBox   = np.array([600, 600, 600])  # simulation domain [mm]. Sized so the centred
                                      # board clears ≳λ/4 to the inner PML_8 boundary on
                                      # every face — PML_8 consumes ~8·mesh_res (≈107 mm)
                                      # inside each face.
NrTS_opt   = 150000  # time steps per optimisation run. Set EQUAL to NrTS_final so the
                     # optimiser judges AR at the same fidelity as the confirm stage: the razor
                     # AR/beamwidth does not survive a coarse→fine change, so a cheaper opt run
                     # selects on an optimistic AR that collapses at full fidelity.
NrTS_final = 350000  # time steps for the final high-fidelity run. the
                     # razor CP AR null is time-step-limited at 150k (a direct 150k vs 250k
                     # re-run of the locked W=82.5/trunc=8.25 design moved the AR null depth
                     # 0.41->1.03 dB and the AR<=3 freq band 7.9->6.6 MHz — the 150k numbers
                     # were optimistic). 350k is the convergence top-rung to confirm 250k is
                     # settled and to write a convergence-proven results.json (see tests/
                     # tool_trunc_bw_sweep.py + the convergence ladder in docs/research.md §3).
NrTS_screen = 150000  # SCREEN fidelity for the W×truncation grid. Equal to
                     # NrTS_opt: the screen must centre the AR NULL (optimizer._screen_cost on
                     # f_ar_null), and the razor AR null does NOT converge at 60k — a 60k run read
                     # AR 8.8 dB where the 150k truth is 0.4 dB, so a cheap screen mis-ranked the
                     # null-centred design (the whole single-feed re-tune traced to that). At full
                     # fidelity the null frequency is reliable; CONFIRM then re-applies the full
                     # coverage cost (incl. AR depth/beamwidth at f_target) to pick the winner.

# Parallel FDTD workers (within-phase). 0 = use os.cpu_count().
# Each worker spawns one openEMS subprocess; OMP_NUM_THREADS is set to 1
# per worker so openEMS doesn't itself try to claim all cores.
# Lower this if RAM is tight (~200–500 MB per concurrent sim).
num_workers = 0

# Hard ceiling on concurrent workers, applied on top of num_workers/cpu_count.
# Caps peak RAM/temp-disk and keeps the wall-clock estimate honest. Both the optimiser pool
# and the ETA derive from this via optimizer.resolve_workers(), so they can never disagree.
#
# SET TO 3: at the full NrTS_screen = NrTS_opt = 150k the openEMS NF2FF recording per
# sim is large, and 9 concurrent 150k sims returned EMPTY NF2FF (Prad/Dmax≈0 with a still-valid
# S11) — a RAM/temp-disk overrun — whereas 3-concurrent×150k and 9-concurrent×60k both ran clean.
# 3 keeps every phase inside the proven-safe regime; on a ~20-thread host _run_batch then gives
# each sim cores//3 ≈ 6 FDTD threads (faster per sim), so the 9-sim grid runs as 3 quick waves at
# ~the same wall-clock as one slow 9-wide wave. The worker ALSO guards against empty NF2FF (returns
# a failure so a tripped sim is excluded, not silently selected). Raise only on a host with RAM/
# scratch verified at 150k.
MAX_WORKERS = 3

# Per-phase hang guard. optimizer._run_batch waits at most this long for a
# phase's sims via as_completed(timeout=...); a wedged/diverged openEMS child is
# then recorded as a failure and the worker pool rebuilt, instead of freezing the
# whole run. MUST exceed the real wall-clock of a phase's slowest sim or healthy
# sims get marked as failures: this host runs ~0.011 s/step solo (20 threads) and
# slower under the optimiser's concurrent 4-thread sims, so a 120k-step candidate
# takes ~60-100 min. 3 h gives margin;
# lower it only on a host fast enough that a single opt sim finishes well inside it.
PHASE_TIMEOUT_S = 10800

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

# ══════════════════════════════════════════════════════════════════
# Single-feed corner-truncated RHCP design — geometry seeds
# ══════════════════════════════════════════════════════════════════
# CP comes from truncating two diagonally-opposite corners of a near-square patch
# (the chamfer splits the two degenerate modes so they are 90° apart at f_target),
# fed by ONE inset microstrip. No coupler, no isolated-port resistor — the dual-feed
# coupler dumped ~64 % of accepted power into that resistor (realised gain −9.6 dBic);
# the single feed recovers it (validated: η_rad 28 %, realised gain +0.8 dBic). All
# values are seeds — the optimiser refines W (resonance) / trunc (AR) / inset (match).

# CP square side: average of the LP width and length, shrunk by a calibrated factor
# (0.86, from the proven single-feed reference design); the optimiser refines it.
W_CP_INIT = (W_lp + L_lp) / 2.0 * 0.86   # mm  (≈ 82.5 at εr 4.15)

# Corner truncation (chamfer leg per corner). Literature/proven start ≈ 0.10·W (with
# total Q ≈ 40-50 on FR-4, the Sharma-Gupta ΔS/S ≈ 1/(2Q) gives Δ/W ≈ 0.08-0.10).
TRUNC_INIT = 0.10 * W_CP_INIT            # mm  (≈ 8.25)

# Single inset feed at the −y edge centre. 50 Ω microstrip; shallow inset on 1.6 mm.
FEED_W     = 3.2                # mm — 50 Ω line width (Hammerstad @ εr 4.15: W/h 1.997 → 50 Ω)
INSET_Y    = 0.07 * W_CP_INIT   # mm — feed inset depth (≈ 5.8; 7 % of W, proven seed)
INSET_GAP  = 0.6               # mm — etched gap each side of the inset feed line
BOARD_MARGIN  = 8.0           # mm — min ground beyond any copper (return current + edge)

# ── Optimizer cost weights (lower cost = better candidate) ────────
# Each term is normalized so weight ≈ 1 makes them comparable in magnitude;
# penalties are 0 inside the "good" region. These are the ACTIVE coverage-cost
# weights.
W_FREQ  = 1.0   # weight on the resonance penalty (shape set by F_RES_* below)
W_MATCH = 1.0   # weight on max(0, s11_dB + 10)  in dB       (0 once matched to -10 dB)

# Resonance penalty shape (optimizer._cost). The OLD penalty divided
# |f_res-f_target| by fc (250 MHz), so even a 16 MHz miss cost ~0.06 and the
# optimiser ignored resonance — run 20260606_052114 kept a +16 MHz design and
# DISCARDED an on-resonance arm=48.9 mm candidate (f −4.5 MHz, AR 2.5, BW 40°) by a
# 0.03 cost margin. Now: NO penalty within a small deadband (fab/channel tolerance),
# then a strong linear ramp on a few-MHz scale, so landing 869.52 MHz dominates the
# cost until centred, after which AR/beam fine-tune. (≈4.5 MHz off → 1.0 cost ≈ a
# 3 dB AR-over-cone penalty; 15 MHz off → 4.5.)  See also docs note in src/optimizer.py.
F_RES_DEADBAND_MHZ = 1.5   # MHz — no resonance penalty within this of f_target
F_RES_SCALE_MHZ    = 3.0   # MHz — penalty rises by 1.0 per this many MHz beyond deadband
                           #   (SHARP — used by the SCREEN cost to shortlist on-resonance
                           #    grid candidates for the confirm stage; keep it sharp.)

# Resonance penalty in the FINAL/CONFIRM cost (_cost) is a GENTLE tiebreaker, NOT a
# dominator. Once a candidate is matched at f_target (pen_s11) and clean-CP over the
# f_target±margin band (pen_ar / rew_bw, both evaluated AT the target), where the S11
# *dip* sits is electrically irrelevant for a backup patch — and fab/εr spread moves it
# several MHz anyway. Run #3 (RHCP_Patch_20260606_193640) had the SHARP penalty (2.8 for
# a 10 MHz miss) wrongly crown an on-dip / beam-0° arm=38 design over an off-dip /
# beam-44° arm=40 one. These soften ONLY the final selection (the screen stays sharp).
F_RES_DEADBAND_FINAL_MHZ = 4.0    # MHz — no final-cost resonance penalty within this
F_RES_SCALE_FINAL_MHZ    = 20.0   # MHz — gentle ramp (1.0 per 20 MHz) → tiebreaker, not driver
W_CP    = 1.0   # multiplier on the WRONG-HAND penalty in _cost. NOTE: the AR-over-cone
                # term uses W_AR_CONE (below), NOT W_CP — edit W_AR_CONE to retune AR.

# AR is the TRUE axial ratio (dB, ≥0; 0 = perfect circular). 3 dB is the
# conventional CP spec edge. WRONG_HAND_PENALTY is added to the AR term (times
# W_CP) when a candidate comes out LHCP-dominant; _cost ALSO adds a large hard-gate
# constant so a wrong-handed result can never win on a fluke.
AR_MAX_DB          = 3.0
WRONG_HAND_PENALTY = 3.0

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

# ── Coverage cost weights (single-feed coverage optimiser) ─────────────────────
# The no-tracking BACKUP patch is selected on WIDE-BEAM coverage, not boresight
# gain: reward a large AR≤3 dB elevation beamwidth, penalise the worst AR over
# the 0–COVER_CONE° cone, and hold a FLOOR on RHCP gain across the cone (not
# maximise it). These replace the old boresight-gain reward and board-area
# penalty (a small board already follows from the beamwidth reward).
W_AR_BW         = 2.0    # reward ∝ (AR≤3 dB beamwidth / AR_BW_REF). PRIMARY objective for
                        #   this coverage backup patch — raised 1.0→2.0 so a wide clean-CP
                        #   beam is decisive vs the edge-dominated worst-AR-over-cone penalty
                        #   (run #3: a 44° beam must beat a 0° beam; see F_RES_*_FINAL note).
# Radiation-efficiency term. η_rad = Prad/P_acc (dipole-validated) rewards designs that
# actually RADIATE accepted power rather than dissipate it (FR-4 dielectric loss + any
# feed mismatch — a good input S11 alone does not guarantee a high realised gain). This
# was the lesson from the retired dual-feed coupler, which radiated only ~3 % (−9.6 dBic);
# the single-feed patch recovers it (~28 %). REWARD saturates at ETA_RAD_REF; weighted
# high because a wide clean-CP beam is worthless if the antenna barely radiates.
W_EFF           = 4.0    # reward ∝ min(η_rad / ETA_RAD_REF, 1) — keeps the optimiser radiating
ETA_RAD_REF     = 0.45   # radiation efficiency at which the reward saturates (good FR-4 patch)
W_AR_CONE       = 1.0    # penalty ∝ worst-AR-over-cone above AR_MAX_DB (dominated by the 45°
                        #   cone EDGE; the beamwidth reward above is the real coverage signal)
W_GAIN_FLOOR    = 1.0    # penalty when min RHCP gain over the cone < GAIN_FLOOR_DBIC
AR_BW_REF       = 80.0   # deg — reference AR≤3 dB FULL beamwidth (reward normaliser)
GAIN_FLOOR_DBIC = 2.0    # dBic — min acceptable RHCP gain over the cone
COVER_CONE_DEG  = 45.0   # deg — half-cone over which AR/gain coverage is scored

# ── Ground-plane / substrate half-width sweep (Phase 4) ───────────
# sub_hw_mm = half-width of the square copper ground plane AND substrate plate
# (board edge = 2 × sub_hw). At 869.52 MHz λ₀ ≈ 345 mm.
#
# Physics: a patch ground plane only needs to reach ~0.5–0.6 λ; beyond that the
# gain curve flattens and merely ripples with edge diffraction. Measured here:
# 150→375 mm board bought only ~+1.4 dBi (≈6× the area for ~1 dB), and most of
# that is already won by ~250 mm. So the board is kept SMALL: the enclosure caps
# it at 170 mm, and the Phase-4 sweep is selected on the COVERAGE cost (a smaller
# GP broadens the beam → larger AR≤3 dB beamwidth reward), not on any board-area
# penalty.
# The single-feed patch only needs the board to hold the ~83 mm patch + margin, so the
# board is set purely by the wide-beam COVERAGE goal: a smaller GP broadens the beam.
SUB_HW_DEFAULT = 80.0    # 160 mm board - LOCKED. The dual-feed beamwidth-vs-GP sweep showed the AR≤3 beam
                         #   WIDENS as the GP shrinks (160→52°, 170→40°, 180→36°, 190→28°); 160 mm gave the
                         #   widest clean-CP beam and is kept for the single-feed patch (re-confirm on re-tune).
SUB_HW_MIN     = 80.0    # 160 mm — floor (patch ~83 mm + ≥0.5·BOARD_MARGIN each side).
SUB_HW_MAX     = 80.0    # 160 mm — pinned; board not swept (locked on the coverage result above).


# ── Grid search (W × corner-truncation) — the two coupled resonance/AR levers ──────
# The single-feed CP patch has two coupled levers: patch side W (resonance) and the
# corner truncation (the CP mode-split / AR null). The optimiser sweeps them on ONE 2-D
# grid at NrTS_screen, then confirms the best W per truncation at full fidelity (NrTS_opt)
# — AR is razor-thin and does NOT converge at the screen NrTS, so it is judged only at
# confirm. The single inset stays at the seed (it sets the match, not resonance/AR).
GRID_W_FRAC = (0.994, 1.000, 1.006)  # patch side W grid (fraction of the warm_start seed W).
                                   #   Brackets the seed: the W=82.5 seed already puts the AR
                                   #   NULL on f_target (NF2FF-measured 869.0 MHz, AR 0.4 dB,
                                   #   AR≤3 BW 8 MHz), so the grid stays centred on it
                                   #   (82.0/82.5/83.0 mm → null ≈ 874/869/864 MHz).
                                   #   HISTORY: an earlier version recentred UP to land the S11
                                   #   *centroid* on f_target — but the AR null sits ~7 MHz BELOW
                                   #   the centroid, so that pushed the null off (AR @ f0 went
                                   #   0.4 → 4.6 dB). The optimiser now centres the null itself
                                   #   (optimizer._cost / _screen_cost on f_ar_null), not the centroid.
GRID_TRUNC_MM = (6.5, 8.25, 10.0)  # corner-truncation grid (mm), bracketing the proven 0.10·W ≈ 8.25.
                                   #   Smaller Δ → narrower mode split → tighter AR null but more
                                   #   fab-sensitive; the sweep centres the AR≤3 null on f_target.
N_CONFIRM   = 3                    # best-W-per-truncation winners re-run at full NrTS_opt

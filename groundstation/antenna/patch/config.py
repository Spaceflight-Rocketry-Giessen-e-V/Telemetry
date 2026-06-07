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
SimBox   = np.array([600, 600, 600])  # simulation domain [mm]. Sized so the OFFSET
                                      # board (centred in the domain by build_full_sim)
                                      # clears ≳λ/4 to the inner PML_8 boundary on every
                                      # face — PML_8 consumes ~8·mesh_res (≈107 mm) inside
                                      # each face. The old 560×560×420 crowded the -x/-y/-z
                                      # PML (~0.1 λ) and biased Dmax / wide-angle AR.
NrTS_opt   = 150000  # time steps per optimisation run. Set EQUAL to NrTS_final so the
                     # opt metric matches the final-run metric. Run 20260606_052114
                     # proved the razor-thin AR/beamwidth does NOT survive coarse→final:
                     # identical dims read AR 2.5 dB / AR≤3 beam 36° at 120000 but
                     # AR 3.4 dB / 0° at 150000, so the optimiser was selecting on an
                     # optimistic AR that collapsed in the final run. Matching fidelity
                     # removes that disagreement (≈+25% time/sim; see the speed plan,
                     # which more than offsets it by cutting the sim COUNT).
NrTS_final = 150000  # time steps for the final high-fidelity run  (was 80000)
NrTS_screen = 60000  # cheap SCREEN fidelity for the coarse W×arm grid: resonance + S11
                     # converge here, but the razor AR/beamwidth does NOT — that is
                     # judged only at the full-fidelity CONFIRM stage (NrTS_opt). The
                     # grid block (below) + optimizer._run_search consume these.

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
# NOTE: the optimiser's batch sizes (the W×arm GRID = len(GRID_W_FRAC)·len(GRID_ARM_MM),
# and N_CONFIRM, below) are kept near/below MAX_WORKERS so each runs as ~one pool wave.
# With ~5 concurrent sims on a ~20-thread host _run_batch gives each sim cores//5 = 4
# FDTD threads, filling every core via threads rather than workers — better per-sim
# efficiency. On a host with far fewer cores, shrink the grid for full single waves.
MAX_WORKERS = 9

# Per-phase hang guard. optimizer._run_batch waits at most this long for a
# phase's sims via as_completed(timeout=...); a wedged/diverged openEMS child is
# then recorded as a failure and the worker pool rebuilt, instead of freezing the
# whole run. MUST exceed the real wall-clock of a phase's slowest sim or healthy
# sims get marked as failures: this host runs ~0.011 s/step solo (20 threads) and
# slower under the optimiser's concurrent 4-thread sims, so a 120k-step candidate
# takes ~60-100 min — NOT the ~3-4 min the old 1800 s assumed. 3 h gives margin;
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
# Flat dual-feed (branch-line coupler) RHCP design — geometry seeds
# ══════════════════════════════════════════════════════════════════
# CP no longer comes from corner truncation; it comes from a 90° branch-line
# hybrid feeding two orthogonal patch edges in quadrature.  So the patch is a
# plain SQUARE (side ≈ resonant length, NO 0.86 CP shrink) and the coupler +
# two feed lines are new etched copper on the same top layer.  All values are
# seeds — the optimiser refines them.  See docs/migration-plan.md §2.

# Square patch side seed — a square resonates on its side length, so seed from
# the LP resonant length L_lp (≈ 83 mm at 869.52 MHz on FR-4 1.6 mm).
W_SQ_INIT = L_lp                 # mm

# Branch-line coupler: a square ring of four λg/4 arms. Through arms are
# Z0/√2 = 35.36 Ω (wider); the shunt arms and I/O lines are 50 Ω. Hammerstad
# widths on εr=4.15 / h=1.6 mm (re-synthesised for NP-140F; lower εr → wider lines).
CPL_W50 = 3.2                    # mm — 50 Ω line width   (Hammerstad synth @ εr 4.15: W/h 1.997 → 50.0 Ω)
CPL_W35 = 5.43                   # mm — 35.36 Ω line width (Hammerstad synth @ εr 4.15: W/h 3.391 → 35.4 Ω)
# Arm length ≈ λg/4. Textbook εeff≈3.3 gives λg/4≈47 mm, but in-situ the coupler is loaded
# by the patch+feeds (effective εeff≈4.8). The validated clean-CP design (W=87.14/arm=48)
# resonated AND delivered good quadrature TOGETHER at 714 MHz; uniformly scaling the whole
# structure by 714/869.52 = 0.821 moves that onto the target, giving arm ≈ 48*0.821 ≈ 40 mm.
# (The earlier "arm=48 quadrature is mistuned to 714" reading came from a malformed-patch run
# and is RETRACTED — 714 was simply where the un-scaled design happened to work.)
CPL_ARM = 40.0                   # mm — 0.821 * 48 (scaled λg/4 for clean CP at 869.52)
# Local fine mesh for the coupler/feed copper: config.mesh_res (~13 mm) is far too
# coarse for the ~3-5 mm strips and ~0.6 mm gaps, so the coupler arms/feeds get an
# explicit fine mesh at this scale (3+ cells across every strip width).
METAL_EDGE_RES = 0.4             # mm — local mesh near coupler/feed edges

# Feed routing: each coupler output → its orthogonal inset feed point. The two
# 50 Ω feed lines MUST be equal electrical length so the 90° quadrature reaches
# the patch intact.
FEED_W     = CPL_W50             # mm — feed lines are 50 Ω microstrip
INSET_X    = 16.0               # mm — inset depth, x-edge feed (impedance match); matches the
INSET_Y    = 16.0               #      validated anchor. dual_feed_layout auto-caps it to
                                #      (W-arm)/2-3.15 at small W so the two notches never collide.
INSET_GAP  = 0.6                # mm — etched gap each side of an inset feed line
CPL_PATCH_GAP = 2.5            # mm — copper gap, coupler TR corner → patch BL corner
ISO_STUB      = 6.0            # mm — short stub from the isolated corner to its 50 Ω R
BOARD_MARGIN  = 8.0            # mm — min ground beyond any copper (return current + edge)
INPUT_STUB = 25.0              # mm — 50 Ω input stub that hosts the MSL port
                                #      (≈0.13 λg: room for ≥5 prop mesh lines plus
                                #      the excitation/measurement planes ahead of
                                #      the first coupler junction)

# ── Optimizer cost weights (lower cost = better candidate) ────────
# Each term is normalized so weight ≈ 1 makes them comparable in magnitude;
# penalties are 0 inside the "good" region. These are the ACTIVE coverage-cost
# weights (the old boresight-gain / board-area weights were retired & removed).
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

# ── Coverage cost weights (flat dual-feed design; rewritten optimiser) ─────────
# The no-tracking BACKUP patch is selected on WIDE-BEAM coverage, not boresight
# gain: reward a large AR≤3 dB elevation beamwidth, penalise the worst AR over
# the 0–COVER_CONE° cone, and hold a FLOOR on RHCP gain across the cone (not
# maximise it). These replace the old boresight-gain reward and board-area
# penalty (a small board already follows from the beamwidth reward).
W_AR_BW         = 2.0    # reward ∝ (AR≤3 dB beamwidth / AR_BW_REF). PRIMARY objective for
                        #   this coverage backup patch — raised 1.0→2.0 so a wide clean-CP
                        #   beam is decisive vs the edge-dominated worst-AR-over-cone penalty
                        #   (run #3: a 44° beam must beat a 0° beam; see F_RES_*_FINAL note).
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
# For the dual-feed design the board (= ground = substrate) must also hold the
# ~47×47 mm coupler and the two feed lines beside the ~83 mm patch, so the floor
# is larger than the old single-feed board. The coverage sweep then prefers the
# SMALLEST board that still fits and meets AR/match (a smaller GP broadens the
# beam — the wide-beam goal — so no separate area penalty is needed).
SUB_HW_DEFAULT = 80.0    # 160 mm board - LOCKED. A beamwidth-vs-GP sweep (tests/board_sweep.py) showed the
                         #   AR≤3 beam WIDENS as the GP shrinks (160→52°, 170→40°, 180→36°, 190→28°);
                         #   160 mm is the coupler-limited floor (need ~79 mm half-width) and is best on
                         #   every CP metric (AR 1.70 dB, worst-cone 5.5 dB, min-gain-over-cone ~0 dBic).
SUB_HW_MIN     = 80.0    # 160 mm — floor (coupler+feeds + 8 mm margin need ~79 mm half-width).
SUB_HW_MAX     = 80.0    # 160 mm — pinned; board no longer swept. dual_feed_layout auto-grows only if
                         #   the coupler+stub need more (need ~79 < 80), so the board is exactly 160 mm.
SUB_HW_N       = 5       # (legacy) old GP-sweep candidate count. The GP phase was
                         # DROPPED — the coupler footprint pins the board near ~178 mm,
                         # so the optimiser no longer sweeps sub_hw; kept for reference.


# ── Grid search (W × coupler-arm) — replaces the sequential phase schedule ──────
# The optimiser sweeps the two COUPLED resonance/AR levers (patch side W and coupler
# arm) on ONE independent 2-D grid at NrTS_screen, then confirms the best W per arm at
# full fidelity (NrTS_opt). This escapes the coordinate-descent basin trap — run
# 20260606_052114 tuned W and arm in SEPARATE phases and kept a +14.9 MHz design — and
# is ~2-3x faster (fewer sims, fewer waves, most cheap). inset stays at the seed (it
# sets the match, not resonance); the board is fixed (the coupler pins it near ~178 mm).
GRID_W_FRAC = (0.98, 1.00, 1.02)   # patch side W grid (fraction of the warm_start seed W). RE-WIDENED
                                   #   to ±2 % for the εr 4.3→4.15 (NP-140F) re-anchor: lower εr grows
                                   #   the resonant W ~+1.8 %, so the seed was bumped 71.5→72.5 mm
                                   #   (run.py warm_start) and the grid widened so the new basin is
                                   #   bracketed (~71.1–74.0 mm; wings ±14 MHz) despite in-situ
                                   #   uncertainty. Re-tighten to ±1 % once a scout re-locates the basin.
GRID_ARM_MM = (38.0, 40.0, 42.0)   # coupler-arm grid (mm), bracketing the scaled 0.821*48≈39.4.
                                   #   W is now resonance-calibrated, so this sweep is mostly to
                                   #   widen the AR≤3 coverage beamwidth (44° at arm=40 in the scout).
N_CONFIRM   = 3                    # best-W-per-arm winners re-run at full NrTS_opt

# Patch antenna — work in progress

CP / match / handedness are **validated** (latest sim `RHCP_Patch_20260607_120756`):
160×160 mm, NP-140F (εr 4.15, tanδ 0.014), 1.6 mm, W = 72.5 / coupler-arm 40,
dual-feed branch-line coupler, **869.525 MHz** (f_res 870.7 MHz), RHCP.

- Boresight: S11 −11.0 dB, AR 1.64 dB, **directivity 5.9 dBi** (was mis-reported as 3.9 — see below),
  AR≤3 dB beam 56°.
- 45° coverage cone: worst AR 5.3 dB, min RHCP **directivity** ~2.0 dBic.
- ⚠️ **Realised gain ≈ −9.6 dBic** (η_rad ≈ 3 %). The antenna radiates only ~3 % of accepted
  power — see "Efficiency resolved" below. The link still closes, but a feed-match re-tune is recommended
  **before fabricating**.

KiCad board exported (`patch_antenna.kicad_pcb`): NP-140F / 869.525 silk, datasheet-style
silk, soldermask keep-out over RF copper, edge-launch SMA land, isolated-port R (R50_ISO)
+ ground via, 3× M3 holes. (The board reflects the CURRENT dims; it changes if the feed is re-tuned.)

---

## ✅ Efficiency / realised gain — RESOLVED (was the parked sim/analysis rework)

The parked items are done. The dipole-validated method (`tests/stage0_dipole_calibration.py`)
turned up TWO real findings — and showed the WIP's earlier hypotheses (bad NF2FF box, Prad
normalisation) were targeting **non-bugs**:

1. **Directivity units bug (fixed).** openEMS `nf2ff.Dmax` is a LINEAR ratio, not dBi —
   directivity = `10·log10(Dmax)` (`metrics.directivity_dbi`). The repo reported the raw ratio
   as dBi, so the true boresight directivity is **5.9 dBi, not 3.9**; min-gain-over-cone, the
   optimizer gain term and `board_sweep` were all ~2 dB low. Proven: a lossless half-wave dipole
   gives openEMS Dmax 1.656 → 2.19 dBi == textbook 2.15.

2. **Radiation efficiency ≈ 3 % is REAL (not an artefact).** Prad was never 33× wrong — it matches
   a fine-sphere solid-angle integral to 0.5 %, and the dipole gives η_rad = Prad/P_acc ≈ 100 %
   (lossless). The patch genuinely radiates **η_rad ≈ 3.1 %** of accepted power → **realised gain
   ≈ −9.6 dBic** vs 5.9 dBi directivity. Cause: the branch-line coupler routes the patch's
   feed-point mismatch into the **isolated-port 50 Ω resistor**; the good S11 (−11 dB) is the
   coupler MASKING that mismatch. Decomposition: a single MSL-fed patch (no coupler / iso-R)
   radiates ~29 %, so the iso-resistor dump dominates the dual-feed loss.

Implemented: `postproc._band_sweep` now computes η_rad / η_tot / realised gain (validation-gated
on 0 < η_rad ≤ 1), restored to `directivity_vs_freq.png`, `gain_vs_theta.png`, `results.json`
(`eta_rad`/`eta_tot`/`realised_gain_dBic`), the summary sheet and console. Outputs were regenerated
from the existing sim_data (no re-sim needed; the box was never the problem).

**Link budget still closes** (`tests/tool_link_budget.py`): at −9.6 dBic the 10 km downlink keeps
~16 dB margin boresight, ~12 dB at the cone edge (the original ~30 dB margin absorbs the ~13 dB
realised-gain deficit). A feed-match re-tune recovers ~28 dB. *(TX power / RX sensitivity are stated
assumptions — the repo has no numeric link budget; plug in the real mission figures.)*

## ▶ CURRENT FOCUS — feed-match re-tune (stop the iso-resistor dump)

Goal: get power INTO the patch (radiate) instead of into the isolated-port resistor, raising
realised gain from ≈ −9.6 dBic toward ≈ +2 dBic, while keeping the clean CP.

- [ ] **Coupler arm is mis-tuned.** The fast circuit model (`tests/tool_coupler_circuit.py`) puts
      the optimum at **arm ≈ 48 mm (λg/4)**, not the current 40. The config's "loaded εeff 4.8 → 40 mm"
      rationale looks wrong (patch loading doesn't change the *arm* εeff). Arm 48 gives S11/isolation
      −37 dB, balance 0, phase 90°.
- [ ] **Patch feed match needs a deeper effective inset** (~L/3 ≈ 22 mm to reach 50 Ω), but the
      geometry caps inset at `h − arm/2 − 3.2` (≈ 13 mm at arm 40, ≈ 9 mm at arm 48) because the two
      feeds tap OFF-CENTRE near the lower-left corner (yL = xB = −arm/2) and the adjacent insets collide.
      **The current topology cannot give both a proper arm AND a deep enough inset.**
- [ ] **Fix = geometry redesign** (geometry.py): relocate the feed taps toward the patch EDGE CENTRES
      (yL, xB → ~0) so deep insets fit and the modes are fed symmetrically, and/or insert a **λ/4
      transformer** in each (equal-length) feed line. Then re-optimise.
- [ ] **Re-optimise with the new efficiency-aware cost.** Added `config.W_EFF` / `ETA_RAD_REF` and
      η_rad into `optimizer._run_sim_worker` + `_cost` / `_screen_cost`, so the optimiser now selects
      designs that actually radiate. This is a multi-hour FDTD campaign + a 150k confirm + board regen.
- [ ] Re-run `tests/tool_link_budget.py` at the re-tuned realised gain to confirm the recovered margin.

> Note: a 60k screen sweep of in-geometry levers (arm/inset) was inconclusive — the mismatched
> structure is so high-Q that 60k doesn't converge; the matched re-tune should converge much faster.

## ⛔ Pre-fab gates (resolve before ordering)
- [ ] **Decide: fab the current −9.6 dBic design (link still closes) OR re-tune first.** Re-tuning
      changes the board, so don't order until this is settled.
- [ ] **Confirm the fab actually supplies NP-140F** at 160×160. JLCPCB's cheap tier stocks
      KingBoard KB-6164 (εr ~4.6), NOT Nan Ya NP-140F (εr 4.15). If not guaranteed: accept KB-6164
      and re-tune for εr 4.6, or pick a fab that stocks Nan Ya.
- [ ] **Lock RHCP sense before committing copper** (issue #43) — confirm the sim handedness matches
      the rocket's RHCP QFH; wrong sense = ~15–20 dB cross-pol loss.

## Notes
- Radio-side **daughterboard** (matching resistors behind the SMA) is a *separate* board — not this one.
- Old run dirs / logs / `board_sweep_results.json` are gitignored build artefacts (regenerable).
- New NF2FF calibration test: `python tests/stage0_dipole_calibration.py` (PASS = absolute
  efficiency/realised gain are trustworthy).

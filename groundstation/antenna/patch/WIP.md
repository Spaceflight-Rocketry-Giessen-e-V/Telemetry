# Patch antenna — work in progress

**Single-feed corner-truncated RHCP patch** (branch `patch_antenna_SF`), replacing the
retired dual-feed branch-line coupler (which dumped ~64 % of accepted power into its
isolated-port resistor → realised gain −9.6 dBic).

NP-140F (εr 4.15, tanδ 0.014), 1.6 mm, **869.525 MHz**, 160×160 mm board, RHCP, one
edge-launch SMA, **no coupler, no termination resistor**.

## ✅ RESOLVED — the design is the config seed
The full optimise + NF2FF analysis showed the patch **already works at the seed**. The
earlier "AR 6.2 dB, needs tuning" was a **reporting artefact**, not the antenna.

**Final geometry: W = 82.5 mm · corner truncation Δ = 8.25 mm · feed inset = 5.8 mm ·
board 160 mm** (these ARE the `config.py` synthesis seeds — `default_params()`).

| metric | value (150k, NF2FF) |
|---|---|
| Axial ratio @ f0 | ~**1.4 dB** band-robust (single-freq 0.45 dB is optimistic & **not convergence-proven** — the 150k run capped before −40 dB; the optimiser's worst-over-band AR0 = 1.4 dB) |
| AR ≤ 3 dB beam | **to the horizon (upper hemisphere)** — "180°" is the metric ceiling (θ swept 0–90° only), worst 1.0 dB over the 45° cone |
| AR ≤ 3 dB freq bandwidth | **7.5 MHz** — ⚠️ NARROWER than the ±0.1 εr null shift (~±10 MHz) + thermal; **NOT drift-robust**, see the cold-tune gate |
| Return loss S11 @ f0 | −12.1 dB (idealised MSL port; the as-built SMA-launch transition is un-simulated, see gates) |
| Directivity / realised | 6.6 dBi / **+0.84 dBic boresight, ≈ −2.0 dBic at the 45° cone edge** (η_tot 26.5 %) |
| Radiation eff. η_rad / η_tot | 28.3 % / 26.5 % |
| **Realised gain** | **+0.8 dBic**, RHCP (BLTR diagonal) |

## 🔑 What the optimise taught us (two bugs found + fixed)
The CP **axial-ratio null sits ~7 MHz BELOW the S11 centroid** — a *matched* patch is not
automatically circular at f_target. NF2FF-measured on real sim_data:
`W=82.5 → null 869.0 MHz / AR 0.45 dB`, `W=83.05 → null 863.5 / AR 4.6`.

1. **Optimiser centred the wrong frequency.** It drove the S11 centroid (`f_res`) to
   f_target, which pushed the AR null ~7 MHz low. Fixed: the worker now scans boresight AR
   over f_target ± 20 MHz and `_cost`/`_screen_cost` centre **`f_ar_null`** instead;
   `GRID_W_FRAC` brackets the seed; `NrTS_screen` 60k → 150k (the razor null doesn't
   converge at 60k — a 60k run read AR 8.8 dB where the 150k truth is 0.4).
2. **Postproc smoothing crushed the null.** The AR-vs-f sweep used a 25 MHz boxcar (5-pt
   over 5 MHz/pt) that refilled the few-MHz null → reported ~5 dB. Fixed: fine 0.5 MHz grid
   + light 3-pt smooth; now reports AR-null freq / AR_min / contiguous AR≤3 bandwidth.

## ▶ In progress
- [ ] **Verification optimise** (corrected AR-null objective, NrTS_screen=150k) running to
      confirm W ≈ 82.5 / Δ 8.25 is the cost optimum (and check if another Δ widens the AR
      band). The deliverable board already comes from the validated W=82.5 sim_data.

## ⛔ Pre-fab gates
- [x] Lock RHCP sense vs the rocket's QFH — **QFH confirmed RHCP (team, 2026-06-08)**; the
      patch is RHCP (BLTR diagonal) → matched pair, 0 dB polarisation loss. (issue #43)
- [ ] **GATE — per-unit cold-AR acceptance test (REQUIRED, not optional).** The CP null is a
      narrow 7.5 MHz band and ±0.1 εr alone shifts it ~±10 MHz (corrected; the earlier "8 MHz
      absorbs the spread" claim was wrong — the band is NARROWER than the spread). A mid/edge-spec
      or hot board can run near-linear (AR>3 → ~3 dB pol loss). Measure each board's boresight AR
      at 869.525 and bin/tune; CP cannot be assumed from the sim.
- [x] **εr/thickness robustness sweep DONE** (tool_eps_sweep.py): null moves ~−10 MHz per +0.1 εr;
      only εr≈4.15 keeps AR≤3 in-channel (±0.1 εr → AR@f0 8–13 dB, near-linear). Thickness ±0.1 mm
      fine. **⇒ as-built 1.6 mm CP is εr-fragile.** Options: (a) **3.2 mm re-optimise** to widen the
      AR band ≳±10 MHz (recommended; also +1.5–2 dB; needs PCBWay) · (b) measured-εr batch + re-tune
      · (c) accept linear fallback (−3 dB pol; link still closes). Per-board cold-AR test stays a gate.
- [ ] **GATE — convergence check**: the 150k run capped before the −40 dB stop; re-run the
      nominal point at ≥250k (and a finer mesh of the sub-cell 8.25 mm chamfer) to prove the
      AR null depth/beamwidth are settled, not staircase/ring-down artefacts.
- [ ] Confirm the fab supplies NP-140F at 160×160 IN WRITING (JLCPCB cheap tier defaults to
      KB-6164-class εr ~4.6 → patch lands ~25 MHz low; prepare that re-tune as a fallback).
- [ ] Simulate/measure the **radome** as a superstrate (detunes the marginal CP downward) and
      the **real SMA-launch** S11 (the 3.2→0.61 mm neck adds ~3 nH the −12 dB sim didn't see).

## Notes
- `tests/stage0_dipole_calibration.py` validates the NF2FF efficiency/directivity (lossless
  dipole → η≈100 %, Dmax 2.19 dBi); run it if absolute numbers ever look off.
- The board (`kicad_export`) is regenerated from the W=82.5 results.json; old run dirs /
  `board_sweep_results.json` are gitignored build artefacts (regenerable).

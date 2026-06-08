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
| Axial ratio @ f0 | **0.45 dB** (AR_min 0.41 dB, null at 869.0 MHz) |
| AR ≤ 3 dB beam | **180°** (worst 1.0 dB over the 45° cone) |
| AR ≤ 3 dB freq bandwidth | **8 MHz** (robust to fab/εr drift) |
| Return loss S11 @ f0 | −12.1 dB |
| Directivity | 6.6 dBi |
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
- [ ] Confirm the fab supplies NP-140F at 160×160 (else re-tune for KB-6164 εr ~4.6 — the
      8 MHz AR bandwidth absorbs the εr spread, but resonance/null shift must be checked).
- [ ] Lock RHCP sense vs the rocket's RHCP QFH (issue #43).
- [ ] Per-unit cold-test recommended (single-feed CP AR is εr/fab-sensitive; the known
      NP-140F εr is what makes it land — the 8 MHz AR band gives margin).

## Notes
- `tests/stage0_dipole_calibration.py` validates the NF2FF efficiency/directivity (lossless
  dipole → η≈100 %, Dmax 2.19 dBi); run it if absolute numbers ever look off.
- The board (`kicad_export`) is regenerated from the W=82.5 results.json; old run dirs /
  `board_sweep_results.json` are gitignored build artefacts (regenerable).

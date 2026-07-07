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

| metric | value (**350k, convergence-proven**) |
|---|---|
| Axial ratio @ f0 | **1.04 dB** boresight — now CONVERGED (150k→250k→350k ladder; 250k==350k). The old 0.45 dB was the optimistic 150k value; the converged null is ~1.0 dB. |
| AR ≤ 3 dB beam | **±76° (152°)** — converged (the old "180°" was the θ-sweep ceiling); worst **1.66 dB** over the ±45° cone |
| AR ≤ 3 dB freq bandwidth | **6.5 MHz** (converged; the 150k 7.5 MHz was optimistic) — ⚠️ still NARROWER than the ±0.1 εr null shift (~±10 MHz) + thermal; **NOT drift-robust**, see the cold-AR gate |
| Return loss S11 @ f0 | −12.6 dB (idealised MSL port; the as-built SMA-launch transition is un-simulated, see gates) |
| Directivity / realised | 6.6 dBi / **+0.98 dBic boresight, ≈ −1.85 dBic at the 45° cone edge** (η_tot 27.4 %) |
| Radiation eff. η_rad / η_tot | 29.0 % / 27.4 % |
| **Realised gain** | **+1.0 dBic**, RHCP (BLTR diagonal) |

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

## ✅ Truncation is at its 1.6 mm CP optimum — no geometric improvement available
A direct (W × truncation) drift-margin sweep (`tests/tool_trunc_bw_sweep.py`, scores each
design by how far its AR≤3 band extends past the 869.4–869.65 channel = the εr/thermal drift
it absorbs) settled the "can another Δ widen the AR band?" question with data:
- **Bigger Δ over-splits the two CP modes** — at W=82.5, AR_min climbs monotonically
  0.41 → 2.83 → 5.44 → 7.55 dB for Δ = 8.25 → 9.5 → 11 → 12.75 (CP destroyed). Δ=8.25
  (the textbook 0.10·W) already sits at the deepest null / widest band.
- A fine bracket at 150k *looked* like Δ=8.5 widened the band (9.9 vs 7.9 MHz), **but it was
  a 150k under-convergence artefact**: at 250k, Δ=8.25/8.5/8.6 are identical (6.5–6.7 MHz
  band, ~3 MHz drift margin). 1.6 mm is Q-limited; the band cannot be widened by truncation.
- ⇒ **W=82.5 / Δ=8.25 stands as the optimum.** The only band-widening lever is thickness
  (3.2 mm) — **explicitly off the table** (decision: stay 1.6 mm).

## ⛔ Pre-fab gates
- [x] Lock RHCP sense vs the rocket's QFH — **QFH confirmed RHCP (team, 2026-06-08)**; the
      patch is RHCP (BLTR diagonal) → matched pair, 0 dB polarisation loss. (issue #43)
- [ ] **GATE — per-unit cold-AR acceptance test (REQUIRED, not optional).** The CP null is a
      narrow **6.5 MHz** band (converged) and ±0.1 εr alone shifts it ~±10 MHz — the band is
      NARROWER than the spread. A mid/edge-spec or hot board can run near-linear (AR>3 → ~3 dB pol
      loss). Measure each board's boresight AR at 869.525 and bin/tune; CP cannot be assumed from
      the sim. ⚠️ Make this an **at-temperature** test, not just room-temp — thermal drift is a
      second drift source (see the thermal gate below).
- [x] **εr/thickness robustness sweep DONE** (tool_eps_sweep.py): null moves ~−10 MHz per +0.1 εr;
      only εr≈4.15 keeps AR≤3 in-channel (±0.1 εr → AR@f0 8–13 dB, near-linear). Thickness ±0.1 mm
      fine. **⇒ as-built 1.6 mm CP is εr-fragile.** **DECISION: stay 1.6 mm** (no 2/3.2 mm) — the
      3.2 mm band-widening lever is off the table. Mitigation = the per-board cold-AR gate above
      (the design is otherwise at its 1.6 mm CP optimum; truncation cannot widen the band). If a
      board lands near-linear it falls back to −3 dB pol and the link still closes (backup role).
- [ ] **GATE — thermal CP window** (`tests/tool_thermal_drift.py`, NEW): TCDk(εr)+CTE walk the
      null with temperature — a SECOND ±-several-MHz drift on top of the εr-lot spread, which a
      one-time room-temp tune cannot cancel. **First run (PLACEHOLDER −300 ppm/°C TCDk, illustrative):
      null walks ~+0.11 MHz/°C (~+8 MHz over −15→+55 °C); CP@channel holds ≈0→55 °C but FAILS at
      −15 °C (the COLD side breaks first, AR ~3.5 dB).** ⚠️ TCDk/CTE are PLACEHOLDER FR-4 values —
      **get NP-140F's datasheet TCDk + CTE in writing** (with the εr confirmation) for the real window.
      ⇒ Run the per-board cold-AR gate at the **COLD operating extreme**, not just room temperature.
- [x] **GATE — convergence check DONE.** Re-ran the locked nominal point on a 150k→250k→350k
      NrTS ladder (`config.NrTS_final` now 350k). The AR null IS time-step-limited at 150k but
      **settles by 250k**: boresight AR 0.45(150k)→1.04(250k)→1.04(350k); AR≤3 band 7.9→6.6→6.5 MHz;
      250k==350k ⇒ converged. `fab/results.json` is now the convergence-proven 350k run (geometry
      unchanged; only the over-optimistic 150k metrics were corrected — silk updated to match).
      Finer chamfer-mesh rungs were not needed (the band/null stop moving on the NrTS axis alone).
- [ ] Confirm the fab supplies NP-140F at 160×160 IN WRITING (JLCPCB cheap tier defaults to
      KB-6164-class εr ~4.6 → patch lands ~25 MHz low; prepare that re-tune as a fallback).
- [ ] Simulate/measure the **radome** as a superstrate (detunes the marginal CP downward) and
      the **real SMA-launch** S11 (the 3.2→0.61 mm neck adds ~3 nH the −12 dB sim didn't see).

## Notes
- `tests/stage0_dipole_calibration.py` validates the NF2FF efficiency/directivity (lossless
  dipole → η≈100 %, Dmax 2.19 dBi); run it if absolute numbers ever look off.
- The board (`kicad_export`) is regenerated from the W=82.5 results.json; old run dirs /
  `board_sweep_results.json` are gitignored build artefacts (regenerable).
- **New analysis tools** (both clone the `tool_eps_sweep` harness; AR-vs-f at θ=2°, fixed dims):
  - `tests/tool_trunc_bw_sweep.py` — (W × truncation) DRIFT-MARGIN sweep; scores each design by
    how far its AR≤3 band extends past the channel edges. Used to prove Δ=8.25 is the 1.6 mm
    optimum and that the 150k "Δ=8.5 wider band" was an under-convergence artefact.
  - `tests/tool_thermal_drift.py` — TCDk(εr)+CTE temperature sweep → CP-in-channel temperature
    window. PLACEHOLDER FR-4 coefficients until the NP-140F datasheet values are confirmed.
- `config.NrTS_final` is now **350000** (was 150000): the razor CP null is time-step-limited at
  150k and only settles by ~250k; the deliverable run must use the convergence-proven fidelity.

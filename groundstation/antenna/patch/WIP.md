# Patch antenna — work in progress

**Migrated to a SINGLE-FEED corner-truncated RHCP patch** (branch `patch_antenna_SF`),
replacing the dual-feed branch-line coupler. The coupler dumped ~64 % of accepted power
into its isolated-port resistor (realised gain −9.6 dBic); deleting it recovers that power.

NP-140F (εr 4.15, tanδ 0.014), 1.6 mm, **869.525 MHz**, 160×160 mm board, RHCP, one
edge-launch SMA, **no coupler, no termination resistor**.

## ✅ Done — coupler → single-feed migration
- CP now from truncating two diagonal corners of a near-square patch (chamfer Δ), fed by
  ONE inset microstrip at the −y edge centre. `geometry.notched_square_polygon` gained
  `trunc`/`diag`; `geometry.single_feed_layout` replaces `dual_feed_layout`;
  `model.build_patch_sim` rebuilt (PML_8, centred board); `build_full_sim` + coupler
  geometry deleted. `PatchParams` = W_mm / trunc_mm / inset_y_mm / sub_hw_mm.
- Optimizer grid is now **W × corner-truncation** (resonance × AR), efficiency-aware
  (`W_EFF`); postproc / plotting / run.py / kicad_export all on the single-feed layout;
  coupler tests + `tool_coupler_circuit` deleted.
- **Validated** (throwaway 150k at the proven warm-start dims W 82.5 / Δ 8.25 / inset 5.8,
  from the old single-feed branch re-scaled to εr 4.15):

  | | dual-feed coupler | **single-feed (un-tuned seed)** |
  |---|---|---|
  | η_rad | 3.1 % | **28.4 %** |
  | Realised gain | −9.6 dBic | **+0.8 dBic** |
  | Directivity | 5.9 dBi | 6.6 dBi |
  | Handedness | RHCP | **RHCP** (BLTR diagonal) |
  | S11 | −11 dB | −10.9 dB |
  | AR | 1.64 dB | **6.18 dB ← needs tuning** |

## ▶ CURRENT FOCUS — tune the CP (AR) to ≤3 dB
- [ ] **Full optimise** (`python run.py` with `single_sim_only=False`, ~3 h): the W×truncation
      grid centres the AR null on f_target. AR 6.2 at the seed is just un-tuned (truncation Δ
      sets the mode split, W centres resonance); corner-truncated patches reach AR <1 dB tuned.
- [ ] Confirm η / realised gain hold (~+1–3 dBic; FR-4's 33 % dielectric loss is the ceiling)
      and re-check `tests/tool_link_budget.py` at the tuned realised gain.
- [ ] Watch handedness: the build uses the BLTR diagonal (= RHCP at +z, validated). The
      console prints "FLIP truncation diagonal" if a run comes out LHCP.

## ⛔ Pre-fab gates
- [ ] Optimise first — the board (`kicad_export`) should reflect the TUNED dims, not the seed.
- [ ] Confirm the fab supplies NP-140F at 160×160 (else re-tune for KB-6164 εr ~4.6).
- [ ] Lock RHCP sense vs the rocket's RHCP QFH (issue #43).

## Notes
- Single-feed CP AR is εr/fab-sensitive (the original reason the coupler was chosen); the
  NP-140F datasheet-known εr is what makes it tunable now. Per-unit cold-test recommended.
- `tests/stage0_dipole_calibration.py` validates the NF2FF efficiency/directivity; run it if
  absolute numbers ever look off.
- Old run dirs / `board_sweep_results.json` are gitignored build artefacts (regenerable).

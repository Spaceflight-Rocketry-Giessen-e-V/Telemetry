# Patch antenna — work in progress

Design is **committed & validated** (latest sim `RHCP_Patch_20260607_120756`):
160×160 mm, NP-140F (εr 4.15, tanδ 0.014), 1.6 mm, W = 72.5 / coupler-arm 40,
dual-feed branch-line coupler, **869.525 MHz** (f_res 870.7 MHz), RHCP.

- Boresight: S11 −11.0 dB, AR 1.64 dB, Dmax 3.9 dBi, AR≤3 dB beam 56°.
- 45° coverage cone: worst AR 5.3 dB, min RHCP gain ~0 dBic.

KiCad board exported (`patch_antenna.kicad_pcb`): NP-140F / 869.525 silk, datasheet-style
silk (front boresight-farfield panel, back elevation panel + sunburst deco), soldermask
keep-out over RF copper, edge-launch SMA land, isolated-port R (R50_ISO) + ground via, 3× M3 holes.

---

## ▶ CURRENT FOCUS — PCB fabrication
- [ ] Generate Gerbers + drill (NC) from `patch_antenna.kicad_pcb`.
- [ ] Fab-readiness review: trace/gap vs fab min, SMA land, vias, mask openings, edge cuts, drills.
- [ ] Fab order spec: 2-layer, 1.6 mm, **NP-140F** (see gate below), HASL (or ENIG), 1 oz (2 oz optional), qty 5.
- [ ] Hand-assembly notes: edge-launch SMA (WE 60312202114514), 1× 50 Ω 0402/0603 at R50_ISO.

## ⛔ Pre-fab gates (resolve before ordering)
- [ ] **Confirm the fab actually supplies NP-140F** at 160×160. JLCPCB's cheap tier stocks
      KingBoard KB-6164 (εr ~4.6), NOT Nan Ya NP-140F (εr 4.15). If NP-140F isn't guaranteed:
      either accept KB-6164 and re-tune W for εr 4.6 (patch ~−2 %), or pick a fab that stocks Nan Ya.
- [ ] **Lock RHCP sense before committing copper** (issue #43) — confirm the sim handedness
      matches the rocket's RHCP QFH; wrong sense = ~15–20 dB cross-pol loss.

## ⏸ Parked — sim / analysis (deferred; not blocking fab)
- [ ] **NF2FF efficiency / realised gain** — absolute efficiency is NOT trustworthy: openEMS
      directivity (Dmax 3.9 dBi) is correct, but `nf2ff.Prad` came out ~33× below the port
      accepted power → a non-physical ~3 % / −11.6 dBic, so it was dropped from the outputs
      (directivity reported instead). TODO lives in `src/postproc.py::_band_sweep`. Fix order:
      (1) prime suspect is `build_full_sim`'s default `CreateNF2FFBox()` on the OFFSET board —
      re-create with explicit bounds enclosing the board with ≥ λ/4 PML clearance, re-sim;
      (2) integrate Prad on a fine full sphere; (3) validate vs a lossless dipole (~100 %).
      Then restore η_rad/η_tot/realised-gain to `plot_gain_vs_freq`, `results.json`, summary sheet.
      Realised gain IS below 3.9 dBi (FR-4 + isolated-resistor loss) — bench-measure if the fix stalls.
- [ ] **Link-budget re-check vs realised gain** — the 22–30 dB margin was figured at ~4 dBic
      directivity; confirm it still closes at the (lower) realised gain once known.

## Notes
- Radio-side **daughterboard** (matching resistors behind the SMA) is a *separate* board — not this one.
- Old run dirs / logs / `board_sweep_results.json` are gitignored build artefacts (regenerable).

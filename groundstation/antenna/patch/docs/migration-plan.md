# Flat dual-feed (branch-line coupler) RHCP patch — as-built design notes

> **⚠️ SUPERSEDED 2026-06-08 — the dual-feed coupler design below is RETIRED.** A power
> decomposition showed the branch-line coupler dumps ~64 % of accepted power into its
> isolated-port resistor (realised gain −9.6 dBic). The design migrated to a **single-feed
> corner-truncated RHCP patch** (no coupler, no resistor) on branch `patch_antenna_SF`,
> which recovers that power (validated: η_rad 28 %, realised +0.8 dBic, RHCP). See WIP.md
> and [[patch-antenna-sim-state]] for the current design; the notes below are kept as
> historical reference for the §0/§2/§5 anchors that some pre-migration docstrings cite.

> **STATUS — migration COMPLETE.** The 869.52 MHz ground-station backup patch is a
> single flat 2-layer FR-4 PCB whose RHCP comes from a **dual quadrature feed** (an
> etched branch-line / 90° hybrid coupler driving two orthogonal inset feeds), **not**
> from corner truncation. It supersedes both the dropped aperture-coupled air-gap concept
> (no air gap, slot, probe, aluminium, standoffs, or second board) and the earlier
> truncated-corner single-feed patch. Work lives on the `patch_antenna_research` branch.
>
> This file was the forward-looking migration plan; it is now kept as **as-built design
> notes** — the reference several code docstrings point at. Section numbers §0/§2/§5 are
> stable anchors for those links.

Target: 869.52 MHz, ~1.6 mm FR-4 (εr 4.3, tanδ ~0.02), single 2-layer board. λ₀ ≈ 344.8 mm.
The design is optimised for **wide-beam coverage** (AR and RHCP gain held over an elevation
cone), not boresight gain — it is the no-tracking BACKUP antenna behind the tracked helical.

---

## 0. Geometry parameter object — `PatchParams`
The whole design is one frozen dataclass ([src/params.py](../src/params.py)) so it threads
through `build_full_sim` / the optimiser / post-processing without long positional signatures
and pickles cleanly into the `ProcessPoolExecutor` workers (a frozen dataclass of plain floats
survives the `spawn` start method):

```python
@dataclass(frozen=True)
class PatchParams:
    W_mm:        float   # square patch side
    cpl_arm_mm:  float   # coupler arm length (~λg/4)
    cpl_w50_mm:  float   # 50 Ω line width   (shunt arms + I/O)
    cpl_w35_mm:  float   # 35.36 Ω line width (Z0/√2 through arms)
    inset_x_mm:  float   # inset depth of the x-edge feed
    inset_y_mm:  float   # inset depth of the y-edge feed
    sub_hw_mm:   float   # ground/substrate half-width (smaller → broader beam)
```

`from_dict()` (partial dicts take config seeds) + `with_()` (`dataclasses.replace`) let the
optimiser sweep one field at a time. **The two feed lines are equal electrical length by
construction** (`dual_feed_layout` derives them from the coupler/patch geometry), so there is
**no `feed_len_mm` parameter** — it was removed as a dead degree of freedom.

---

## 1. File map (as-built)
| File | Role |
|------|------|
| [src/params.py](../src/params.py) | `PatchParams` + `default_params()` from the config seeds. |
| [config.py](../config.py) | FR-4 block, `substrate_kappa`, `mesh_res`, `SimBox`, coupler/feed seeds, coverage cost weights (incl. `F_RES_*` resonance penalty), grid-search params (`GRID_W_FRAC`, `GRID_ARM_MM`, `N_CONFIRM`, `NrTS_screen`), FDTD/parallel machinery. |
| [src/geometry.py](../src/geometry.py) | `notched_square_polygon`, `branch_line_rects`, and `dual_feed_layout(p)` — the single source of truth for every copper coordinate, shared by the model and the KiCad export. |
| [src/model.py](../src/model.py) | `build_full_sim` (active): offset board centred in the domain, patch + coupler + 2 L-feeds, `AddMSLPort` input, `AddLumpedElement` R=50 isolated termination, PML_8, mesh halos. `build_patch_sim(stage='single')` (Stage-1 single-feed, retained for the Stage-1 test). `_Tee`. |
| [src/optimizer.py](../src/optimizer.py) | Persistent pool, `_run_batch` (dynamic threads, `as_completed` timeout + `_rebuild_pool`), coverage `_cost` + coarse `_screen_cost`, the **2-D (W × coupler-arm) grid screen → full-fidelity confirm** search (`_run_search`), `_run_sim_worker` coverage metric. |
| [src/metrics.py](../src/metrics.py) | `axial_ratio_db`, `s11_db`, `cp_center_freq`, `failure_result`, `ar_beamwidth_deg`, `worst_ar_over_cone`, `min_gain_over_cone` — shared by worker and final run. |
| [src/postproc.py](../src/postproc.py) | S11 / AR-vs-f sweeps, far-field, coverage cuts, VTK, `results.json`, summary. |
| [src/kicad_export.py](../src/kicad_export.py) | One 2-layer board re-derived from `dual_feed_layout`: F.Cu = patch + coupler + feeds + stubs, B.Cu = ground, edge-launch SMA + isolated-port R/via markers. |
| [src/plotting.py](../src/plotting.py) | All figures, incl. AR-vs-θ and gain-vs-θ coverage plots. |
| [run.py](../run.py) | `warm_start` / `reuse_best` / `resolve_dimensions`, run-mode dispatch, isolated post-processing child, logging/ETA. |
| [tests/](../tests) | Standalone harnesses, run as `python tests/<name>.py`. Stage gates: `stage1_single_feed`, `stage2_coupler`, `stage2_dual_feed`, `stage3_optimizer`. Tools: `tool_build_inspect`, `tool_coupler_circuit`, `tool_show_geometry`. Shared `_bootstrap` does openEMS DLL discovery + puts the project root on `sys.path`. |

---

## 2. Branch-line coupler — the RHCP mechanism
A branch-line hybrid is a square ring of four λg/4 arms: the two **through** arms are
**Z0/√2 = 35.36 Ω**, the two **shunt** arms are **Z0 = 50 Ω**. `branch_line_rects` builds the
four arms as F.Cu rectangles; `dual_feed_layout` places the ring and routes the feeds.

**Locked topology** (empirically confirmed by `tests/stage2_coupler.py`, then hard-coded):
input = **BL**, isolated = **BR**, outputs = **TL** (−90°, leads) and **TR** (−180°, lags).
`branch_line_rects` is called with `w_h = cpl_w50_mm` (horizontal arms = 50 Ω) and
`w_v = cpl_w35_mm` (vertical arms = 35.36 Ω), so input→isolated runs along a 50 Ω shunt arm
and input→through along a 35.36 Ω series arm — the standard hybrid.

**Seeds at 869.52 MHz, 1.6 mm FR-4, εr 4.3** (Hammerstad; the optimiser fine-tunes `cpl_arm_mm`):

| Quantity | Value |
|---|---|
| λ₀ | 344.8 mm |
| 50 Ω line: width, λg/4 | **3.1 mm**, ~47.7 mm |
| 35.36 Ω line: width, λg/4 | **5.3 mm**, ~46.6 mm |
| coupler ring | **~47 × 47 mm** |

The widths `cpl_w50_mm`/`cpl_w35_mm` are **not swept** (they are self-consistent in-sim with the
modelled εr). The optimiser's grid sweeps **`W_mm` and `cpl_arm_mm`** — the two coupled
resonance/AR levers (`cpl_arm_mm` shifts resonance ~−18 MHz/mm); `inset_*` and `sub_hw_mm` are
held at the seed. The single arm length is shared by the 50 Ω and 35.36 Ω arms even though their
λg/4 differ by ~1 mm — a known small phase-balance limitation.

**Input excitation — `AddMSLPort`** (not a lumped port): spans ground (z=0) to strip
(z=substrate_thickness) over the 50 Ω input stub; `prop_dir` along the stub, `exc_dir = 'z'`.
The MSL port **self-computes Z_ref/β** — `s11_db(port.uf_ref, port.uf_inc)` and `Zin =
uf_tot/if_tot` work with no fixed-50 Ω divide. It needs **≥5 mesh lines along the propagation
length** plus the transverse halo; the stub is `INPUT_STUB` long and `Feed_R`-terminated so the
board stays finite (nothing crosses the NF2FF surface).

**Isolated-port termination — lumped resistor:**
```python
res = CSX.AddLumpedElement('R_iso', ny='z', caps=True, R=config.feed_R)
res.AddBox(start=[ix, iy, 0], stop=[ix, iy, z])   # strip-to-ground, fine halo at [ix,iy]
```
On the board this is one 50 Ω 0603 SMD resistor + a ground via.

**Handedness:** TL (leading) → LEFT(−x)/E_x, TR (lagging) → BOTTOM(−y)/E_y gives **RHCP at +z**.
This is **self-checking** — the worker computes `is_rhcp` from `E_cprh`/`E_cplh`, `_cost` applies
a hard wrong-hand gate, and the final summary prints `SWAP feeds` if it ever comes out LHCP.

---

## 3. Optimiser — grid search + two-tier confirm + coverage cost
**Search (`_run_search`)** — replaces the old sequential `W→I→C→W2→GP` coordinate descent, which
could not navigate the coupling between the two resonance levers: run `20260606_052114` kept a
**+14.9 MHz** design because Phase W and Phase C tuned `W` and `cpl_arm` in *separate* phases and
never visited their joint sweet spot. Two stages instead:

| Stage | What | Fidelity |
|---|---|---|
| **GRID** | one **independent 2-D grid** over `W_mm` (`GRID_W_FRAC`) × `cpl_arm_mm` (`GRID_ARM_MM`) — the two coupled resonance/AR levers; `inset_*` + `sub_hw_mm` fixed at the seed | **`NrTS_screen`** (cheap; resonance + S11 reliable, AR **not**) |
| **CONFIRM** | the **best W per arm** (≤ `N_CONFIRM`, ranked by `_screen_cost`) re-run; the full `_cost` picks the winner | **`NrTS_opt` (= `NrTS_final`)** |

Independent (no inter-phase barrier → fewer waves), AR-diverse (one candidate per arm), and
~2-3× faster than the old 25-sim sweep. The **ground-plane sweep is dropped** — the coupler
footprint pins the board near ~178 mm, so it was degenerate.

**`_screen_cost`** (GRID ranking): resonance + S11 (+ soft wrong-hand) **only** — the razor AR is
not trustworthy at `NrTS_screen`, so it is judged solely at CONFIRM.

**Coverage `_cost`** (CONFIRM ranking; lower is better), all at f_target:
- **resonance**: *no* penalty within ±`F_RES_DEADBAND_MHZ` (1.5 MHz), then a linear ramp on a
  `F_RES_SCALE_MHZ` (3 MHz) scale — **strong enough to actually centre 869.52 MHz**. (The old
  `|Δf|/fc` form made a 16 MHz miss cost ~0.06, so resonance was ignored — the run-1 root cause.)
- reward **AR≤3 dB elevation beamwidth** (normalised to `AR_BW_REF` = 80°, capped);
- penalise **worst AR over the 0–`COVER_CONE_DEG`(45)° cone** above `AR_MAX_DB`;
- penalise **min RHCP gain over the cone** below `GAIN_FLOOR_DBIC` (2 dBic) — a floor, not a max;
- keep **S11 ≤ −10 dB**; **wrong-hand hard gate** (a wrong-handed candidate can never win).

**Opt = final fidelity.** `NrTS_opt` was raised to `NrTS_final` (150 000): the razor AR/beamwidth
did not survive coarse→final (run-1: AR 2.5 dB / BW 36° at 120 k vs 3.4 dB / 0° at 150 k for
identical dims), so CONFIRM now scores on the SAME fidelity the final run reports.

**AR is band-robust:** the worker evaluates AR at `f_target` **and** `f_target ± AR_MARGIN_MHZ`
(1.5 MHz) and selects on the **worst** value. The RHCP gain floor is computed from the **RHCP
component `E_cprh`** (not total field), matching post-processing exactly.

---

## 4. Post-processing & results
- `_axial_ratio_sweep` — AR vs frequency; boresight AR + RHCP sense reported at **f_target**.
- `_coverage_cuts` — `CalcNF2FF(theta=0..90° step 2°, phi=[0,45,90,135])` at **f_target**: AR per
  (θ,φ), RHCP partial gain per (θ,φ); reports **AR≤3 dB beamwidth** (worst over φ), **worst AR over
  the cone**, **min RHCP gain over the cone**. θ=0 is taken from the next ring (the CP basis is
  singular on-axis).
- `_farfield` — 2D/3D pattern + authoritative `Dmax`, also at **f_target** (the operating point).
- `results.json` — the `PatchParams` fields (so the KiCad export re-derives the same board) plus
  `f_res_MHz`, `s11_at_ft_dB`, `ar_boresight_dB`, `rhcp`, `ar3_beamwidth_deg`, `worst_ar_cone_dB`,
  `min_gain_cone_dBic`, `Dmax_dBi`. The optimiser and final run share the `metrics.py` helpers so
  they agree.

---

## 5. Build stages & validation gates (as-built)
**Stage 1 — single-feed square patch.** ✅ `build_patch_sim(stage='single')`, driven by
`tests/stage1_single_feed.py`. Gate met: S11 ≤ −10 dB near f_target, resonance within ±3 MHz, Dmax
~5–6 dBi. De-risked the patch + MSL-port mechanics before the coupler (RHCP not expected here).

**Stage 2 — full dual-feed; verify RHCP.** ✅ `build_full_sim`, driven by `tests/stage2_dual_feed.py`
(coupler S-params first checked in isolation by `tests/stage2_coupler.py`).
Gate met: boresight AR ≤ 3 dB, **RHCP confirmed**, S11 ≤ −10 dB, isolated port absorbing.

**Stage 3 — optimise for coverage.** ✅ implemented — the 2-D grid screen + two-tier confirm
search + coverage cost above (`run.py` with `single_sim_only=False`). Machinery smoke-tested by
`tests/stage3_optimizer.py` (tiny grid at tiny NrTS). NOTE: the first full run
(`20260606_052114`) used the OLD coordinate-descent + the broken resonance cost and landed
+14.9 MHz off — superseded by this grid search; not yet re-run.

**Stage 4 — two-layer KiCad export.** ✅ `src/kicad_export.py` — F.Cu patch+coupler+feeds, B.Cu
ground, Edge.Cuts, edge-launch SMA footprint, isolated-port SMD-R footprint + ground via.

**Standing risks:** coupler amplitude/phase balance on lossy FR-4 (the #1 AR limiter — validate
with `tests/tool_coupler_circuit.py` / `stage2_coupler.py`); board real-estate (~47 mm ring + ~83 mm patch
+ GP); feed mutual coupling (co-tune the insets).

---

## 6. Correctness-critical implementation notes
Things that silently corrupt CP results if wrong (each hardened in the current code):
- **Patch edges must be meshed explicitly.** `AddEdges2Grid` ignores `Polygon` primitives
  (openEMS automesh only hints POINT/BOX), so `build_full_sim` adds triple-line halos at every
  patch edge. Without them the two feedless edges get ~5–13 mm cells while the feed edges get
  ~1 mm — an asymmetric mesh that splits the E_x/E_y resonances and breaks the 90° quadrature.
- **PML clearance.** The board is offset into the −x/−y quadrant, so the domain is **centred on
  the board** and `SimBox` (600³ mm) gives ≥ λ/4 of air to the inner PML on every face. Too-close
  PML clips the finite-GP back-lobe / reactive near-field and biases Dmax + wide-angle AR.
- **Opt ↔ final consistency.** Both score AR/gain/beamwidth at **f_target** with the same
  `metrics.py` helpers, gain from `E_cprh`, AR band-robust over ±`AR_MARGIN_MHZ`.

> **openEMS contract:** `AddMSLPort` self-computes `Z_ref`/`β` and needs ≥5 propagation-direction
> mesh lines; `AddLumpedElement(ny='z', caps=True, R=50)` is the isolated-port termination;
> `AddEdges2Grid` does **not** grid `Polygon` primitives — add patch-edge lines by hand.

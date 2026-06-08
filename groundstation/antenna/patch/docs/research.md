# Patch Antenna Research — 869.52 MHz RHCP Ground Station

Working notes and findings for the SPROG telemetry ground-station patch antenna.
Synthesised from openEMS simulation data in this repo, multi-source web research,
and the review paper *Yahya et al., "LoRa Microstrip Patch Antenna: A
comprehensive review," Alexandria Engineering Journal 103 (2024) 197–221*
(doi:10.1016/j.aej.2024.06.045) — the PDF in the repo root.

> **TL;DR — current design (2026-06-08, branch `patch_antenna_SF`).** A flat single
> 2-layer **NP-140F (FR-4-class)** PCB patch, RHCP from a **single-feed corner-truncated**
> patch (two diagonally-opposite corners chamfered), fed by ONE inset microstrip to one
> edge-launch SMA — **no coupler, no termination resistor**, 160×160 mm, ~€30–60/5. It is a
> **no-tracking wide-beam backup** behind the tracked helical; the 10 km link closes with
> large margin, so coverage + robust RHCP matter more than gain. Validated in openEMS at the
> un-tuned seed: **η_rad 28 %, realised gain +0.8 dBic, directivity 6.6 dBi, RHCP**; AR is
> ~6 dB at the seed and is tuned to ≤3 dB by the W×truncation optimiser.
>
> **How we got here (and what was wrong before):** truncated single-feed on FR-4 (broken
> AR 7.1) → explored air/aperture/probe (dropped: manufacturability) → **dual-feed
> branch-line coupler** (chosen 2026-06-04 for εr-robust CP, built + simulated) → **coupler
> RETIRED 2026-06-08** when a power decomposition showed it dumps **~64 % of accepted power
> into its isolated-port resistor** (realised gain −9.6 dBic) → **back to single-feed**, which
> deletes that sink and recovers ~10 dB of realised gain. The dual-feed material in §2–§6/§9
> below is kept as history and flagged ⌗.

---

## 0. Findings (validated in sim, 2026-06-07/08)

1. **The dual-feed coupler radiated only ~3 %.** A 150k power decomposition (iso-resistor
   voltage probe; energy balance closes to 100 %): of accepted power, **63.7 % → isolated-port
   resistor, 33.2 % → FR-4 dielectric, 3.1 % → radiated** → realised gain **−9.6 dBic** despite a
   good **−11 dB S11**. The coupler routes the patch's feed-point mismatch into the iso resistor,
   which a good *input* match hides. That resistor is a **structural sink of the coupler topology** —
   not a bug, and not removable while the coupler stays.
2. **Directivity was a units bug.** openEMS `nf2ff.Dmax` is the **LINEAR** directivity ratio, not
   dBi; the repo reported it raw, under-reading directivity by 10·log10 (≈ +2 dB) — true boresight
   directivity is ~5.9–6.6 dBi, not the "3.9 dBi" once reported. Proven against a lossless half-wave
   dipole (Dmax 1.656 → 2.19 dBi == textbook 2.15). Fixed repo-wide via `metrics.directivity_dbi`;
   permanent calibration test = `tests/stage0_dipole_calibration.py`. **Every "dBic" in §3–§6 that
   came straight from `Dmax` is a linear ratio, ~2 dB below the true directivity.**
3. **The efficiency method is trustworthy.** η_rad = Prad/P_acc, η_tot = Prad/P_inc, realised gain
   = directivity + 10·log10(η_tot). The lossless dipole gives η ≈ 100 %, so a low η on the patch is
   PHYSICAL (FR-4 dielectric + feed mismatch), NOT an NF2FF normalisation artefact.
4. **Single-feed wins on realised gain.** No iso resistor → the 64 % can't be dumped. Validated on
   the same FR-4 board: **η_rad 3 %→28 %, realised gain −9.6→+0.8 dBic, RHCP** (truncate the bottom-
   left + top-right diagonal → RHCP at +z). Cost: single-feed AR is εr/fab-sensitive — now tractable
   because NP-140F's εr is datasheet-known. **AR at the un-tuned seed ≈ 6 dB; the W×truncation
   optimiser centres the AR null on f_target** (truncation Δ sets the mode-split, W sets resonance).
5. **Gain is EFFICIENCY-limited, not aperture-limited.** Directivity (~6.6 dBi) is already fine; the
   antenna loses ~5 dB to FR-4 dielectric. So the gain levers are efficiency, not board size:
>   | Lever | Δ realised gain | Cost / tradeoff |
>   |---|---|---|
>   | **3.2 mm substrate (1.6→3.2)** | **+1.5–2 dB** (+ wider AR) | ~free (stock thickness), re-tune only — **best bang/buck** |
>   | Air/foam gap (~10–25 mm) | **+3–4 dB** (η → ~85 %) | a 3-D assembly (the manufacturability reason it was dropped) |
>   | Stacked parasitic patch | +1–2 dB (+ BW) | adds a layer/spacer |
>   | Board 160→200 mm | **only ~+0.5 dB** directivity | *narrows the beam* — trades coverage; diminishing past ~0.6 λ (§4) |
>   | Lower-loss laminate (Rogers) | +3–4 dB | over budget |
>   | 2×2 array | +6 dB | needs >250 mm + a feed network — breaks the size/coverage budget |
>
>   Every *directivity* lever (board, stacking, array) narrows the beam (fights the coverage role);
>   every *efficiency* lever (thickness, air, laminate) raises gain *without* narrowing it — prefer those.

## 1. Project context

| Fact | Value |
|------|-------|
| Operating frequency | 869.52 MHz (EU 868 ISM; g3 high-power sub-band 869.4–869.65 MHz), λ₀ ≈ 345 mm |
| Polarisation needed | **RHCP** — the rocket carries an onboard **RHCP quadrifilar helix**, so RHCP↔RHCP is a matched pair (0 dB polarisation loss). LHCP would be a deep mismatch. |
| Role of this antenna | A **fixed, wide-beam RHCP** receiver. A separate **tracked high-gain helical** already handles the primary link, so this patch should *complement* it (wide coverage, robust CP) — not duplicate it with a high-gain pencil beam. |
| Why CP at all | A spinning/tumbling vehicle rotates its onboard antenna; matched CP avoids the deep polarisation fades that linear↔linear suffers. (With an RHCP rocket, same-sense CP is the only correct choice.) |

> ⚠️ **Sense matters most.** RHCP↔RHCP = matched; RHCP↔LHCP = 20+ dB loss. The
> onboard QFH is **RHCP — confirmed by the team**, so the patch *and* the ground
> helical must both be RHCP. The patch's sense is set by the CP perturbation (slot
> orientation / truncated diagonal) and is trivial to flip in design; the **helix's
> sense is fixed by its winding**, so treat the helix as the reference and match the
> patch to it. *(The repo does not yet record the helix winding sense — the helical
> table has none and the QFH section is a stub, issue #43 — confirm and document
> it.)* A mirrored patch layout yields a perfect *LHCP* antenna, deaf to the rocket.

---

## 2. Microstrip patch fundamentals

- A patch resonates when its length ≈ λ/2 in the substrate; higher permittivity
  εr shrinks it (≈ 1/√εr), lower-loss raises efficiency. FR-4 here: εr ≈ 4.1,
  tanδ ≈ 0.013, h = 1.6 mm → patch ≈ 83 mm. Air (εr ≈ 1) → patch ≈ 165 mm.
- Feed options: inset microstrip, coaxial **probe**, proximity-coupled,
  aperture-coupled. The repo's model uses a z-directed (probe-like) feed at an
  inset point on the −y edge ([../src/model.py](../src/model.py)).
- The **ground plane** separates two worlds: the radiating side (above) and the
  feed/electronics side (below). Keep all coax/connectors/radio **below** it.

### Circular polarisation — three ways to make it
| Method | AR bandwidth / robustness | Efficiency | Note |
|--------|---------------------------|------------|------|
| **Single-feed corner truncation** (**CHOSEN**) | ~0.5–2 % on thin substrate; tight on 1.6 mm FR-4 | **high — no loss network** | CP from one mode-split; AR is εr/fab-sensitive but tunable with a known εr (NP-140F). All accepted power goes to the patch. |
| Single-feed slot/U-slot variants | ~2–7 % | high | lateral AR improvement only |
| ⌗ **Dual-feed 90° hybrid** (branch-line coupler) — *retired* | ~6–30 %+, tolerance-proof | **LOW — iso resistor sinks the mismatch** | quadrature enforced by copper, but its isolated port burned **~64 %** of accepted power (§0) → realised gain −9.6 dBic. Robust CP, terrible gain. |
| **Sequential rotation** (array) | >15 %, excellent | high | cross-pol cancels by geometry; needs many elements + a feed network |

**The single-feed vs coupler trade (settled §0):** the coupler buys εr-robust CP but pays
it with a structural efficiency sink (its isolated-port resistor absorbs the patch
mismatch → −9.6 dBic). Single-feed has no such sink (→ +0.8 dBic at the seed) but its CP is
εr/fab-sensitive: the AR≤3 dB window width ∝ 1/Q, and thin lossy FR-4 is high-Q, so a
~1–2 MHz resonance drift slides the operating point off the AR null. **Mitigations that
make single-feed viable now:** (1) NP-140F's datasheet-known εr (±0.1) lands resonance
predictably; (2) FR-4's loss actually *lowers* Q and *widens* the AR window vs Rogers;
(3) the W×truncation optimiser centres the null on f_target; (4) 3.2 mm substrate (a gain
lever anyway) widens AR further. Per-unit cold-test still recommended.

---

## 3. The FR-4 baseline and its two failures

The repo's optimised FR-4 design (W=83.16, Δ=6.96, y_inset=5.81 mm, 375 mm GP)
reported, at the final high-fidelity sim:

- **S11 ≈ −19 dB** (good match), **Dmax ≈ 5.8 dBic**.
- **AR = 7.1 dB at f_target, AR≤3 dB bandwidth ≈ 0 MHz** → CP effectively broken.

Two root causes:
1. **Dielectric loss → low gain.** FR-4 tanδ burns ~40–55 % of input power as
   heat (efficiency ~45–60 %), capping realised gain at ~4.4–5.8 dBic vs the
   ~6–7 dBic a patch could give.
2. **Razor-thin AR → broken CP.** Single-feed corner truncation on 1.6 mm FR-4
   has ~0 MHz of usable AR bandwidth.

### Optimiser pitfall (fixed in this repo)
The optimiser was being *misled*: it judged AR from an under-converged sim where
resonance landed on f_target (AR looked ~2 dB), but the converged final run drifted
and revealed AR ≈ 7 dB. Same geometry, same AR formula, same cone — the difference was
FDTD convergence on a ~0-bandwidth AR null.

> **Optimiser (current — single-feed).** A **2-D grid (patch side W × corner-truncation
> Δ) screen + full-fidelity confirm** (config.py: `GRID_W_FRAC × GRID_TRUNC_MM`, `N_CONFIRM`).
> W sets resonance, Δ sets the CP mode-split, and the AR null is only centred on f_target when
> both are right together (a sequential coordinate descent can't navigate that coupling). The
> AR is judged only at the full-fidelity confirm (`NrTS_opt = NrTS_final = 150000`; screen at
> `NrTS_screen = 60000` — resonance/match converge there, the razor AR does not). Selection:
> a deadband+ramp resonance penalty (`F_RES_*`), worst AR over f_target ± `AR_MARGIN_MHZ`,
> AR≤3 beamwidth reward, a gain floor, and a **radiation-efficiency reward (`W_EFF`)** so the
> optimiser keeps designs that actually radiate. The board is locked at 160 mm for wide-beam
> coverage (not swept). *(Historical: the original sequential `W→I→C→W2→GP` descent and a
> coupler-arm grid are retired with the coupler.)*

---

## 4. Gain physics & the ground-plane size law

Gain ultimately needs **aperture**. A single patch is directivity-limited to
~6–7 dBic; on FR-4 you only keep ~4.4–5.8 after losses. You cannot buy big gain
on one small board — only recover efficiency.

**Ground-plane size has sharply diminishing returns** (simulated, legacy single-feed
FR-4; the *D** column is the raw `Dmax` LINEAR ratio — true directivity is ~2 dB higher,
see §0.2 — but the SHAPE of the curve is what matters here):

| GP edge | board/λ₀ | D* (Dmax ratio) |
|--------|---------|------|
| 150 mm | 0.43 | 4.4 |
| 250 mm | 0.72 | 5.3 |
| 300 mm | 0.87 | 5.5 |
| 350 mm | 1.01 | 5.8 |
| 375 mm | 1.09 | 5.8 |
| 400 mm | 1.16 | **5.5** (edge-diffraction ripple) |

The diminishing-returns LAW holds regardless of the units offset: ~+1 unit of directivity
over the whole 150→375 mm range, most of it by ~250 mm, then ripple past ~1 λ₀. **So a
bigger board is cost (and a narrower beam), not gain** — and for the 160→200 mm range the
user asked about, expect only ~+0.5 dB directivity while the coverage beam narrows. A patch
ground only needs ~0.5–1 λ for a clean pattern; realised *gain* is set by EFFICIENCY (§0.5),
not ground size.

---

## 5. Cost vs board size + laminate (the single-feed FR-4 route)

> **Board = 160×160 NP-140F, 2-layer 1.6 mm.** 160 mm (not larger) is deliberate for the
> wide-beam coverage role — a beamwidth-vs-ground sweep (`tests/board_sweep.py`, run on the
> dual-feed; re-confirm on the single-feed) showed the AR≤3 coverage beam *widens* as the GP
> shrinks (**160→52°, 170→40°, 180→36°, 190→28°**). The board is square and **centred** on the
> single-feed patch (~83 mm), so all four corners are clear (4× M3 holes). ⌗ The 160 mm figure
> and "coupler-limited floor" reasoning date from the retired dual-feed; the single-feed patch
> sets its own (smaller) floor (patch + margin), so 160 mm is now a coverage choice, not a floor.
> Going to 200 mm buys ~+0.5 dB directivity but narrows the beam (§0.5/§4) — only do it if you
> are trading coverage for gain.

PCB price is driven by **area** with discrete tier jumps. JLCPCB: ≤100×100 mm
hits a ~2 USD promo tier; a per-50 cm² surcharge starts above **650 cm²**
(≈ a 255 mm square) — so the **160×160 board (256 cm²) is comfortably cheap-tier**
(~25–45 €/5 incl. ship+VAT to the EU).

| Board | D* @1.6 mm (Dmax ratio) | 5× JLCPCB (incl. ship+VAT) | 5× Aisler (EU) |
|------|-------------|----------------------------|----------------|
| 100×100 | ~3.7 | ~15–25 € | ~54 € |
| 120×120 | ~4.0 | ~25–40 € | ~72 € |
| 150×150 | 4.4 | ~35–55 € | ~104 € |
| 170×170 | ~4.6 | ~45–70 € | ~129 € |
| **160×160 (CHOSEN)** | — | **~25–45 €** | ~115 € |
| *375×375 (old)* | 5.8 | *~140 €* | — |

(D* = the raw `Dmax` linear ratio from the legacy single-feed sweep, ~2 dB below true
directivity — §0.2. The single-feed patch's directivity is ~6.6 dBi; realised gain depends
on EFFICIENCY, not board size.)

Within the allowed range, **directivity moves <1 dB while cost 2–3×** → pick small.
The real performance comes from the **substrate (3.2 mm or air)**, not size.
On 1.6 mm the highest-leverage cheap change is **3.2 mm FR-4** (+~1 dB and wider
AR), available only at PCBWay (JLCPCB caps at 2.0 mm). *Mid-loss "FR-4" grades
(S1141/S1000H) are not low-loss — they're the default stock — so they buy ~0 dB;
real low-loss means Rogers/I-Speed/S7-series, which break the budget.*

**Laminate choice — NP-140F over stock FR-4 (predictability, not loss).** The build uses
**Nan Ya NP-140F** (FR-4-class, Tg 135 °C), not generic stock FR-4. The reason is NOT loss
(NP-140F tanδ ~0.013 vs stock ~0.0155 buys ~0.3–0.5 dB — irrelevant against the 22–30 dB
link margin, exactly the "mid-loss FR-4 ≈ 0 dB" point above). It is **εr predictability**:
a resonant patch lands where εr says it will, and NP-140F is datasheet-specified at
**εr 4.0–4.2 (±0.1)**, whereas stock FR-4 is an unspecified ~4.2–4.6 grab-bag (the actual
stock part, KingBoard **KB-6164**, measures ~4.6 / 0.0155 @ 1 GHz). Known + tighter εr →
~±10 MHz batch resonance scatter vs ~±20 MHz on KB-6164, i.e. boards that hit 869.52 MHz
without per-unit tuning. At equal cost with the laminate **guaranteed if specified**,
NP-140F is the pick — design εr = 4.15 @ 870 MHz. ⚠️ **Confirm the fab actually supplies
NP-140F at 160 mm**: JLCPCB's cheap tier stocks KingBoard/Shengyi (KB-6164-class), so a
bare "FR-4" order silently gives εr ~4.6 and the patch lands ~25 MHz low.

### On-board performance levers (the single-feed FR-4 route — CURRENT)
On the single etched FR-4 board (one SMA), these recover *efficiency* (the gain-limiter,
§0.5); the 3.2 mm option also helps the single-feed AR robustness:

| Lever | Effect on realised gain | Note |
|-------|--------|------|
| **3.2 mm substrate** (1.6→3.2 mm) | **+1.5–2 dB** + wider/robuster AR | **biggest lever**; PCBWay (JLCPCB caps at 2.0 mm). Re-tune after. |
| **Soldermask keep-out over the patch** | +0.1–0.3 dB | *free*; makes the build match the bare-PEC sim (already in kicad_export) |
| **Re-optimise W/Δ/inset** | recovers match / AR | *mandatory* after any stackup change |
| **2 oz copper** | +0.1–0.2 dB | cheap insurance for feed/edges |
| **Lower-loss laminate** | +3–4 dB | ⚠️ real low-loss = Rogers/I-Speed (over budget); stock "FR-4" grades buy ~0 dB |

Bigger jumps need aperture / extra assembly (§0.5): air/foam gap (+3–4 dB), stacked
parasitic (+1–2 dB), arrays (>250 mm). The §6 menu below is the historical exploration of
those — the chosen build is this single etched FR-4 board (3.2 mm if more gain is wanted).

---

## 6. Design space for RHCP + gain (exploration menu — historical)

> ⌗ **This is the explored option menu, not the current build.** The CHOSEN design is the
> flat single-feed corner-truncated FR-4 patch (§0/§9). The rows below are the gain/CP
> options weighed along the way; the practical gain levers for the current build are in §0.5
> (3.2 mm substrate first; air gap if more is needed). "Gain (dBic)" here is rough/projected.

| Design | Gain (dBic) | RHCP robustness | Size @ 869 MHz | HPBW | Cost (5×) | Verdict |
|--------|-------------|-----------------|----------------|------|-----------|---------|
| **FR-4 single-feed, 1.6 mm** | ~+1–3 realised | tunable (known εr) | 83 mm patch / 160 board | ~70° | cheap | **CHOSEN** (§9) — efficient, RHCP from truncation |
| FR-4 single-feed, 3.2 mm | ~+3–4 realised | wider AR | same, 3.2 mm | ~70° | cheap | best cheap gain upgrade (§0.5) |
| ⌗ Dual-feed branch-line coupler | **−9.6 realised** | excellent | 160 board | ~52° | cheap | RETIRED — iso resistor sank 64 % (§0.1) |
| Air patch, single feed | 7–8 directivity | good (~25–30 MHz AR) | 165 mm patch, ~300 mm gnd, 25 mm tall | ~65° | ~30–60 € | gain option (3-D assembly) |
| Stacked CP patch | 8–9.5 | excellent (6–15 %) | +taller (40–55 mm) | ~55° | ~60–150 € | +1–2 dB, adds a layer |
| 2×2 seq-rotation array (air) | 11–12.5 | excellent (>15 %) | ~0.45 m panel | ~40° | ~80–150 € | gain path; needs aiming + feed net |
| 2×4 / 4×4 array | 14–17 | excellent | 0.5–1 m+, heavy | ~20–30° | ~200–400 € | **avoid** — duplicates the helical |
| *+ dielectric/FSS superstrate* | +2 to +6 | CP-safe (symmetric) | +~170 mm tall | narrower | +5–30 € | single-element gain boost |
| *+ cavity-backed ground* | +2–3, **F/B +12–22 dB** | improves AR | shallow box | — | +10–25 € | great for ground multipath |
| Short-backfire / patch-cup | 13–15 | good | ~0.3–0.7 m | ~30° | ~20–60 € | pointed only |

### Why air is the key unlock
Replacing FR-4 with an air/foam gap does two things at once:
1. **Efficiency → gain:** lossless dielectric → ~90–95 % efficiency → the ~2.5–
   3.5 dB lost to heat now radiates → ~7–8 dBic.
2. **Lower Q → robust CP:** a thick (~0.06–0.08 λ₀ ≈ 20–28 mm) low-ε gap drops Q
   ~10×, widening the AR≤3 dB window from ~0 to **~25–30 MHz** — finally
   tolerant to fab/εr/drift.

Trade-off: the air patch is ~2× larger (εr≈1) and a real 3-D assembly. The
straight probe through a 25 mm gap is very inductive → use an **L-probe** (probe
rises ~18 mm then bends ~35 mm horizontally under the patch with a ~3–5 mm
capacitive gap) or a U-slot to cancel the inductance.

### Sequential rotation (for arrays)
Rotate elements 0/90/180/270° *and* feed with matching phase: wanted RHCP adds
coherently, unwanted LHCP + per-element cross-pol spread 90° apart and **cancel**.
CP becomes a property of array *geometry*, so even mediocre single-feed elements
give boresight AR <1 dB and >15 % AR bandwidth. The robust way to do array CP.
Caveat: cleanest on boresight, softer off-axis; the corporate feed's phase
offsets are frequency-dependent (here that's tolerance margin, not bandwidth).

### Feed options (single air patch)
Gain is ~7–8 dBic for **all** of these — the feed sets the **match** and **AR
robustness**, not gain. A straight 25 mm probe is very inductive (poor S11); every
option below cancels that and/or improves CP. Ranked by mechanical simplicity
(★ = simplest, ★★★★ = most involved):

| Feed | RHCP via | AR robustness | Match / BW | Mech. | Best when |
|------|----------|---------------|-----------|-------|-----------|
| Straight coax probe *(prior design)* | truncation | good (air) | **poor at 25 mm gap** | ★ | only with a short (~10 mm) gap |
| **Straight probe + series chip cap** | truncation | good | **good, tunable** | ★ | minimal mechanics + a tuning knob |
| Capacitive-disc / top-hat probe | truncation | good | good | ★★ | no solder to the floating plate |
| Probe + U-slot in patch | truncation / U-slot | good, wider | good + wider BW | ★★ | want more BW, simple feed |
| L-probe (modified) *(Cheng-Lim-Phua)* | truncation | good, AR decoupled | **best single-feed BW** | ★★★★ | max BW, don't mind fiddly |
| Proximity-coupled microstrip | truncation | good | good, wide | ★★★ | clean, but adds a layer |
| Aperture-coupled (slot), single feed | truncation + slot | good | good, wide | ★★★ | want the simplest *patch* (bare plate) |
| Aperture dual-slot + 90° hybrid | quadrature (network) | **excellent** | excellent | ★★★★ | bulletproof RHCP, no probes |

**Pick (historical menu):** these probe / aperture routes were the alternatives weighed
before the planar route was chosen. The **shipped feed is the etched inset microstrip**
on the corner-truncated single-feed patch (§5, §9) — no probe, no extra layer, all copper
on one face, reproducible by etch alone. The probe/aperture rows are kept only as the
exploration record.

### Patch geometry options
The radiator **outline shape is ~gain-neutral** (all ~6–8 dBic on air); it sets the
CP method, AR robustness, and size. Gain only rises with aperture (stacking /
parasitics / superstrate).

**Base outline**
| Shape | RHCP via | Gain | Note |
|-------|----------|------|------|
| Square + truncated corners *(plan)* | cut 2 opposite corners | ~7–8 | the standard |
| **Nearly-square rectangle, diagonal feed** | slightly a≠b (a/b≈1+1/Q) | ~7–8 | **simplest — no corner cuts** |
| Square + 2 corner tabs (additive) | add tabs | ~7–8 | same effect, additive |
| Circular disc + ellipticity / 2 indents / cross-slot | slight asymmetry | ~7–8 | more rotationally symmetric pattern |
| Annular ring | perturbed ring | lower | narrowband, no gain benefit |
| Triangle / pentagon | perturbation / inherent asymmetry | ≤ | compact / classic "wild" CP shape |

**Wider-AR perturbations** (only if single-feed AR comes out tight — unlikely on
air): asymmetric / unequal-arm cross-slot; half-E + parasitic (Li et al.);
asymmetric U-slot.

**Gain / BW add-ons** (the real gain levers short of an array): stacked parasitic
patch (+1–1.5 dB); coplanar gap-coupled parasitics (+1–2 dB); parasitic director
(+1–3 dB); dielectric/FSS superstrate (+2–6 dB, CP-safe if symmetric).

**Miniaturisation** (skip — 300 mm is fine): shorting-pin half/quarter patch (½–¼
size, CP harder, pattern tilts); meander/slot slow-wave; fractal boundary
(Koch/Minkowski/Sierpinski — lower efficiency).

**Ground / structure:** cavity/cup wall (+2–3 dB, big front-to-back improvement —
good for a ground station); EBG ring (surface-wave suppression — mostly for
thick/high-εr, not needed on air); DGS (niche).

**Exotic ("go wild"):** curl/spiral patch (inherent broadband CP, lower gain, needs
a reflector); metasurface-loaded patch; spidron fractal CP; a mini 2×2
sequential-rotation cluster as one element; magneto-electric (ME) dipole; DRA
(dielectric resonator instead of a patch).

**Pick:** a **nearly-square rectangle** (or truncated square) on the air gap — full
gain, clean single-feed RHCP, zero corner work. Circular-disc-with-truncation if
you prefer round. Add a stacked parasitic or superstrate only for >8 dBic; skip
miniaturisation and EBG (they fight the air-gap efficiency win).

---

## 7. Lessons from the literature

### From the AEJ 2024 LoRa-MPA review (Yahya et al.)
- **868 MHz patches are low-gain in practice:** the survey's 868 MHz designs
  cluster at **~1.5–5 dBi**, nearly all on FR-4 — consistent with our ceiling.
- **Single-feed CP is hard here:** it cites a truncated-corner + multilayer CP
  patch (with metamaterial gain boost, ~2 dBi) and a design stuck at **AR ≈
  7.2 dB** — the same failure mode as our baseline.
- **Substrate guidance:** for gain, choose **low permittivity + low loss
  tangent**; high-εr shrinks size but increases loss. (→ supports air/low-ε.)
- **Enhancement levers it catalogues** (useful if we ever stay on FR-4):
  - **EBG** (electromagnetic band-gap) ground structures — *suppress surface
    waves*, raising gain/efficiency on lossy/thick substrates; a 2×2 "SAM" EBG
    array improved a cited design.
  - **Metamaterial** (split-ring) and **dielectric/FSS superstrate** — gain.
  - **DRA** (dielectric resonator) — low loss, wide impedance BW (air/dielectric
    interface).
  - **Corrugation** (bull's-eye / leaky-wave) — high gain from a planar aperture.
- Tools used in the field: CST, HFSS, FEKO, ADS (we use openEMS — comparable
  FDTD). Target **SWR < 1.5** for the match.

### The adjacent goldmine: UHF RFID reader antennas (865–868 MHz)
EU UHF RFID is **865–868 MHz** — essentially our frequency — and RFID readers
overwhelmingly use **CP patch** antennas (typically dual-feed/hybrid or
truncated single-feed, ~6–9 dBic, often air/foam or thick substrate). These are
the most directly transferable real-world designs. GNSS (1.2–1.6 GHz) CP-patch
design *methods* also transfer directly.

### Design SOP — single-feed corner-truncated CP → air-gap L-probe
Grounded in Sharma & Gupta (1983), Balanis Ch.14, Cheng-Lim-Phua (2017), and the
RFID CP-patch literature (§10).

1. **Size the patch.** Air (εr≈1) → side ≈ λ₀/2 − fringing (~150–165 mm); ground
   ≥ ~0.7–1 λ₀. **Choose the gap height first:** thin = high Q = razor AR; a thick
   air gap (~20–25 mm, several % of λ) lowers Q — *that* is what buys usable AR and
   impedance bandwidth. This is the whole reason to go air.
2. **Set the perturbation.** Single-feed CP = splitting the TM10/TM01 modes into an
   equal-amplitude 90° pair at f₀. Design rule: **truncation area dS/S ≈ 1/(2·Q0)**,
   and **AR bandwidth ≈ 1/(√2·Q0)**. Estimate Q0 (low for a thick air gap) → compute
   the cut. Thick gap → cut **more** corner → more forgiving. Truncate the diagonal
   that yields **RHCP**.
3. **Place the feed.** Diagonal feed point for 50 Ω. For air, use an **L-probe**
   (vertical pin → horizontal arm under the patch). Cheng-Lim-Phua's trick: add an
   **extra bend** to the L-probe → an S11 matching knob that does *not* spoil AR
   (decouples match from polarisation).
4. **Tune AR, then match, then iterate:** (a) truncation so the split resonances
   straddle 869.52 MHz with the AR minimum at band centre; (b) L-probe height/arm
   for |S11|≤−10 dB without dragging AR; (c) re-check AR — widen the gap (lower Q),
   or escalate to stacked/parasitic/sequential only if single-feed AR is too tight.
5. **Sense-check RHCP** from the far field (E_R vs E_L) — the wrong diagonal gives
   LHCP and ~20 dB loss vs the rocket's RHCP helix. Verify before fabrication.
6. **Measure.** Targets from the air-gap analogues: **~7–8 dBic**, **AR<3 dB across
   869.4–869.65 MHz**, |S11|≤−10 dB; check AR over the **elevation cone (~75° 3-dB
   AR beamwidth)**, not just boresight — the rocket moves across the sky.

### Pitfalls (from the literature)
- **Narrow AR is the central single-feed weakness** (AR BW ≈ 1/(√2·Q0)). Fix from
  the start with a **thick air gap** to drop Q (what every air-gap RFID paper does).
- **Manufacturing sensitivity:** high-Q truncation is tiny and CP "is very sensitive
  to manufacturing errors." Air-gap/low-Q → bigger, more forgiving truncation.
- **Polarisation sense:** wrong diagonal = LHCP = ~20 dB loss. Lock sense in sim,
  re-verify on the physical part.
- **Match↔AR coupling:** a plain probe trades S11 against AR. Use the modified
  (extra-bend) L-probe for a near-independent match knob.
- **Air-gap mechanical stability:** gap height sets f₀, Q, AR *and* match — fix it
  rigidly (machined standoffs / low-loss foam); treat it as a tuned parameter.
- **Scaling 915→869:** the best L-probe analogue (Cheng-Lim-Phua) is ~915 MHz —
  scale linear dims by ~1.05× as a start, then re-optimise; don't copy verbatim.
- **Don't over-reach on bandwidth:** the telemetry channel is ~250 kHz; a clean
  single-feed air-gap patch (~864–870 MHz AR) is ample. Reserve stacking/sequential
  feed for if single-feed AR can't be centred reliably.
- **openEMS meshing:** mesh the air gap and the thin truncated corners finely and
  check AR convergence — under-meshed corners report *optimistic* AR (the exact trap
  that bit the FR-4 optimiser, §3).

---

## 8. EU 868 regulatory notes (CEPT/ERC 70-03; ETSI EN 300 220 / EN 302 208)
- **Telemetry channel:** **869.4–869.65 MHz** is the EU high-power SRD sub-band —
  **500 mW e.r.p. (27 dBm)** with **≤10 % duty cycle OR LBT+AFA**. 869.52 MHz sits
  squarely here. (The old "g3" letter label is from earlier ERC 70-03 editions;
  recent editions renumber, but the limits stand.)
- **RFID reuse band (design source, *not* your link):** **865–868 MHz**, ETSI
  **EN 302 208**, up to **2 W e.r.p.** on 200 kHz channels. ~1.5–4.5 MHz below
  869.52 → RFID CP-patch designs transfer directly, but their power/channel rules
  are a *separate* allocation — don't apply them to your 869.52 link.
- **Wider 863–870 SRD context:** lower sub-bands (868.0–868.6, 868.7–869.2, …)
  are 25 mW; 869.4–869.65 at 500 mW is the *only* high-power slot — which is why
  telemetry uses it.
- **Practical:** the duty/power caps are **transmitter** obligations; a receive-only
  ground antenna isn't power-limited. Design/measure for clean RHCP and |S11|≤−10 dB
  across **at least 869.4–869.65 MHz**. Keep any TX EIRP ≤27 dBm e.r.p. (antenna
  gain + cable accounted for).

---

## 9. Decision & recommended build — flat single-PCB, single-feed corner-truncated

**One flat 2-layer NP-140F PCB.** RHCP from **truncating two diagonal corners** of a
near-square patch; ONE inset microstrip feed to ONE edge-launch SMA. No coupler, no
termination resistor, no air, no probe, no standoffs. Order → solder one SMA → done.

| Item | Spec | Note |
|------|------|------|
| **Board** | single **2-layer NP-140F, 1.6 mm, 160×160 mm** (centred patch, 4× M3) | top = patch + feed; bottom = ground. εr 4.15 @ 870 MHz. |
| **Patch** | near-square ~82.5 mm, two diagonal corners chamfered ~8 mm | **CP from the truncation**; BL+TR diagonal → RHCP at +z |
| **Feed** | ONE inset microstrip, −y edge centre, ~6 mm inset → edge-launch SMA | 50 Ω; no coupler, no resistor — all accepted power goes to the patch |
| **Ground** | 160 mm → **wide beam** (coverage) | locked for coverage; bigger = narrower beam (§4) |
| Validated (un-tuned seed) | **directivity 6.6 dBi, η_rad 28 %, realised +0.8 dBic, RHCP, S11 −10.9 dB** | AR ~6 dB at seed → optimiser tunes ≤3 dB |
| Cost | **~€25–45 for 5** (1 PCB + 1 SMA) | + coax / radome per station |

Why this design: it's the same fully-reproducible "order-solder-done" etched PCB, but
single-feed deletes the dual-feed coupler's **isolated-port resistor — a structural sink
that burned ~64 % of accepted power** (§0.1), recovering ~10 dB of realised gain (−9.6 →
+0.8 dBic). The price is that single-feed CP is εr/fab-sensitive; that is now manageable
because NP-140F's εr is datasheet-known (§5), the W×truncation optimiser centres the AR
null, and 3.2 mm substrate (the main gain lever, §0.5) also widens AR. RHCP sense is set by
**which diagonal is truncated** (BL+TR → RHCP) — verify from the far field (E_R vs E_L) and
against the helix/QFH sense (§1, issue #43). Build: [bom.csv](bom.csv) *(update: drop the
50 Ω R)*. As-built code on branch `patch_antenna_SF`.

**To increase gain (if wanted):** efficiency, not aperture — **3.2 mm substrate (+1.5–2 dB,
PCBWay)** first, then an air/foam gap (+3–4 dB, 3-D assembly). A bigger board (200 mm) buys
only ~+0.5 dB and narrows the beam (§0.5/§4).

**Open before fab:** run the full W×truncation optimise to land AR ≤ 3 dB at f_target; then
the KiCad board reflects the tuned dims. Confirm NP-140F is actually supplied at 160 mm (§5).

---

## 10. References / further reading
*All citation-checked (DOIs/URLs verified to resolve and match). ★ = most directly
on-topic for the suspended air-gap L-probe RHCP build.*

**Design method / SOP**
- **Sharma, P. C. & Gupta, K. C.** "Analysis and Optimized Design of Single Feed
  Circularly Polarized Microstrip Antennas." *IEEE TAP* 31(6), 1983, 949–955.
  doi:10.1109/TAP.1983.1143162. — *The* single-feed CP recipe: dS/S ≈ 1/(2Q),
  diagonal→RHCP. **Primary method reference.**
- **Lee, Sambell, et al.** "A Design Procedure for a Circularly Polarized, Nearly
  Square Patch Antenna." *Microwave Journal* (art. 935). — perturbation-segment SOP
  (2.45 GHz worked example).
- "Single-feed Corner-Truncated Microstrip CP Antenna CAD Design." *IEEE* (doc
  9772892). — CAD procedure + closed-form Q (frequency-agnostic).
- Balanis, *Antenna Theory*, Ch. 14 — cavity model, CP, ground-plane effects, AR.

**★ Suspended air-gap / L-probe CP at ~UHF RFID (closest precedents)**
- **★ Cheng, K., Lim, E. H. & Phua, Y. N.** "Circularly Polarized Suspended Patch
  Antenna Fed by Modified L-Probe for UHF RFID Reader." *Radioengineering* 26(4),
  2017, 1033–1040 (open: radioeng.cz). — Suspended air patch + **modified L-probe**
  (extra bend = match knob that doesn't spoil AR). 5.5 % AR BW, **9.7 dBic** single /
  **14.7 dBic** 2×2, ~890–940 MHz → scale ×~1.05 for 869.52.
- **Nestoros, Christou & Polycarpou.** "Design of Wideband CP Patch Antennas for
  RFID … FCC/ETSI UHF Bands." *PIER C* 78, 2017, 115–127. doi:10.2528/PIERC17071801
  (open). — Air single + stacked truncated-corner, 865–928 MHz, 8.3 / 9.3 dBic.
- "A Universal UHF RFID Reader Antenna." *IEEE TMTT* 57(5), 2009 (doc 4806172). —
  2 corner-truncated patches + suspended feed + 4 sequential probes: 8.3 dBic,
  AR<3 dB & ~75° AR beamwidth over 818–964 MHz (16.4 %).
- **Li, J., et al.** "A Wideband Single-Fed CP Patch Antenna With Enhanced AR
  Bandwidth for UHF RFID." *IEEE Access* 6, 2018, 55883–55892.
  doi:10.1109/ACCESS.2018.2872692 (open). — techniques to widen single-feed AR.

**On-band (868 MHz) benchmarks & context**
- "Low Cost Circularly Polarized Antenna for IoT Space Applications." *MDPI
  Electronics* 9(10):1564, 2020. doi:10.3390/electronics9101564. — 868 MHz RHCP on
  cheap FR-4, ~3 dBic, ~50 MHz BW (realistic cheap-build benchmark).
- "Design of Circular Polarized Dual Band Patch Antenna" (MSc thesis, DIVA
  diva2:528320). — 868 MHz CP patch, worked design, ~24 MHz BW.
- **Nguyen, Ferrero & Trinh.** "Compact UHF CP Multi-Band Quadrifilar Antenna for
  CubeSat." *MDPI Sensors* 23(12):5361, 2023. doi:10.3390/s23125361. — RHCP **QFH**
  at 868/915/923, 77×77×10 mm (helix — comparison/context, the rocket-side analogue).
- **Yahya, M. S. et al.** "LoRa Microstrip Patch Antenna: A comprehensive review."
  *Alexandria Engineering Journal* 103 (2024) 197–221. doi:10.1016/j.aej.2024.06.045.
  (PDF in repo root.) — field survey: 868 MHz patches ~1.5–5 dBi; EBG/metamaterial/
  DRA/corrugation enhancement levers.

**Regulatory**
- CEPT/ERC **Recommendation 70-03** (current edition) — EU SRD band plan.
- ETSI **EN 300 220** (non-specific SRD) and **EN 302 208** (UHF RFID).

---
*Last updated 2026-06-08 for the single-feed corner-truncated design (branch `patch_antenna_SF`).
The dual-feed branch-line coupler was retired after a power decomposition showed it radiated
~3 % (§0). Sections marked ⌗ are kept as history. Current state: WIP.md + §0/§9.*

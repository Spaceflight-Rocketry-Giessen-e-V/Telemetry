# Patch Antenna — 869.525 MHz RHCP Ground Station

Design notes for the SPROG telemetry ground-station patch antenna: what it is, why it is
built this way, and what has to be verified on the physical boards. Synthesised from the
openEMS simulations in this repo, multi-source web research, and the review paper
*Yahya et al., "LoRa Microstrip Patch Antenna: A comprehensive review," Alexandria
Engineering Journal 103 (2024) 197–221* (doi:10.1016/j.aej.2024.06.045).

> **The design.** One flat 2-layer **NP-140F (FR-4-class)** PCB, **160×160 mm**. RHCP comes
> from a **single-feed corner-truncated** patch (two diagonally-opposite corners chamfered),
> fed by **one** inset microstrip to **one** edge-launch SMA — no coupler, no termination
> resistor, ~€25–45 for 5. The antenna is a **fixed, wide-beam RHCP backup** behind the
> tracked helical; the 10 km link closes with large margin, so coverage and robust CP matter
> more than gain.
>
> **Geometry (locked):** patch side **W = 82.5 mm**, corner truncation **Δ = 8.25 mm**, feed
> inset **5.8 mm**, ground plane **160 mm** — these are the `config.py` synthesis seeds.
>
> **Simulated performance** (`fab/results.json`): boresight **AR 1.04 dB**, AR ≤ 3 dB over a
> **152° beam** and a **6.5 MHz** band, worst AR **1.66 dB** across the ±45° coverage cone,
> **S11 −12.6 dB**, directivity **6.6 dBi**, **η_rad 29 %** / η_tot 27 %, realised gain
> **+1.0 dBic** boresight (−1.8 dBic at the 45° cone edge), **RHCP**.

---

## 1. Project context

| Fact | Value |
|------|-------|
| Operating frequency | 869.525 MHz (EU 868 ISM; high-power sub-band 869.4–869.65 MHz), λ₀ ≈ 345 mm |
| Polarisation needed | **RHCP** — the rocket carries an onboard **RHCP quadrifilar helix**, so RHCP↔RHCP is a matched pair (0 dB polarisation loss). LHCP would be a deep mismatch. |
| Role of this antenna | A **fixed, wide-beam RHCP** receiver. A separate **tracked high-gain helical** handles the primary link, so this patch *complements* it (wide coverage, robust CP) rather than duplicating it with a high-gain pencil beam. |
| Why CP at all | A spinning/tumbling vehicle rotates its onboard antenna; matched CP avoids the deep polarisation fades that linear↔linear suffers. With an RHCP rocket, same-sense CP is the only correct choice. |

> ⚠️ **Sense matters most.** RHCP↔RHCP = matched; RHCP↔LHCP = 20+ dB loss. The onboard QFH is
> **RHCP (confirmed by the team)** and this patch is **RHCP** via the bottom-left + top-right
> truncated diagonal, so the pair is matched. The ground helical must be RHCP too: the patch's
> sense is set by the CP perturbation and is trivial to flip in design, whereas the **helix's
> sense is fixed by its winding** — treat the helix as the reference and match everything else
> to it. A mirrored patch layout yields a perfect *LHCP* antenna, deaf to the rocket.

---

## 2. Microstrip patch fundamentals

- A patch resonates when its length ≈ λ/2 in the substrate; higher permittivity εr shrinks it
  (≈ 1/√εr), lower loss raises efficiency. FR-4 class here: εr ≈ 4.15, tanδ ≈ 0.014,
  h = 1.6 mm → patch ≈ 83 mm. Air (εr ≈ 1) would need ≈ 165 mm.
- Feed options: inset microstrip, coaxial **probe**, proximity-coupled, aperture-coupled. This
  build uses an etched inset microstrip on the −y edge; the model feeds it at that inset point
  ([../src/model.py](../src/model.py)). All RF geometry is etched, so the antenna is
  reproducible by etch alone — no probe, no spacer, no extra layer.
- The **ground plane** separates two worlds: the radiating side (above) and the
  feed/electronics side (below). Keep all coax/connectors/radio **below** it.

### Circular polarisation — three ways to make it
| Method | AR bandwidth / robustness | Efficiency | Note |
|--------|---------------------------|------------|------|
| **Single-feed corner truncation** (**CHOSEN**) | ~0.5–2 % on thin substrate; tight on 1.6 mm FR-4 | **high — no loss network** | CP from one mode-split; AR is εr/fab-sensitive but tunable with a known εr. All accepted power goes to the patch. |
| Single-feed slot/U-slot variants | ~2–7 % | high | lateral AR improvement only |
| Dual-feed 90° hybrid (branch-line coupler) | ~6–30 %+, tolerance-proof | **low** | quadrature enforced by copper, but the coupler's isolated port terminates into a resistor that absorbs the patch's feed-point mismatch — a structural efficiency sink a good *input* match hides. Robust CP, poor realised gain. |
| Sequential rotation (array) | >15 %, excellent | high | cross-pol cancels by geometry; needs many elements + a feed network |

**Why single-feed.** The coupler buys εr-robust CP, but its isolated-port resistor is a
structural sink: it swallows the patch mismatch instead of radiating it, costing roughly an
order of magnitude in realised gain on the same board. Single-feed has no such sink — every
watt accepted goes to the patch — at the price of an εr/fab-sensitive AR. That price is
payable here because the AR ≤ 3 dB window width ∝ 1/Q and:

1. NP-140F's εr is datasheet-specified (±0.1), so resonance lands predictably (§5);
2. FR-4-class loss *lowers* Q and therefore *widens* the AR window compared with a low-loss
   laminate;
3. the optimiser centres the **AR null** (not the S11 dip) on f_target (§3);
4. a thicker substrate widens AR further, if a future revision wants the margin (§6).

The residual risk — a narrow AR band against εr and thermal drift — is handled by a per-board
acceptance test rather than by design (§9).

---

## 3. Design rules that govern this patch

### CP centre and impedance match are separate tuning targets
A *matched* patch is not automatically circular at f_target. On this geometry the axial-ratio
null sits **~6–7 MHz below the S11 centroid**, so tuning on the S11 dip lands the CP null
below the channel. Measured by NF2FF on real sim data (same Δ and inset, only W varied):

| W (mm) | AR-null frequency | AR @ 869.525 MHz | S11 centroid |
|---|---|---|---|
| **82.5 (locked)** | **869.0 MHz** | **1.0 dB** ✓ | 875.0 MHz |
| 83.05 | 863.5 MHz | 4.6 dB ✗ | 870.2 MHz |

A 0.55 mm change in W moves the null ~5.5 MHz and takes AR at f_target from ~1 dB to ~4.6 dB.
**Rule: centre the design on the AR null and verify CP on the AR(f) curve, never on the S11
dip.**

### Truncation sets the mode split; W centres it
Single-feed CP splits the TM10/TM01 modes into an equal-amplitude 90° pair at f₀. The classic
design rules are **truncation area dS/S ≈ 1/(2·Q0)** and **AR bandwidth ≈ 1/(√2·Q0)** — both
say the same thing: low Q buys forgiving CP. Δ and W are coupled (Δ sets the split, W centres
it), so they have to be tuned together. Δ = 8.25 mm ≈ 0.10·W sits at the deepest null for this
1.6 mm stackup; enlarging Δ over-splits the modes and destroys CP, so the AR band cannot be
widened by truncation alone — only by lowering Q (thicker substrate or an air gap).

Measured on a (W × Δ) drift-margin sweep (`tests/tool_trunc_bw_sweep.py`, W fixed at 82.5 mm):
boresight AR_min climbs monotonically **0.41 → 2.83 → 5.44 → 7.55 dB** for Δ = **8.25 → 9.5 →
11 → 12.75 mm**. At converged fidelity Δ = 8.25 / 8.5 / 8.6 are indistinguishable (6.5–6.7 MHz
band, ~3 MHz of drift margin), so apparent band differences seen at coarse fidelity do not
survive convergence. Δ = 8.25 mm stands as the optimum for this stackup.

### Gain is efficiency-limited, not aperture-limited
Directivity (6.6 dBi) is already at what a single patch gives. The antenna loses ~5 dB to
dielectric loss and mismatch, so the gain levers are efficiency, not board size:

| Lever | Δ realised gain | Cost / tradeoff |
|---|---|---|
| **3.2 mm substrate** (1.6→3.2 mm) | **+1.5–2 dB** (+ wider AR) | ~free as stock thickness, re-tune only — best bang/buck |
| Air/foam gap (~10–25 mm) | **+3–4 dB** (η → ~85 %) | a 3-D assembly instead of one etched board |
| Stacked parasitic patch | +1–2 dB (+ BW) | adds a layer/spacer |
| Lower-loss laminate (Rogers) | +3–4 dB | over budget |
| Soldermask keep-out over the patch | +0.1–0.3 dB | free; makes the build match the bare-copper sim (already in `kicad_export`) |
| 2 oz copper | +0.1–0.2 dB | cheap insurance for feed and edges |
| Board 160→200 mm | only ~+0.5 dB directivity | *narrows the beam* — trades coverage (§4) |
| 2×2 array | +6 dB | needs >250 mm plus a feed network — breaks the size/coverage budget |

**The asymmetry that decides everything here:** every *directivity* lever (bigger board,
stacking, arrays) narrows the beam and fights the wide-beam role, while every *efficiency*
lever (thickness, air gap, laminate) raises gain *without* narrowing it. Prefer efficiency.
Any stackup change makes a re-optimise of W/Δ/inset mandatory.

### Optimiser and convergence
A **2-D grid (patch side W × corner-truncation Δ) screen plus a full-fidelity confirm**
(`config.py`: `GRID_W_FRAC` × `GRID_TRUNC_MM`, `N_CONFIRM`). W sets resonance, Δ sets the CP
mode-split, and the AR null is only centred on f_target when both are right together — a
sequential coordinate descent cannot navigate that coupling. The worker scans boresight AR
across f_target ± 30 MHz and the cost functions centre `f_ar_null`. Selection uses a
deadband+ramp resonance penalty (`F_RES_*`), the worst AR over f_target ± `AR_MARGIN_MHZ`,
an AR ≤ 3 dB beamwidth reward, a gain floor, and a **radiation-efficiency reward** (`W_EFF`)
so the optimiser keeps designs that actually radiate. The board is locked at 160 mm for
coverage and is not swept.

**Convergence is part of the method, not a formality.** Resonance and match settle quickly,
but the CP null is a razor feature that is time-step-limited far longer: it only stops moving
above ~250k FDTD time steps, which is why the screen runs at `NrTS_screen = 150000` and the
deliverable run at `NrTS_final = 350000`. Judge AR only at full fidelity, and confirm any
headline AR figure on a time-step ladder rather than a single run. The same applies to mesh:
under-meshed truncated corners report *optimistic* AR.

The ladder on the locked geometry: boresight AR **0.45 dB @ 150k → 1.04 @ 250k → 1.04 @ 350k**,
AR ≤ 3 dB band **7.9 → 6.6 → 6.5 MHz**. 250k and 350k agree, so the deliverable run
(`fab/results.json`) is converged; coarser runs read optimistically on both figures. Finer
chamfer meshing was not needed — the null and band stop moving on the time-step axis alone.

### Verification procedure
1. Size W for the substrate εr so resonance lands near the channel.
2. Set Δ from the Q estimate (dS/S ≈ 1/(2·Q0)); truncate the diagonal that yields **RHCP**
   (bottom-left + top-right → RHCP at +z).
3. Place the inset for a 50 Ω match, then re-check — match and CP centre move independently.
4. Centre the **AR null** on f_target on a fine frequency grid (a coarse grid or heavy
   smoothing hides a few-MHz null entirely).
5. **Sense-check RHCP from the far field** (E_R vs E_L). The wrong diagonal gives LHCP and
   ~20 dB loss against the rocket's RHCP helix. Verify before fabrication.
6. Check AR over the **coverage cone**, not just boresight — the rocket moves across the sky.
7. Confirm the run is converged (time-step ladder, mesh at the chamfers).

`tests/stage0_dipole_calibration.py` is the permanent calibration gate for the far-field
chain: a lossless half-wave dipole must come back at η ≈ 100 % and Dmax 2.19 dBi against the
textbook 2.15 dBi. Run it whenever absolute directivity or efficiency numbers look off.

---

## 4. Ground plane, beamwidth and board size

**Ground-plane size has sharply diminishing returns.** From a ground-plane sweep on this patch
family:

| GP edge | board/λ₀ | directivity |
|--------|---------|------|
| 150 mm | 0.43 | 6.4 dBi |
| 250 mm | 0.72 | 7.2 dBi |
| 300 mm | 0.87 | 7.4 dBi |
| 350 mm | 1.01 | 7.6 dBi |
| 375 mm | 1.09 | 7.6 dBi |
| 400 mm | 1.16 | 7.4 dBi (edge-diffraction ripple) |

About +1 dB across the whole 150→375 mm range, most of it reached by ~250 mm, then ripple past
~1 λ₀. A patch ground only needs ~0.5–1 λ for a clean pattern, and realised *gain* is set by
efficiency (§3), not ground size. **A bigger board is cost and a narrower beam, not gain.**

**Smaller ground = wider beam, and that is what this antenna wants.** A beamwidth-vs-ground
sweep shows the AR ≤ 3 dB coverage beam widening as the ground shrinks:

| GP edge | AR ≤ 3 dB beamwidth |
|---|---|
| 160 mm | 52° |
| 170 mm | 40° |
| 180 mm | 36° |
| 190 mm | 28° |

So **160 mm is a deliberate coverage choice**, not a manufacturing floor: the patch itself
(~83 mm plus feed and margin) would fit on much less. The board is square and centred on the
patch, leaving all four corners clear for 4× M3. Going to 200 mm buys ~+0.5 dB directivity
while narrowing the beam — only do that when deliberately trading coverage for gain.

---

## 5. Cost and laminate

PCB price is driven by **area** with discrete tier jumps. JLCPCB: ≤100×100 mm hits a ~2 USD
promo tier, and a per-50 cm² surcharge starts above **650 cm²** (≈ a 255 mm square) — so the
**160×160 board (256 cm²) is comfortably in the cheap tier** (~25–45 €/5 incl. ship+VAT to
the EU).

| Board | directivity @1.6 mm | 5× JLCPCB (incl. ship+VAT) | 5× Aisler (EU) |
|------|-------------|----------------------------|----------------|
| 100×100 | ~5.7 dBi | ~15–25 € | ~54 € |
| 120×120 | ~6.0 dBi | ~25–40 € | ~72 € |
| 150×150 | 6.4 dBi | ~35–55 € | ~104 € |
| **160×160 (CHOSEN)** | **6.6 dBi** | **~25–45 €** | ~115 € |
| 170×170 | ~6.6 dBi | ~45–70 € | ~129 € |
| 375×375 | 7.6 dBi | ~140 € | — |

Within the allowed range, **directivity moves <1 dB while cost goes 2–3×** → pick small. Real
performance comes from the **substrate**, not the size. *Mid-loss "FR-4" grades (S1141,
S1000H) are not low-loss — they are the default stock — so they buy ~0 dB; genuine low-loss
means Rogers / I-Speed / S7-series, which break the budget.*

**Laminate — NP-140F for predictability, not for loss.** The build specifies **Nan Ya NP-140F**
(FR-4-class, Tg 135 °C) rather than generic stock FR-4. The reason is *not* loss: NP-140F's
tanδ ~0.013–0.014 against stock ~0.0155 buys ~0.3–0.5 dB, irrelevant against a 22–30 dB link
margin (exactly the "mid-loss FR-4 ≈ 0 dB" point above). The reason is **εr predictability**: a
resonant patch lands where εr says it will, and NP-140F is datasheet-specified at
**εr 4.0–4.2 (±0.1)**, whereas stock FR-4 is an unspecified ~4.2–4.6 grab-bag (the common stock
part, KingBoard **KB-6164**, measures ~4.6 / 0.0155 @ 1 GHz). Known and tighter εr means
~±10 MHz of batch resonance scatter instead of ~±20 MHz, i.e. boards that hit 869.525 MHz
without per-unit tuning. At equal cost, with the laminate guaranteed if it is specified,
NP-140F is the pick — design εr = 4.15 @ 870 MHz.

> ⚠️ **Confirm the fab actually supplies NP-140F at 160×160.** Cheap tiers stock
> KingBoard/Shengyi (KB-6164-class), so a bare "FR-4" order silently delivers εr ~4.6 and the
> patch lands ~25 MHz low. Get it in writing, and keep the re-tune ready as a fallback.

---

## 6. Upgrade paths (if a future revision wants more)

The built board is 1.6 mm and stays 1.6 mm. If a revision needs more gain or more AR margin,
take the efficiency levers in order — they raise gain *without* narrowing the coverage beam:

1. **3.2 mm substrate** (+1.5–2 dB, and a wider/more drift-tolerant AR window because Q drops).
   Available at PCBWay; JLCPCB caps at 2.0 mm. Requires a full re-tune of W/Δ/inset.
2. **Air/foam gap (~20–25 mm).** Two wins at once: a lossless dielectric takes efficiency to
   ~90–95 % (the ~2.5–3.5 dB now lost as heat radiates instead), and a thick low-ε gap drops Q
   roughly 10×, widening the AR ≤ 3 dB window from a few MHz to ~25–30 MHz — enough to absorb
   fab, εr and thermal drift outright. The costs are real: the patch grows ~2× (εr ≈ 1, ~165 mm
   side), it becomes a 3-D assembly whose gap height must be held rigidly (the gap sets f₀, Q,
   AR *and* match), and a straight probe through that gap is strongly inductive, so it needs an
   L-probe or a series capacitance to cancel the reactance.
3. Stacked parasitic patch (+1–2 dB) or a superstrate, if aperture is genuinely needed.

Directivity levers (bigger board, arrays) are the wrong tool for this antenna — they narrow
the beam and duplicate the tracked helical.

---

## 7. Lessons from the literature

### From the AEJ 2024 LoRa-MPA review (Yahya et al.)
- **868 MHz patches are low-gain in practice:** the survey's 868 MHz designs cluster at
  **~1.5–5 dBi**, nearly all on FR-4 — consistent with the ceiling seen here.
- **Single-feed CP is hard at this frequency:** the review cites a truncated-corner multilayer
  CP patch (with a metamaterial gain boost, ~2 dBi) and a design stuck at **AR ≈ 7.2 dB**.
  Narrow AR is the characteristic single-feed failure mode.
- **Substrate guidance:** for gain, choose **low permittivity and low loss tangent**; high εr
  shrinks size but increases loss.
- **Enhancement levers it catalogues** (relevant while staying on FR-4):
  - **EBG** (electromagnetic band-gap) ground structures — suppress surface waves, raising
    gain/efficiency on lossy or thick substrates.
  - **Metamaterial** (split-ring) and **dielectric/FSS superstrate** — gain.
  - **DRA** (dielectric resonator) — low loss, wide impedance bandwidth.
  - **Corrugation** (bull's-eye / leaky-wave) — high gain from a planar aperture.
- Tools used in the field: CST, HFSS, FEKO, ADS (this repo uses openEMS — comparable FDTD).
  Target **SWR < 1.5** for the match.

### The adjacent goldmine: UHF RFID reader antennas (865–868 MHz)
EU UHF RFID sits at **865–868 MHz** — essentially this frequency — and RFID readers
overwhelmingly use **CP patch** antennas (dual-feed/hybrid or truncated single-feed,
~6–9 dBic, often air/foam or thick substrate). These are the most directly transferable
real-world designs. GNSS (1.2–1.6 GHz) CP-patch design *methods* also transfer directly.

### Pitfalls the literature keeps repeating
- **Narrow AR is the central single-feed weakness** (AR BW ≈ 1/(√2·Q0)). On a thin, high-Q
  board it is the binding constraint; the only structural fix is lower Q (§6).
- **Manufacturing sensitivity:** a high-Q truncation is small and CP is very sensitive to
  fabrication error. Low-Q designs get a bigger, more forgiving truncation.
- **Polarisation sense:** the wrong diagonal gives LHCP and ~20 dB loss. Lock the sense in
  simulation and re-verify on the physical part.
- **Don't over-reach on bandwidth:** the telemetry channel is ~250 kHz wide. A CP null centred
  on the channel is what matters, not a broad AR band for its own sake.
- **Meshing and convergence:** mesh the thin truncated corners finely and check AR convergence
  — an under-resolved model reports *optimistic* AR (§3).

---

## 8. EU 868 regulatory notes (CEPT/ERC 70-03; ETSI EN 300 220 / EN 302 208)
- **Telemetry channel:** **869.4–869.65 MHz** is the EU high-power SRD sub-band —
  **500 mW e.r.p. (27 dBm)** with **≤10 % duty cycle OR LBT+AFA**. 869.525 MHz sits squarely
  here. (The old "g3" letter label is from earlier ERC 70-03 editions; recent editions
  renumber, but the limits stand.)
- **RFID reuse band (design source, *not* this link):** **865–868 MHz**, ETSI **EN 302 208**,
  up to **2 W e.r.p.** on 200 kHz channels. ~1.5–4.5 MHz below 869.525 → RFID CP-patch designs
  transfer directly, but their power/channel rules are a *separate* allocation — don't apply
  them to the 869.525 link.
- **Wider 863–870 SRD context:** lower sub-bands (868.0–868.6, 868.7–869.2, …) are 25 mW;
  869.4–869.65 at 500 mW is the *only* high-power slot — which is why telemetry uses it.
- **Practical:** the duty/power caps are **transmitter** obligations; a receive-only ground
  antenna isn't power-limited. Design and measure for clean RHCP and |S11| ≤ −10 dB across at
  least **869.4–869.65 MHz**. Keep any TX EIRP ≤ 27 dBm e.r.p. (antenna gain and cable
  accounted for).

---

## 9. The build

**One flat 2-layer NP-140F PCB.** RHCP from **truncating two diagonal corners** of a
near-square patch; ONE inset microstrip feed to ONE edge-launch SMA. No coupler, no
termination resistor, no air gap, no probe, no standoffs. Order → solder one SMA → done.

| Item | Spec | Note |
|------|------|------|
| **Board** | 2-layer **NP-140F, 1.6 mm, 160×160 mm** (centred patch, 4× M3) | top = patch + feed; bottom = ground. Design εr 4.15 @ 870 MHz. |
| **Patch** | near-square **W = 82.5 mm**, two diagonal corners chamfered **Δ = 8.25 mm** | CP from the truncation; BL+TR diagonal → **RHCP at +z** |
| **Feed** | ONE inset microstrip, −y edge centre, **5.8 mm** inset → edge-launch SMA | 50 Ω; no coupler, no resistor — all accepted power goes to the patch |
| **Ground** | 160 mm → **wide beam** (coverage) | locked for coverage; bigger = narrower beam (§4) |
| **Simulated** | **AR 1.04 dB boresight**, AR ≤ 3 dB over a **152° beam** / **6.5 MHz** band, worst **1.66 dB** over the ±45° cone, **S11 −12.6 dB**, directivity **6.6 dBi**, η_rad **29 %**, realised **+1.0 dBic**, RHCP | AR null on f_target; `fab/results.json` |
| **Cost** | **~€25–45 for 5** (1 PCB + 1 SMA) | + coax and radome per station |

Build details and sourcing: [bom.csv](bom.csv). Gerbers and the as-built KiCad project are in
`fab/`.

### Acceptance gates
- **Per-board cold-AR test (required, not optional).** The CP null is a **6.5 MHz** band while
  ±0.1 εr alone shifts it ~±10 MHz, and temperature adds a second drift of the same order — the
  band is narrower than the spread, so CP cannot be assumed from the simulation. Measure each
  board's boresight AR at 869.525 MHz and bin or tune it. Do this at the **cold operating
  extreme**, not just at room temperature: the cold side breaks first. A board that lands
  near-linear falls back to ~−3 dB polarisation loss and the link still closes in this backup
  role, but it must be a known board, not a surprise.
- **εr sensitivity (measured — `tests/tool_eps_sweep.py`).** The null moves ~**−10 MHz per
  +0.1 εr**, so only εr ≈ 4.15 keeps AR ≤ 3 dB inside the channel; at ±0.1 εr the boresight AR
  at f_target degrades to **8–13 dB** (effectively linear). A ±0.1 mm thickness tolerance is
  harmless by comparison. This is what makes the per-board gate mandatory rather than advisory.
- **Thermal CP window (`tests/tool_thermal_drift.py`).** TCDk(εr) + CTE walk the null by
  ~**+0.11 MHz/°C** (≈ +8 MHz across −15…+55 °C) — a second drift source stacked on the lot
  spread, which a one-time room-temperature tune cannot cancel. CP holds from roughly 0 to
  55 °C but **fails at −15 °C** (AR ~3.5 dB): the cold side breaks first. ⚠️ These coefficients
  are **placeholder FR-4 values** — the real window needs NP-140F's datasheet TCDk and CTE.
- **Laminate confirmation.** Get NP-140F at 160×160 confirmed in writing (§5), together with
  the datasheet TCDk and CTE needed to pin the thermal CP window.
- **Sense verification.** Confirm RHCP from the far field (E_R vs E_L) and against the rocket's
  RHCP QFH and the ground helical's winding (§1).
- **Un-simulated hardware.** The radome acts as a superstrate and detunes the CP null downward,
  and the real SMA launch transition (the microstrip neck, 3.2 → 0.61 mm, adds ~3 nH) sits
  outside the idealised port model. Check both before committing a station build.

### Analysis tools
Re-runnable harnesses in `tests/` — all read the locked dims from `config.py`, and their JSON
outputs are gitignored as regenerable:

| Script | Purpose |
|---|---|
| `tool_eps_sweep.py` | εr / thickness robustness of the CP null |
| `tool_trunc_bw_sweep.py` | (W × truncation) drift-margin sweep |
| `tool_thermal_drift.py` | TCDk + CTE temperature CP window |
| `board_sweep.py` | AR ≤ 3 dB beamwidth vs ground-plane size |
| `stage0_dipole_calibration.py` | far-field NF2FF calibration gate (lossless dipole) |
| `stage1_single_feed.py`, `stage3_optimizer.py` | resonance scan; optimiser smoke test |
| `tool_build_inspect.py`, `tool_show_geometry.py`, `tool_link_budget.py` | mesh/geometry inspection, viewer, link budget |

---

## 10. References / further reading
*All citation-checked (DOIs/URLs verified to resolve and match). ★ = closest precedents for
single-feed CP patch design at this frequency.*

**Design method**
- **Sharma, P. C. & Gupta, K. C.** "Analysis and Optimized Design of Single Feed Circularly
  Polarized Microstrip Antennas." *IEEE TAP* 31(6), 1983, 949–955.
  doi:10.1109/TAP.1983.1143162. — *The* single-feed CP recipe: dS/S ≈ 1/(2Q),
  diagonal → RHCP. **Primary method reference.**
- **Lee, Sambell, et al.** "A Design Procedure for a Circularly Polarized, Nearly Square Patch
  Antenna." *Microwave Journal* (art. 935). — perturbation-segment procedure (2.45 GHz worked
  example).
- "Single-feed Corner-Truncated Microstrip CP Antenna CAD Design." *IEEE* (doc 9772892). —
  CAD procedure + closed-form Q (frequency-agnostic).
- Balanis, *Antenna Theory*, Ch. 14 — cavity model, CP, ground-plane effects, AR.

**★ CP patches at UHF RFID frequencies (closest precedents)**
- **★ Cheng, K., Lim, E. H. & Phua, Y. N.** "Circularly Polarized Suspended Patch Antenna Fed
  by Modified L-Probe for UHF RFID Reader." *Radioengineering* 26(4), 2017, 1033–1040 (open:
  radioeng.cz). — Suspended air patch + modified L-probe (an extra bend gives an S11 knob that
  does not spoil AR). 5.5 % AR BW, **9.7 dBic** single / **14.7 dBic** 2×2, ~890–940 MHz →
  scale ×~1.05 for 869.525.
- **Nestoros, Christou & Polycarpou.** "Design of Wideband CP Patch Antennas for RFID …
  FCC/ETSI UHF Bands." *PIER C* 78, 2017, 115–127. doi:10.2528/PIERC17071801 (open). — Air
  single and stacked truncated-corner, 865–928 MHz, 8.3 / 9.3 dBic.
- "A Universal UHF RFID Reader Antenna." *IEEE TMTT* 57(5), 2009 (doc 4806172). — 2
  corner-truncated patches + suspended feed + 4 sequential probes: 8.3 dBic, AR < 3 dB and
  ~75° AR beamwidth over 818–964 MHz (16.4 %).
- **Li, J., et al.** "A Wideband Single-Fed CP Patch Antenna With Enhanced AR Bandwidth for UHF
  RFID." *IEEE Access* 6, 2018, 55883–55892. doi:10.1109/ACCESS.2018.2872692 (open). —
  techniques to widen single-feed AR.

**On-band (868 MHz) benchmarks & context**
- "Low Cost Circularly Polarized Antenna for IoT Space Applications." *MDPI Electronics*
  9(10):1564, 2020. doi:10.3390/electronics9101564. — 868 MHz RHCP on cheap FR-4, ~3 dBic,
  ~50 MHz BW (realistic cheap-build benchmark).
- "Design of Circular Polarized Dual Band Patch Antenna" (MSc thesis, DIVA diva2:528320). —
  868 MHz CP patch, worked design, ~24 MHz BW.
- **Nguyen, Ferrero & Trinh.** "Compact UHF CP Multi-Band Quadrifilar Antenna for CubeSat."
  *MDPI Sensors* 23(12):5361, 2023. doi:10.3390/s23125361. — RHCP **QFH** at 868/915/923,
  77×77×10 mm — the rocket-side analogue.
- **Yahya, M. S. et al.** "LoRa Microstrip Patch Antenna: A comprehensive review." *Alexandria
  Engineering Journal* 103 (2024) 197–221. doi:10.1016/j.aej.2024.06.045. — field survey:
  868 MHz patches ~1.5–5 dBi; EBG / metamaterial / DRA / corrugation enhancement levers.

**Regulatory**
- CEPT/ERC **Recommendation 70-03** (current edition) — EU SRD band plan.
- ETSI **EN 300 220** (non-specific SRD) and **EN 302 208** (UHF RFID).

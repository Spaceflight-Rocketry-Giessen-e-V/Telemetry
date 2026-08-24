# Fab order — JLCPCB

Ordering checklist for the 869.525 MHz RHCP patch board. Parts list is in
[bom.csv](bom.csv); the design rationale behind these numbers is in
[research.md](research.md) (§5 cost/laminate, §9 build + acceptance gates).

> ## ⛔ Two things to settle BEFORE you order
>
> 1. **Re-plot the Gerbers.** The Gerbers tracked in `fab/gerbers/` are **stale** — see
>    [Gerber status](#gerber-status) below. Re-export them from the current board first.
> 2. **Confirm the laminate εr in writing.** JLCPCB's standard FR-4 is **not** NP-140F, and the
>    wrong εr detunes the antenna by ~25 MHz — see [Laminate](#laminate--the-one-that-matters).

---

## JLCPCB order form

| Field | Setting | Note |
|---|---|---|
| Base Material | FR-4 | |
| Layers | 2 | |
| Dimension | 160 × 160 mm | square, centred patch |
| PCB Qty | 5 | |
| Product Type | Industrial/Consumer electronics | |
| Different Design | 1 | |
| Delivery Format | Single PCB | no panelisation |
| PCB Thickness | **1.6 mm** | locked; 3.2 mm is not offered here (JLC caps at 2.0 mm) |
| PCB Color | any (green) | cosmetic — the top copper is mask-free anyway |
| Silkscreen | White | |
| Surface Finish | **Lead-free HASL** (default) or **ENIG** | see [Surface finish](#surface-finish) |
| Outer Copper Weight | **1 oz** (35 µm) | matches the exported stackup; 2 oz optional (+0.1–0.2 dB) |
| Board Outline Tolerance | Regular ±0.2 mm | design rule is 0.2 mm |
| Via Covering | Tented | only 4 RF vias; not critical |
| Min via / hole | Default | smallest hole is 0.4 mm — inside standard capability |
| Impedance Control | **No** | it forces JLC's own stackup + εr, which fights the NP-140F requirement |
| Castellated Holes | **No** | the end-launch SMA solders to top+bottom edge pads; no edge plating needed |
| Gold Fingers | No | |
| Remove Order Number | **Yes** (or specify bottom) | the top is exposed copper — keep JLC's mark off the patch |
| Electrical Test | Fully test (default) | |
| Confirm Production File | not required, but **expect a query** | JLC will likely flag the fully-open top mask — it is intentional |

---

## Laminate — the one that matters

The antenna's CP only lands on-channel at **εr ≈ 4.15** (Nan Ya **NP-140F**, or an equivalent
datasheet-specified FR-4-class laminate). JLCPCB's economy tier ships whatever Tg130–140 stock
they have loaded — typically **KingBoard/Shengyi KB-6164-class, εr ≈ 4.6** — which lands the
patch **~25 MHz low**. You cannot pick NP-140F from the standard dropdown.

Before ordering, either:
- open a support ticket / use the order **Remarks** to get the actual base material **and its Dk
  confirmed in writing**, or
- accept the shift and plan the re-tune (re-run the optimiser at the confirmed εr, re-export).

This is still an open pre-fab gate in [research.md §9](research.md).

## Surface finish

The entire **top copper is intentionally soldermask-free** (it matches the bare-copper
simulation — mask would pull resonance down ~5–10 MHz), so the finish coats a large exposed area.

- **Lead-free HASL (default):** free, RF-negligible at 869 MHz, solders fine for one SMA. The only
  downside is a slightly uneven coating over the large exposed patch, and a slightly less flat
  SMA tab.
- **ENIG (optional, ~$10–15/5):** dead-flat and uniform over the exposed copper and the 0.61 mm
  SMA launch tab. Take it only if you want the connector land perfectly coplanar. Note ENIG's
  nickel is marginally *more* lossy at RF than HASL — negligible here, but "ENIG = better RF" is
  not the reason to pick it.

Either is acceptable; the radome protects the exposed copper.

## Board-specific notes

- **Mounting holes are routed, not drilled.** The four M3 corner holes (8 mm inset) are cut as
  circles in `Edge.Cuts`, so they are absent from the drill file — JLC routs them. Fine, but the
  edges are slightly rougher than a drilled hole. Switching to drilled M3 is a board edit, not an
  order option.
- **The only drilled holes are four 0.4 mm plated vias** at the feed — the SMA-launch ground
  stitching, not mounting holes.
- **Top soldermask fully open** over patch + feed + SMA lands: intentional, already in the Gerbers
  (`F.Mask` openings). Don't let anyone "fix" it.

## Paste into JLCPCB "Remarks"

> 2-layer, 1.6 mm. Top soldermask is intentionally opened over all top copper (bare copper is by
> design — do not add mask). Requesting a laminate with Dk ≈ 4.15 (Nan Ya NP-140F or equivalent) —
> please confirm the actual base material and its Dk before production. Do not print the order
> number on the top (patch) side — bottom silk only.

---

## Gerber status

**The Gerbers in `fab/gerbers/` are stale — re-plot before ordering.**

- They were plotted **2026-06-16** with **KiCad 9.0.7**.
- `fab/patch_antenna.kicad_pcb` was since re-saved in **KiCad 10.0** (last change 2026-08-01,
  `generator_version "10.0"`), so the tracked Gerbers no longer correspond to the current board.
- The geometry difference is confined to a **front-silkscreen** graphic — copper, soldermask,
  board outline, vias and mounting holes are unchanged, so the *electrical and mechanical* board
  is identical. But the export is stale and unverified; don't ship it as-is.

### Version note — you need KiCad 10 to re-plot
The board is a **KiCad 10** file. `kicad-cli` 9.0.x **cannot load it** ("Failed to load board").
Re-plot on a machine with **KiCad 10** (or newer). This is also why the Gerbers drifted: the board
was edited in KiCad 10 on another machine and never re-plotted.

### To refresh (one command)
From the repo root, on a machine with a matching KiCad:

```
pwsh groundstation/antenna/patch/fab/export_gerbers.ps1
```

It locates `kicad-cli`, re-plots `gerbers/` from the board, and writes
`fab/patch_antenna_gerbers.zip` — **upload that zip to JLCPCB.** Then commit the refreshed
`fab/gerbers/` so the folder stays self-consistent. (Manual fallback: KiCad ▸ File ▸ Fabrication
Outputs ▸ Gerbers, then Generate Drill Files.)

### Guard — Gerbers can't silently go stale again
A `pre-commit` hook (`fab/hooks/pre-commit`) **blocks any commit that changes the board without
also staging refreshed Gerbers**. Install it once per machine from the repo root:

```
cp groundstation/antenna/patch/fab/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

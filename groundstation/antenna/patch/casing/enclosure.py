# -*- coding: utf-8 -*-
"""Parametric weather-sealed enclosure for the single-feed RHCP patch — Python -> OpenSCAD.

Mirrors the kicad_export.py pattern: reads the SAME board geometry from config.py (board edge =
2*SUB_HW_DEFAULT, substrate thickness, patch size, the M3 hole convention) and EMITS a parametric
OpenSCAD model, so the casing can never drift from the PCB it holds. OpenSCAD then renders
verification PNGs and exports the print/cut files.

A printed, weather-sealed tray with a bonded acrylic radome window. The RF geometry (10 mm
patch->window air gap, ~0.115*lambda0 wall-to-patch clearance, no metal above the ground plane)
and the DFM/sealing rules below are enforced by build-time asserts, so a future param edit cannot
silently break a print, a seal, or the RF clearance:
  * WALL 4 mm — thin enough to print ALL-PERIMETER solid (watertight) rather than around a porous
    infilled core; the gasket ribs (1.25 mm) + the window LIP bond carry the seal.
  * FLOOR 4 mm (>=6 fused bottom layers) for a watertight base.
  * Mount ears EMBED 4 mm into the wall so they fuse with the body into ONE connected first-layer
    footprint (a touching-but-not-overlapping ear slices as detached islands).
  * WALL gasket: the foam-gasket groove leaves a >=1.2 mm rib each side; thinner ribs will not
    slice, seal, or bond.
  * Coax bore is a TEARDROP with a FLAT BOTTOM held >=3 mm above the floor — no thin web at the
    bottom of the wall (leak path) and no unprintable crown overhang. + zip-tie strain relief.
  * WINDOW-LOCATING LIP: the acrylic drops into an outer lip and rests on a hard ledge, so the air
    gap is set by GEOMETRY (gap = wall_top - board_top), not by uncontrolled foam compression; the
    window stands ~1 mm proud as a drip edge. The cut sheet is spec'd undersized (lip + clearance).
  * Standoffs are ALL-PLASTIC: a NYLON M3 screw self-taps straight into the printed boss (pilot
    2.5 mm). No metal anywhere at or above the ground plane -> RF-safe on the patch side.
  * BREATHER VENT (ePTFE/Gore patch) in the floor (RF-safe behind the GP) defeats condensation in a
    permanently-sealed box across -15..55 C — a dew film on the radome is high-eps and wrecks the CP.
    It sits at (50,50), clear of the standoff bosses.
  * Inner floor/wall + boss-base fillets relieve ABS cooling stress; ears trimmed to fit a 220 bed
    with brim room.

THE ANTENNA: 160x160x1.6 mm RHCP single-feed corner-truncated patch, 869.525 MHz, boresight = +Z out
of the PATCH (top) face; B.Cu ground = bottom face. It is eps-FRAGILE (AR<=3 band ~6.5 MHz; eps +
thermal walk the null ~10 + ~8 MHz) so a PER-BOARD cold-AR gate is REQUIRED — see the SEAL SEQUENCE
below, which makes that gate possible on a glued-shut box.

Usage:
    python casing/enclosure.py              # emit .scad + render PNGs + export STL/DXF
    python casing/enclosure.py --no-render   # just emit the .scad
"""

import argparse
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import config  # noqa: E402

# ── board interface (the SAME numbers the PCB is built from) ──────────────────
BOARD_EDGE = 2.0 * config.SUB_HW_DEFAULT      # 160 mm
BOARD_TH   = config.substrate_thickness       # 1.6 mm
PATCH_W    = config.W_CP_INIT                  # ~82.5 mm (clearance / viz)
HOLE_OFF   = config.HOLE_OFF                    # M3 corner inset — single source: config.py
BOARD_R    = 6.0                               # board corner radius (mirrors kicad_export)

# ── enclosure parameters (mm) ─────────────────────────────────────────────────
CLEAR        = 1.0     # board-edge -> cavity-wall gap
WALL         = 4.0     # side wall — thin enough to print ALL-PERIMETER solid (watertight) at >=4
                       # perimeters; a 6 mm wall sliced with an infilled (porous) core. The seal is
                       # carried by the gasket ribs + the window LIP bond, not a thick flat land.
FLOOR        = 4.0     # floor (>=6 fused bottom layers at 0.2 mm)
STANDOFF_H   = 6.0     # board height off the floor (coax routing gap underneath)
AIR_GAP      = 10.0    # patch top -> window inner face (RF: keep >=8; >12 buys ~nothing)
WINDOW_TH    = 3.0     # acrylic sheet thickness (SPEC, not a guess — feeds the radome pre-comp sim)
EXT_R        = 10.0    # outer corner radius (softer / sleeker; cavity corner = ext_r-wall = board R6)
FILLET       = 2.0     # inner floor/wall + boss-base chamfer (ABS stress relief)
# standoffs — ALL-PLASTIC: nylon M3 screw self-taps straight into the printed boss (no metal near
# the antenna at all). The insert/screw RF concern is moot; loads are trivial; assembled once + sealed.
STANDOFF_OD  = 7.0
STANDOFF_PILOT = 2.5   # nylon M3 self-tap pilot (boss wall = (7-2.5)/2 = 2.25 mm)
# foam-gasket groove (in the wall top, inboard) + outer structural bond land
GASKET_INSET = 1.25    # inner rib: cavity wall -> groove
GASKET_W     = 1.5     # foam-cord groove width (ribs = 1.25 in / 1.25 out, ~3 perimeters each)
GASKET_D     = 1.0     # groove depth (compliant cord; shallow = stronger ribs)
# acrylic-window locating lip / drip edge
LIP_W        = 1.5     # outer locating-lip width
LIP_H        = 2.0     # lip height above the window seat (window stands WINDOW_TH-LIP_H proud)
WIN_CLEAR    = 0.4     # radial window-to-lip clearance (sealant-filled)
# coax / SMA feed-through (-Y wall, board plane)
SMA_D        = 12.0    # bore (verify vs real coax OD + boot + potting annulus)
WEB_MIN      = 3.0     # min solid wall below the bore (flat-bottom teardrop holds this)
ZIP_D        = 3.5     # 2x zip-tie strain-relief holes flanking the bore
# breather vent (ePTFE/Gore patch, floor, behind GP -> RF-safe)
VENT         = True
VENT_D       = 6.0     # vent through-hole
VENT_SEAT_D  = 14.0    # exterior recess for the adhesive vent patch
VENT_X       = 50.0    # vent centre — clear of the 4 standoff bosses (auto-checked) and cavity wall
VENT_Y       = 50.0
# mount ears (+/-X, coplanar with floor -> print flat, no leak path, behind GP -> RF-safe)
EAR_LEN      = 12.0
EAR_W        = 30.0
EAR_HOLE_D   = 4.5     # M4 clearance
# print-fit guard
BED          = 220.0   # printer bed (axis)
BRIM         = 8.0     # brim allowance (ABS/ASA)
# cosmetics — exterior only, RF-neutral; shallow wall debossing stays watertight (4 mm wall - 0.6)
LIP_BEVEL    = 1.0     # window-bezel: the outer lip face tapers in this much toward the top
BRAND_L1     = "SPACEFLIGHT ROCKETRY GIESSEN"
BRAND_L2     = "869.525 MHz   RHCP"
BRAND_SIZE   = 6.0     # debossed text cap height
BRAND_DEPTH  = 0.6     # deboss depth into the wall
DECO_ON      = True    # deboss the sunburst (archive/corner_deco.svg) on the +X wall
DECO_SZ      = 36.0
# relative to the .scad's dir (casing/) so the emitted model stays repo-portable — no absolute host path
DECO_SVG     = os.path.relpath(os.path.join(_ROOT, "archive", "corner_deco.svg"), _HERE).replace("\\", "/")
FN           = 96

# ── derived ───────────────────────────────────────────────────────────────────
CAV        = BOARD_EDGE + 2 * CLEAR                  # 162
EXT        = CAV + 2 * WALL                          # 174
BOARD_BOT  = FLOOR + STANDOFF_H                      # 10.0 — board underside (B.Cu ground plane)
BOARD_TOP  = BOARD_BOT + BOARD_TH                    # 11.6 — patch plane
WALL_TOP   = BOARD_TOP + AIR_GAP                     # 21.6 — window seat ledge (sets the air gap)
SMA_Z      = BOARD_BOT + BOARD_TH / 2.0              # 10.8 — coax bore centre
WEB_FLOOR  = FLOOR + WEB_MIN                         # 7.0  — flat bottom of the coax bore
HOLE_XY    = BOARD_EDGE / 2.0 - HOLE_OFF             # 72   — standoff boss centre
LIP_TOP    = WALL_TOP + LIP_H                        # 23.6
EXT_H      = WALL_TOP + WINDOW_TH                    # 24.6 — total stack (window stands proud of lip)
WINDOW     = EXT - 2 * LIP_W - 2 * WIN_CLEAR         # 170.2 — acrylic cut size (drops inside the lip)
OUTER_LAND = WALL - GASKET_INSET - GASKET_W          # 1.25 — outer gasket rib (the window LIP bonds)
BOSS_WALL  = (STANDOFF_OD - STANDOFF_PILOT) / 2.0    # 1.8
BED_SPAN   = EXT + 2 * EAR_LEN                        # 198 — axis-aligned footprint incl. ears

# ── build-time DFM / seal / RF guards (a future param edit can't silently break these) ──
def _check():
    import math
    a = []
    if WEB_MIN < 3.0:                         a.append(f"coax web {WEB_MIN} < 3 mm")
    if SMA_Z + SMA_D * 0.6 >= WALL_TOP:       a.append("coax teardrop peak reaches the window seat")
    if GASKET_INSET < 1.2:                    a.append(f"inner gasket rib {GASKET_INSET} < 1.2 mm")
    if OUTER_LAND < 1.2:                      a.append(f"outer gasket rib {OUTER_LAND:.2f} < 1.2 mm")
    if BOSS_WALL < 1.6:                       a.append(f"standoff boss wall {BOSS_WALL:.1f} < 1.6 mm")
    if WINDOW <= CAV:                         a.append("window does not cover the cavity")
    if AIR_GAP < 8.0:                         a.append(f"air gap {AIR_GAP} < 8 mm (RF)")
    if BED_SPAN + 2 * BRIM > BED:             a.append(f"footprint+brim {BED_SPAN + 2*BRIM:.0f} > bed {BED:.0f}")
    if VENT:                                  # vent must clear every standoff boss AND the cavity wall
        vclr = min(math.hypot(VENT_X - sx * HOLE_XY, VENT_Y - sy * HOLE_XY)
                   for sx in (-1, 1) for sy in (-1, 1))
        if vclr < VENT_SEAT_D / 2 + STANDOFF_OD / 2 + 2:
            a.append(f"vent overlaps a standoff (centre dist {vclr:.1f} mm)")
        if max(abs(VENT_X), abs(VENT_Y)) > CAV / 2 - VENT_SEAT_D / 2 - 2:
            a.append("vent seat runs into the cavity wall")
    if a:
        raise SystemExit("enclosure.py DFM/seal asserts FAILED:\n  - " + "\n  - ".join(a))
_check()


def _params_block() -> str:
    return f"""// ===== AUTO-GENERATED by casing/enclosure.py — DO NOT hand-edit; change the Python =====
part        = "assembly";   // assembly | tray | window2d | section   (-D 'part="tray"')
board_edge={BOARD_EDGE:.3f}; board_th={BOARD_TH:.3f}; patch_w={PATCH_W:.3f}; board_r={BOARD_R:.3f};
hole_xy={HOLE_XY:.3f}; clear={CLEAR:.3f}; wall={WALL:.3f}; floor_th={FLOOR:.3f};
standoff_h={STANDOFF_H:.3f}; air_gap={AIR_GAP:.3f}; window_th={WINDOW_TH:.3f}; ext_r={EXT_R:.3f};
fillet={FILLET:.3f}; so_od={STANDOFF_OD:.3f}; so_pilot={STANDOFF_PILOT:.3f};
gasket_inset={GASKET_INSET:.3f}; gasket_w={GASKET_W:.3f}; gasket_d={GASKET_D:.3f};
lip_w={LIP_W:.3f}; lip_h={LIP_H:.3f}; win_clear={WIN_CLEAR:.3f};
sma_d={SMA_D:.3f}; sma_z={SMA_Z:.3f}; web_floor={WEB_FLOOR:.3f}; zip_d={ZIP_D:.3f};
vent={"true" if VENT else "false"}; vent_d={VENT_D:.3f}; vent_seat_d={VENT_SEAT_D:.3f}; vent_x={VENT_X:.3f}; vent_y={VENT_Y:.3f};
ear_len={EAR_LEN:.3f}; ear_w={EAR_W:.3f}; ear_hole_d={EAR_HOLE_D:.3f};
cav={CAV:.3f}; ext={EXT:.3f}; board_bot={BOARD_BOT:.3f}; board_top={BOARD_TOP:.3f};
wall_top={WALL_TOP:.3f}; lip_top={LIP_TOP:.3f}; window={WINDOW:.3f};
lip_bevel={LIP_BEVEL:.3f}; brand_size={BRAND_SIZE:.3f}; brand_depth={BRAND_DEPTH:.3f};
brand_l1="{BRAND_L1}"; brand_l2="{BRAND_L2}";
deco_on={"true" if DECO_ON else "false"}; deco_sz={DECO_SZ:.3f}; deco_svg="{DECO_SVG}";
$fn={FN};
"""


_BODY = r"""
module rrect(s, r) { offset(r = r) square(s - 2 * r, center = true); }
module rprism(s, r, h) { linear_extrude(height = h) rrect(s, max(0.01, r)); }

// four board standoff bosses (nylon M3 self-taps into the boss — no metal at/above the GP)
module standoffs() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * hole_xy, sy * hole_xy, floor_th])
            difference() {
                union() {
                    cylinder(d = so_od, h = standoff_h);
                    cylinder(d1 = so_od + 2 * fillet, d2 = so_od, h = fillet);   // base fillet
                }
                translate([0, 0, -0.1]) cylinder(d = so_pilot, h = standoff_h + 0.2);  // self-tap pilot bore
            }
}

// foam-gasket groove (inboard) cut into the wall top; outer land stays flat for the adhesive bond
module gasket_groove() {
    inner = cav + 2 * gasket_inset;
    outer = cav + 2 * (gasket_inset + gasket_w);
    translate([0, 0, wall_top - gasket_d])
        linear_extrude(height = gasket_d + 0.1)
            difference() { rrect(outer, ext_r); rrect(inner, ext_r); }
}

// outer locating lip the acrylic window drops into (sets the air gap by a hard ledge; drip edge).
// The OUTER face tapers in (a bezel) for a finished look; the inner pocket wall stays vertical.
module window_lip() {
    translate([0, 0, wall_top])
        difference() {
            linear_extrude(height = lip_h, scale = (ext - 2 * lip_bevel) / ext) rrect(ext, ext_r);
            translate([0, 0, -0.1]) rprism(ext - 2 * lip_w, ext_r, lip_h + 0.2);
        }
}

// coax / SMA feed-through: teardrop (bridgeable crown) with a FLAT bottom >=3 mm above the floor
module sma_cut() {
    yb = -ext / 2 - 1; len = wall + 2;
    intersection() {
        hull() {
            translate([0, yb, sma_z]) rotate([-90, 0, 0]) cylinder(d = sma_d, h = len);
            translate([0, yb, sma_z + sma_d * 0.55]) rotate([-90, 0, 0]) cylinder(d = 0.8, h = len);
        }
        translate([-sma_d, yb - 1, web_floor]) cube([2 * sma_d, len + 2, ext]);   // flat bottom
    }
    // 2x zip-tie strain-relief holes flanking the bore
    for (sx = [-1, 1])
        translate([sx * (sma_d / 2 + zip_d), yb, sma_z]) rotate([-90, 0, 0]) cylinder(d = zip_d, h = len);
}

// breather vent (floor, off-corner, behind the GP -> RF-safe): through-hole + exterior patch seat
module vent_cut() {
    if (vent) {
        translate([vent_x, vent_y, -0.1]) cylinder(d = vent_d, h = floor_th + 0.2);
        translate([vent_x, vent_y, -0.1]) cylinder(d = vent_seat_d, h = 0.8);    // exterior patch recess
    }
}

// flat mount ears on +/-X (coplanar with the floor; outside the sealed cavity). The root EMBEDS
// 'ov' mm into the wall so the ear FUSES with the body -> ONE connected first-layer footprint
// (a touching-but-not-overlapping ear slices as separate islands).
module ears() {
    ov = 4;                 // overlap into the wall (wall is 4 mm -> embeds to the cavity inner face)
    L  = ear_len + ov;
    for (sx = [-1, 1])
        translate([sx * (ext / 2 + (ear_len - ov) / 2), 0, 0])
            difference() {
                linear_extrude(floor_th) offset(r = 3) square([L - 6, ear_w - 6], center = true);
                for (sy = [-1, 1])
                    translate([sx * (L / 2 - 4.5), sy * ear_w * 0.28, -0.1])
                        cylinder(d = ear_hole_d, h = floor_th + 0.2);
            }
}

// debossed branding on the +Y outer wall (two lines) — exterior only, shallow, watertight-safe.
// mirror() in X so it reads correctly when viewed from outside (+Y, looking -Y).
module branding() {
    zs = [[brand_l1, wall_top * 0.60], [brand_l2, wall_top * 0.34]];
    for (i = [0:1])
        translate([0, ext / 2 + 0.1, zs[i][1]])
            rotate([90, 0, 0])
                linear_extrude(height = brand_depth + 0.2)
                    mirror([1, 0, 0])
                        text(zs[i][0], size = brand_size, halign = "center", valign = "center",
                             font = "Liberation Sans:style=Bold");
}

// debossed sunburst (archive/corner_deco.svg) on the +X outer wall (faces +X, cuts -X into the wall)
module deco() {
    if (deco_on)
        translate([ext / 2 - brand_depth, 0, wall_top * 0.5])
            rotate([0, 90, 0])
                linear_extrude(height = brand_depth + 0.2)
                    resize([deco_sz, deco_sz, 0], auto = true) import(deco_svg, center = true);
}

module tray() {
    cr = max(0.01, ext_r - wall);
    difference() {
        union() {
            rprism(ext, ext_r, wall_top);
            window_lip();
            ears();
        }
        // cavity with a 45-ish inner floor/wall fillet at the base
        translate([0, 0, floor_th])
            linear_extrude(height = fillet, scale = cav / (cav - 2 * fillet)) rrect(cav - 2 * fillet, cr);
        translate([0, 0, floor_th + fillet]) rprism(cav, cr, wall_top);
        gasket_groove();
        sma_cut();
        vent_cut();
        branding();
        deco();
    }
    standoffs();
}

module window3d() { translate([0, 0, wall_top]) rprism(window, ext_r, window_th); }
module window2d() { rrect(window, ext_r); }   // undersized cut outline -> DXF (lip + clearance)

module board_ph() {
    color([0.0, 0.45, 0.2]) translate([0, 0, board_bot]) rprism(board_edge, board_r, board_th);
    color([0.85, 0.65, 0.1]) translate([0, 0, board_top]) rprism(patch_w, 6, 0.4);
}

module assembly() {
    tray();
    board_ph();
    color([0.6, 0.8, 1.0, 0.35]) window3d();
}

module section() {
    difference() {
        assembly();
        translate([-ext, 0, -60]) cube([2 * ext, 2 * ext, 220]);   // clean half-space: remove y>0
    }
}

if (part == "assembly") assembly();
else if (part == "tray") tray();
else if (part == "window2d") window2d();
else if (part == "section") section();
"""


def emit_scad(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(_params_block() + _BODY)
    print(f"OpenSCAD model written : {path}")


def _openscad_bin():
    for c in (shutil.which("openscad"),
              r"C:\Program Files\OpenSCAD\openscad.exe",
              r"C:\Program Files (x86)\OpenSCAD\openscad.exe"):
        if c and os.path.exists(c):
            return c
    return None


def render_outputs(scad_path: str, out_dir: str) -> None:
    osc = _openscad_bin()
    if not osc:
        print("  ! OpenSCAD not found — skipping renders/exports (the .scad is still written).")
        return

    def run(args, tag):
        r = subprocess.run([osc, *args, scad_path], capture_output=True, text=True)
        print(f"  {'OK ' if r.returncode == 0 else '!! '}{tag}")
        if r.returncode != 0:
            print((r.stderr or r.stdout or "").strip()[-700:])

    run(["-o", os.path.join(out_dir, "enclosure_iso.png"), "--imgsize=1500,1050", "--projection=p",
         "--colorscheme=Tomorrow", "--camera=0,0,0,62,0,28,0", "--viewall", "--autocenter"], "iso render")
    run(["-o", os.path.join(out_dir, "enclosure_section.png"), "--imgsize=1500,1050", "--projection=o",
         "--colorscheme=Tomorrow", "--camera=0,0,0,90,0,0,0", "--viewall", "--autocenter",
         "-D", 'part="section"'], "section render")
    run(["-o", os.path.join(out_dir, "enclosure_tray.stl"), "-D", 'part="tray"'], "tray STL")
    run(["-o", os.path.join(out_dir, "radome_window.dxf"), "-D", 'part="window2d"'], "window DXF")


def main():
    ap = argparse.ArgumentParser(description="Patch-antenna enclosure (Python -> OpenSCAD).")
    ap.add_argument("--no-render", action="store_true", help="emit the .scad only")
    args = ap.parse_args()

    scad = os.path.join(_HERE, "enclosure.scad")
    emit_scad(scad)
    if not args.no_render:
        render_outputs(scad, _HERE)

    print()
    print("Enclosure summary")
    print(f"  Board held        : {BOARD_EDGE:.0f} x {BOARD_EDGE:.0f} x {BOARD_TH:.1f} mm, patch-up")
    print(f"  Tray external     : {EXT:.0f} x {EXT:.0f} x {WALL_TOP:.1f} mm  (+ {EAR_LEN:.0f} mm ears on +/-X)")
    print(f"  Footprint + brim  : {BED_SPAN:.0f} + 2x{BRIM:.0f} = {BED_SPAN + 2*BRIM:.0f} mm  (bed {BED:.0f}: fits axis-aligned; NO 45deg rotation room)")
    print(f"  Acrylic window    : {WINDOW:.1f} x {WINDOW:.1f} x {WINDOW_TH:.1f} mm, R{EXT_R:.0f}  (drops into the lip; radome_window.dxf)")
    print(f"  Patch->window gap : {AIR_GAP:.1f} mm, set by the LEDGE (hard stop, not foam)  -> total H {EXT_H:.1f} mm")
    print(f"  Wall / floor      : {WALL:.0f} / {FLOOR:.0f} mm (all-perimeter solid; gasket ribs {GASKET_INSET:.2f}/{OUTER_LAND:.2f} mm + window lip bond)")
    print(f"  Standoffs         : 4 x NYLON M3 self-tap @ (+/-{HOLE_XY:.0f}, +/-{HOLE_XY:.0f}), boss wall {BOSS_WALL:.1f} mm + base fillet")
    print(f"  Coax exit         : dia {SMA_D:.0f} teardrop, flat bottom z={WEB_FLOOR:.0f} ({WEB_MIN:.0f} mm web) + 2x zip-tie holes")
    print(f"  Vent              : {'dia %g ePTFE breather in floor (behind GP)' % VENT_D if VENT else 'OFF'}")
    print()
    print("PRINT     : ASA (best UV/outdoor) or PETG — NOT bare ABS on a cold open bed. >=4 perimeters,")
    print("            >=6 top/bottom layers, ~0.15-0.2 mm. If ABS/ASA: heated chamber + 8-10 mm brim +")
    print("            glue-stick/garolite. Tray prints open-side-UP, no supports. Water-test the BARE")
    print("            tray before bonding the window. Window/DXF = cut/laser PMMA (cast eps~2.6).")
    print("ADHESIVE  : flexible UV-stable plastics sealant (MS-polymer / PU / neutral silicone) on the")
    print("            outer bond land — NOT rigid epoxy or acrylic solvent cement (they won't bond")
    print("            PMMA<->ASA and craze over the ~0.8 mm CTE swing on a 170 mm joint).")
    print("BUILD/TEST/SEAL SEQUENCE (resolves the glued-shut vs cold-AR-gate conflict):")
    print("  1. Pre-comp the synthesis freq for THIS acrylic (eps/thickness/10 mm gap) + the real")
    print("     SMA-launch null shift, then fab + reflow the board; quick room-temp S11/AR sanity.")
    print("  2. Mount board on standoffs (NYLON M3, self-tapping). Route coax, connect TEMPORARILY.")
    print("  3. DRY-set the acrylic in the lip (clamps, NO glue) -> reproduces the radome detune + the")
    print("     hard-stop gap. ** HOLD POINT: run the per-board cold-AR gate at the COLD extreme. **")
    print("  4. PASS -> seal (the LAST wet steps): desiccant in the -Z corner; foam cord in the groove;")
    print("     flexible pot the coax (mask the board top so it can't wick onto the patch); bond the")
    print("     window on the outer land; let cure with the vent open. FAIL -> pull the dry window,")
    print("     re-bin/scrap only the board (fully recoverable).")
    print("RF        : nylon (or RTV-captured) board screws ONLY — no metal through the board / at z>=GP.")
    print("            Mast bracket clamps the FLOOR (-Z); never wrap metal up the walls to the GP edge,")
    print("            no metallised paint/foil inside, silica-gel (not metal-can) desiccant near the patch.")
    print("            The acrylic radome still pulls the CP null down a few MHz -> step 1 pre-comp.")


if __name__ == "__main__":
    main()

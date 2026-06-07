# -*- coding: utf-8 -*-
"""Patch antenna geometry shared by the FDTD model and the KiCad export.

A plain SQUARE patch with rectangular inset notches on its edges, fed by 50 Ω
microstrip lines from a branch-line (90° hybrid) coupler. See
``notched_square_polygon`` / ``dual_feed_layout`` and docs/migration-plan.md.

All coordinates are sim coordinates: origin at the patch centre, +Y up, lengths
in mm.  Z is handled by the caller (top copper sits at the substrate thickness).
"""

import numpy as np

import config


# ══════════════════════════════════════════════════════════════════════════
# Flat dual-feed design — square patch with inset notches + microstrip feeds
# ══════════════════════════════════════════════════════════════════════════

def _edge_notches(insets: list, edge: str) -> list:
    """(lo, hi, depth) intervals of removed copper on `edge`, in along-edge coords.

    Each inset dict is {edge, center, width, gap, depth}: the feed metal is
    `width` wide and the etched slot removes `width + 2*gap` of patch copper so a
    `gap` of substrate is left on each side of the feed where it enters.
    """
    out = []
    for ins in insets:
        if ins['edge'] != edge:
            continue
        half = ins['width'] / 2.0 + ins['gap']
        out.append((ins['center'] - half, ins['center'] + half, ins['depth']))
    return out


def notched_square_polygon(W: float, insets: list | None = None) -> list:
    """CCW vertices of a square patch (side W) with rectangular inset notches.

    `insets` is a list of {edge, center, width, gap, depth}. Each notch is a
    rectangular bite cut inward from its edge (a concave detour in the outline);
    the feed line metal (added separately) fills the centre of the slot and
    connects to the patch copper at the notch's inner wall.  Returns a list of
    (x, y) tuples; pass through `patch_polygon_array` for openEMS AddPolygon.
    """
    insets = insets or []
    h = W / 2.0
    pts: list = [(-h, -h)]

    # bottom edge: y=-h, traverse +x, notch carves inward (+y)
    for lo, hi, d in sorted(_edge_notches(insets, 'bottom')):
        pts += [(lo, -h), (lo, -h + d), (hi, -h + d), (hi, -h)]
    pts.append((h, -h))

    # right edge: x=+h, traverse +y, notch carves inward (-x)
    for lo, hi, d in sorted(_edge_notches(insets, 'right')):
        pts += [(h, lo), (h - d, lo), (h - d, hi), (h, hi)]
    pts.append((h, h))

    # top edge: y=+h, traverse -x, notch carves inward (-y)
    for lo, hi, d in sorted(_edge_notches(insets, 'top'), reverse=True):
        pts += [(hi, h), (hi, h - d), (lo, h - d), (lo, h)]
    pts.append((-h, h))

    # left edge: x=-h, traverse -y, notch carves inward (+x)
    for lo, hi, d in sorted(_edge_notches(insets, 'left'), reverse=True):
        pts += [(-h, hi), (-h + d, hi), (-h + d, lo), (-h, lo)]

    return pts


def patch_polygon_array(W: float, insets: list | None = None) -> np.ndarray:
    """Shape-(2, N) array (x-row, y-row) of the notched square for AddPolygon."""
    return np.array(notched_square_polygon(W, insets)).T


def branch_line_rects(cx: float, cy: float, arm: float,
                      w_h: float, w_v: float) -> tuple:
    """Four arm rectangles of a square branch-line ring + its corner (port) points.

    The ring is a square of side `arm` (corner-to-corner centre spacing = λg/4),
    centred at (cx, cy). Horizontal (top/bottom) arms have width `w_h`; vertical
    (left/right) arms have width `w_v`; the arms overlap at the corners so their
    union forms the junctions. In a 90° hybrid the through arms are Z0/√2 = 35.36 Ω
    and the shunt arms are Z0 = 50 Ω — pass widths accordingly for the orientation.

    Pure geometry: no port-role or impedance convention is baked in. Returns
    ``(arms, corners)`` where ``arms`` is a list of ``((x0, y0), (x1, y1))``
    rectangles and ``corners`` is ``{'TL','TR','BL','BR'}`` of (x, y) port points.
    """
    a = arm / 2.0
    L, R, B, T = cx - a, cx + a, cy - a, cy + a       # corner-line coordinates
    arms = [
        ((L, B - w_h / 2.0), (R, B + w_h / 2.0)),     # bottom  (horizontal)
        ((L, T - w_h / 2.0), (R, T + w_h / 2.0)),     # top     (horizontal)
        ((L - w_v / 2.0, B), (L + w_v / 2.0, T)),     # left    (vertical)
        ((R - w_v / 2.0, B), (R + w_v / 2.0, T)),     # right   (vertical)
    ]
    corners = {'TL': (L, T), 'TR': (R, T), 'BL': (L, B), 'BR': (R, B)}
    return arms, corners


def dual_feed_layout(p) -> dict:
    """Derive the full flat dual-feed layout (all coordinates) from PatchParams.

    LOCKED branch-line topology (ideal-TL S-matrix + Pozar): input = BL,
    isolated = BR, outputs = TL (-90 deg) & TR (+180 deg). RHCP at +z mapping:
    TL (leading) -> LEFT (-x) patch edge (excites E_x); TR (lagging) -> BOTTOM
    (-y) patch edge (excites E_y). The coupler sits in the -x/-y corner; the two
    feeds tap the patch at MIRROR points (xB = yL) and are kept EQUAL physical length
    by a -y U-detour on the TR feed (the old xB=yL+arm tap split the patch modes ~16%).

    Patch is centred at the origin (reuses the validated Stage-1 patch + MSL
    pattern); the finite board is OFFSET to enclose the coupler/feeds/stub. All
    copper is over ground with >= config.BOARD_MARGIN clearance (assert below).
    Returns a dict of coordinates consumed by model.build_full_sim and kicad_export.
    """
    h  = p.W_mm / 2.0
    a  = p.cpl_arm_mm / 2.0
    fw = config.FEED_W

    # ── coupler placement: TR corner a fixed copper gap below-left of patch BL ──
    cpl_tr = -h - (config.CPL_PATCH_GAP + p.cpl_w35_mm / 2.0)   # TR corner (x == y)
    cx = cy = cpl_tr - a
    arms, corners = branch_line_rects(cx, cy, p.cpl_arm_mm,
                                      w_h=p.cpl_w50_mm, w_v=p.cpl_w35_mm)
    BL, BR, TL, TR = corners['BL'], corners['BR'], corners['TL'], corners['TR']

    # ── feed taps: SYMMETRIC across the patch y=x diagonal ─────────────────────
    # Left feed taps the -x edge at y=yL; bottom feed taps the -y edge at the MIRROR
    # point x=xB=yL (NOT yL+arm). The old xB=yL+arm tap made the two L-feeds equal
    # length but forced the TR->bottom feed to run a ~74 mm strip 3.6 mm PARALLEL to
    # the bottom radiating edge, loading ONLY the E_y mode and splitting the two patch
    # modes ~16% (run 20260606_130152: 138.8 MHz split -> AR 5.3 dB, broken CP). The
    # symmetric tap mirrors the bottom inset onto the left inset; the lost length is
    # restored by a U-detour routed AWAY from the patch into -y, NOT along the edge.
    yL = -a                            # LEFT-edge feed height  (output TL -> E_x)
    xB = yL                            # BOTTOM-edge feed pos.  (output TR -> E_y) = mirror of yL
    left_fp   = (-h, yL)
    bottom_fp = (xB, -h)

    # GUARD: the two symmetric insets are deep bites on ADJACENT edges near the lower-
    # left corner; if the depth approaches the tap-to-corner distance (yL + h) they
    # OVERLAP, self-intersecting the patch polygon (MALFORMED patch -> garbage sim).
    # This silently bit run 20260606 at small W (W=73/arm=48, W=75/arm=40). Cap each
    # inset so its notch inner end clears the perpendicular notch by >=1 mm; warn when
    # reduced (the cap changes the impedance match, so re-tune).
    _hw = fw / 2.0 + config.INSET_GAP
    _max_inset = (yL + h) - _hw - 1.0
    assert _max_inset > 1.0, f'patch too small for any inset (W={p.W_mm:.1f}, arm={p.cpl_arm_mm:.1f})'
    inset_x = min(p.inset_x_mm, _max_inset)
    inset_y = min(p.inset_y_mm, _max_inset)
    if inset_x < p.inset_x_mm - 1e-9 or inset_y < p.inset_y_mm - 1e-9:
        print(f'  ! inset capped {p.inset_x_mm:.1f}->{min(inset_x, inset_y):.1f} mm to stop the two '
              f'patch notches colliding (W={p.W_mm:.1f}, arm={p.cpl_arm_mm:.1f})', flush=True)

    # TL -> LEFT: vertical leg up to yL, then horizontal leg (+ inset) to the edge
    tl_vleg = ((TL[0] - fw / 2, TL[1]), (TL[0] + fw / 2, yL))
    tl_hleg = ((TL[0] - fw / 2, yL - fw / 2), (-h + inset_x, yL + fw / 2))
    len_tl  = (yL - TL[1]) + ((-h + inset_x) - TL[0])   # centreline length to match

    # TR -> BOTTOM: route to the mirror tap x=xB via a U-detour into -y so it does NOT
    # parallel the bottom edge. Path: right (h1) -> down (v1) -> right (h2) -> up into
    # the bottom inset (v2). The down-leg x is midway TR->tap (clears the coupler right
    # arm, sits below the patch); the detour depth y_low is solved so the TR centreline
    # length equals len_tl (preserves the coupler's 90 deg).
    down_x = (TR[0] + xB) / 2.0
    y_low  = ((xB - TR[0]) + TR[1] + (-h + inset_y) - len_tl) / 2.0
    tr_h1 = ((TR[0],            TR[1] - fw / 2), (down_x + fw / 2, TR[1] + fw / 2))
    tr_v1 = ((down_x - fw / 2,  y_low),          (down_x + fw / 2, TR[1] + fw / 2))
    tr_h2 = ((down_x - fw / 2,  y_low - fw / 2), (xB + fw / 2,     y_low + fw / 2))
    tr_v2 = ((xB - fw / 2,      y_low - fw / 2), (xB + fw / 2,     -h + inset_y))
    assert down_x - fw / 2 > (cx + a + p.cpl_w35_mm / 2.0), 'TR detour overlaps coupler right arm'
    assert y_low < -h, 'TR detour must run below the patch (-y), not across the edge'

    # ── input stub (BL, -y) + isolated stub/R (BR, -y) ─────────────────────────
    stub_end = (BL[0], BL[1] - config.INPUT_STUB)
    iso_end  = (BR[0], BR[1] - config.ISO_STUB)

    # ── offset board: y=x-SYMMETRIC bbox so E_x and E_y see IDENTICAL ground ─────
    # The patch is at the origin (on the y=x line), so a square board is y=x-symmetric
    # iff its centre is on that line (bcx==bcy). A board OFF the diagonal gives the two
    # radiating-edge pairs (+x/-x vs +y/-y) unequal ground clearance, detuning the two
    # modes unequally and narrowing the CP (a secondary mode-degeneracy break — run
    # 20260606: +x 19 mm vs +y 8 mm of ground). The coupler+stub push -y deeper than
    # -x, so extend the shorter (-x) extent to match: xmin==ymin (xmax==ymax==h already)
    # -> board square centred on the diagonal -> equal ground past every patch edge.
    xmin_raw = cx - a - p.cpl_w35_mm / 2.0      # coupler left arm outer edge
    ymin_raw = stub_end[1]                      # input-stub bottom
    xmin = ymin = min(xmin_raw, ymin_raw)       # symmetric -x/-y extents -> bcx == bcy
    xmax = ymax = h                             # patch +x / +y edges
    board_center = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)   # on the y=x diagonal
    need = (h - xmin) / 2.0 + config.BOARD_MARGIN
    sub_hw = max(p.sub_hw_mm, need)

    insets = [dict(edge='left',   center=yL, width=fw, gap=config.INSET_GAP, depth=inset_x),
              dict(edge='bottom', center=xB, width=fw, gap=config.INSET_GAP, depth=inset_y)]

    return dict(
        h=h, a=a, fw=fw, corners=corners, BL=BL, BR=BR, TL=TL, TR=TR,
        left_fp=left_fp, bottom_fp=bottom_fp, yL=yL, xB=xB,
        coupler_arms=arms,
        feed_rects=[tl_vleg, tl_hleg, tr_h1, tr_v1, tr_h2, tr_v2],
        stub_end=stub_end, iso_end=iso_end, insets=insets,
        board_center=board_center, sub_hw=sub_hw,
        copper_bbox=(xmin, xmax, ymin, ymax),
    )

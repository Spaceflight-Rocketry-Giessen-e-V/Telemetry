# -*- coding: utf-8 -*-
"""Patch antenna geometry shared by the FDTD model and the KiCad export.

A near-square patch with two diagonally-opposite corners truncated (the CP
perturbation) and one inset microstrip feed on the −y edge centre — single-feed
corner-truncated RHCP, NO branch-line coupler. See ``notched_square_polygon``
(truncation + notches) and ``single_feed_layout``.

All coordinates are sim coordinates: origin at the patch centre, +Y up, lengths
in mm.  Z is handled by the caller (top copper sits at the substrate thickness).
"""

import numpy as np

import config


# ══════════════════════════════════════════════════════════════════════════
# Single-feed corner-truncated design — patch with chamfered corners + one inset feed
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


def notched_square_polygon(W: float, insets: list | None = None,
                           trunc: float = 0.0, diag: str = 'BLTR') -> list:
    """CCW vertices of a near-square patch with inset notches + truncated corners.

    `insets` is a list of {edge, center, width, gap, depth}. Each notch is a
    rectangular bite cut inward from its edge (a concave detour in the outline);
    the feed line metal (added separately) fills the centre of the slot and
    connects to the patch copper at the notch's inner wall.

    `trunc` (mm) chamfers two diagonally-opposite corners by a 45° cut of leg
    `trunc` — the CP perturbation. `diag` selects which pair: 'BLTR' truncates the
    bottom-left + top-right corners (→ RHCP at +z with a −y-edge feed, validated),
    'TLBR' the other diagonal (→ LHCP / opposite sense). trunc=0 → plain square
    (backward-compatible). Returns (x, y) tuples; see `patch_polygon_array`.
    """
    insets = insets or []
    h = W / 2.0
    d = trunc
    cham = {'BL': False, 'BR': False, 'TR': False, 'TL': False}
    if d > 0.0:
        if diag == 'BLTR':
            cham['BL'] = cham['TR'] = True
        elif diag == 'TLBR':
            cham['TL'] = cham['BR'] = True
        else:
            raise ValueError(f"diag must be 'BLTR' or 'TLBR', got {diag!r}")

    # BL corner / start
    pts: list = [(-h + d, -h)] if cham['BL'] else [(-h, -h)]
    # bottom edge: y=-h, +x, notch carves inward (+y)
    for lo, hi, dep in sorted(_edge_notches(insets, 'bottom')):
        pts += [(lo, -h), (lo, -h + dep), (hi, -h + dep), (hi, -h)]
    # BR corner
    pts += [(h - d, -h), (h, -h + d)] if cham['BR'] else [(h, -h)]
    # right edge: x=+h, +y, notch carves inward (-x)
    for lo, hi, dep in sorted(_edge_notches(insets, 'right')):
        pts += [(h, lo), (h - dep, lo), (h - dep, hi), (h, hi)]
    # TR corner
    pts += [(h, h - d), (h - d, h)] if cham['TR'] else [(h, h)]
    # top edge: y=+h, -x, notch carves inward (-y)
    for lo, hi, dep in sorted(_edge_notches(insets, 'top'), reverse=True):
        pts += [(hi, h), (hi, h - dep), (lo, h - dep), (lo, h)]
    # TL corner
    pts += [(-h + d, h), (-h, h - d)] if cham['TL'] else [(-h, h)]
    # left edge: x=-h, -y, notch carves inward (+x)
    for lo, hi, dep in sorted(_edge_notches(insets, 'left'), reverse=True):
        pts += [(-h, hi), (-h + dep, hi), (-h + dep, lo), (-h, lo)]
    # close the BL chamfer (its top point joins back to the start)
    if cham['BL']:
        pts.append((-h, -h + d))
    return pts


def patch_polygon_array(W: float, insets: list | None = None,
                        trunc: float = 0.0, diag: str = 'BLTR') -> np.ndarray:
    """Shape-(2, N) array (x-row, y-row) of the truncated notched patch for AddPolygon."""
    return np.array(notched_square_polygon(W, insets, trunc, diag)).T


def single_feed_layout(p) -> dict:
    """Derive the single-feed corner-truncated CP layout from PatchParams.

    A near-square patch is centred at the origin with two diagonally-opposite
    corners truncated by ``p.trunc_mm`` (the CP perturbation, diagonal 'BLTR' →
    RHCP at +z). ONE inset microstrip feed enters the centre of the −y (bottom)
    edge to depth ``p.inset_y_mm`` and runs out to a Feed_R-terminated MSL port
    (so the board stays finite — nothing crosses the NF2FF surface). The board is
    a square centred at the origin, sized to the patch + ``config.BOARD_MARGIN``
    (or ``p.sub_hw_mm``, whichever is larger). Returns the coordinates consumed by
    model.build_patch_sim, postproc and kicad_export.
    """
    h     = p.W_mm / 2.0
    fw    = config.FEED_W
    trunc = p.trunc_mm
    inset = p.inset_y_mm
    diag  = 'BLTR'                      # RHCP at +z (validated); 'TLBR' = LHCP

    # one bottom-edge centre inset feed (excites both truncation-split modes)
    insets   = [dict(edge='bottom', center=0.0, width=fw, gap=config.INSET_GAP, depth=inset)]
    feed_fp  = (0.0, -h)               # feed point at the −y edge centre
    feed_x0  = -fw / 2.0
    feed_x1  =  fw / 2.0
    feed_y_patch = -h + inset          # inner end of the inset (joins the patch)

    # board: square, centred at origin, holds the patch + margin
    need   = h + config.BOARD_MARGIN
    sub_hw = max(p.sub_hw_mm, need)

    return dict(
        h=h, fw=fw, trunc=trunc, diag=diag, insets=insets,
        feed_fp=feed_fp, feed_x=(feed_x0, feed_x1), feed_y_patch=feed_y_patch,
        board_center=(0.0, 0.0), sub_hw=sub_hw,
        copper_bbox=(-h, h, -h, h),
    )

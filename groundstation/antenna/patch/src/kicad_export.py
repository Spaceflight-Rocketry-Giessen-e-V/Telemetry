# -*- coding: utf-8 -*-
"""Convert the single-feed corner-truncated RHCP patch geometry to a KiCad 7/8 PCB.

ONE 2-layer board, re-derived from the SAME geometry.single_feed_layout(PatchParams)
the FDTD model builds - so the exported copper matches the simulated copper:

  F.Cu       - near-square patch with two diagonally-opposite corners truncated (CP)
               + inset notch + one 50 Ω feed line to the edge SMA land
  B.Cu       - full ground plane (whole board)
  Edge.Cuts  - board outline (= substrate / ground edge) + 4× M3 holes
  F.SilkS    - datasheet labels (incl. the WR-SMA connector part number)

The single 50 Ω feed runs from the −y edge inset (board centre) to the board edge
and terminates in the WR-SMA 60312202114514 end-launch land pattern: it necks from
3.2 mm down to the connector's 0.61 mm centre-tab land, flanked by two ground pads
(WE's recommended span) stitched to the B.Cu plane. No coupler, no termination
resistor (the dual-feed coupler dumped ~64 % of accepted power into one).

Can be called programmatically via write_kicad_pcb(p, ...) from run.py, or used as
a standalone CLI:

  python -m src.kicad_export results.json
  python -m src.kicad_export --W 82.5 --trunc 8.25 --inset 5.8
  python -m src.kicad_export results.json -o my_board.kicad_pcb
"""

import argparse
import json
import math
import os
import re

import config
from src.geometry import single_feed_layout, notched_square_polygon
from src.params import PatchParams, default_params

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')


def _pts_str(verts) -> str:
    return ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in verts)


def _rect_corners(c0, c1) -> list:
    """Four sim-coord corners of an axis-aligned rectangle from two opposite ones.

    Robust to corner ordering (some layout rects give max-then-min corners).
    """
    (x0, y0), (x1, y1) = c0, c1
    xlo, xhi = sorted((x0, x1))
    ylo, yhi = sorted((y0, y1))
    return [(xlo, ylo), (xhi, ylo), (xhi, yhi), (xlo, yhi)]


def _qr_code_lines(data: str, x0: float, y0: float, size_mm: float,
                   layer: str = 'F.SilkS') -> list:
    """Filled squares forming a QR code for `data`, top-left corner at (x0, y0) in
    KiCad mm, ~`size_mm` square, on `layer`. Uses segno (optional); returns [] with a
    note if segno is missing so the export never hard-fails on the QR dependency.
    Place over a COPPER-FREE top area - silk over bare copper is dropped in fab.
    """
    try:
        import segno
    except Exception:
        print('  ! QR code skipped - run `pip install segno` to embed the repo QR.')
        return []
    qr   = segno.make(data, error='l')
    rows = [list(r) for r in qr.matrix]
    n    = len(rows)
    m    = size_mm / n
    out  = []
    for r, row in enumerate(rows):
        for c, bit in enumerate(row):
            if not bit:
                continue
            mx, my = x0 + c * m, y0 + r * m
            out += ['  (gr_rect',
                    f'    (start {mx:.4f} {my:.4f}) (end {mx + m:.4f} {my + m:.4f})',
                    f'    (layer "{layer}") (width 0) (fill solid)',
                    '  )']
    print(f'  QR code: {n}x{n} modules @ {m:.2f} mm = {size_mm:.1f} mm sq -> {data}')
    return out


def _txt(s, x, y, layer='F.SilkS', size=1.0, just='left', mirror=False, bold=False, angle=0):
    """One silk gr_text. `mirror=True` for back-layer text (reads right from the back);
    `angle` (deg, CCW) rotates it - 90 = vertical, for labels parallel to vertical parts."""
    j  = (f'mirror {just}' if mirror else just)
    th = round(size * (0.18 if bold else 0.14), 3)
    at = f'{x:.4f} {y:.4f}' + (f' {angle:.0f}' if angle else '')
    return [f'  (gr_text "{s}"',
            f'    (at {at}) (layer "{layer}")',
            f'    (effects (font (size {size:.2f} {size:.2f}) (thickness {th})) (justify {j}))',
            '  )']


def _seg(x0, y0, x1, y1, layer='F.SilkS', w=0.15):
    return [f'  (gr_line (start {x0:.4f} {y0:.4f}) (end {x1:.4f} {y1:.4f}) '
            f'(layer "{layer}") (width {w}))']


def _dim(label, lx, ly, tx, ty, layer='F.SilkS', size=1.0):
    """A dimension callout: left-justified text at (lx,ly) + a leader to the part at
    (tx,ty) that STARTS past the text edge (no line-through-text overlap)."""
    w = len(label) * size * 0.72                      # approx rendered text width
    sx = (lx + w + 1.0) if tx >= lx else (lx - 1.0)   # start at the text edge facing the target
    return _txt(label, lx, ly, layer, size, 'left') + _seg(sx, ly, tx, ty, layer, 0.12)


def _silk_table(rows, x0, y0, col_w, row_h, layer, board_w=None, size=1.0):
    """Bordered table: grid lines + left-justified cell text, header row bold.

    `rows` = list of equal-length string lists. If `board_w` is given the table is
    mirrored onto a back layer (x -> board_w - x, text mirrored) so it reads correctly
    when the board is viewed from the back. Returns kicad_pcb lines.
    """
    mir = board_w is not None
    def X(x):
        return (board_w - x) if mir else x
    out = []
    ncol, nrow = len(col_w), len(rows)
    Wt, Ht = sum(col_w), nrow * row_h
    for i in range(nrow + 1):                                   # horizontal rules
        out += _seg(X(x0), y0 + i * row_h, X(x0 + Wt), y0 + i * row_h, layer, 0.12)
    cx = x0
    for j in range(ncol + 1):                                   # vertical rules
        out += _seg(X(cx), y0, X(cx), y0 + Ht, layer, 0.12)
        if j < ncol:
            cx += col_w[j]
    for i, row in enumerate(rows):                              # cell text
        cx = x0
        for j, cell in enumerate(row):
            out += _txt(cell, X(cx + 0.8), y0 + i * row_h + row_h * 0.66,
                        layer, size, 'left', mirror=mir, bold=(i == 0))
            cx += col_w[j]
    return out


def _rounded_rect_edge(W, R, layer='Edge.Cuts', w=0.1):
    """Board outline as a rounded square (side W, corner radius R): 4 lines + 4 arcs."""
    k = R / 2.0 ** 0.5
    out = []
    out += _seg(R, 0, W - R, 0, layer, w)            # top
    out += _seg(W, R, W, W - R, layer, w)            # right
    out += _seg(W - R, W, R, W, layer, w)            # bottom
    out += _seg(0, W - R, 0, R, layer, w)            # left
    for (sx, sy), (cx, cy), (ex, ey) in (
            ((0, R),     (R, R),         (R, 0)),         # TL
            ((W - R, 0), (W - R, R),     (W, R)),         # TR
            ((W, W - R), (W - R, W - R), (W - R, W)),     # BR
            ((R, W),     (R, W - R),     (0, W - R))):    # BL
        mx, my = cx + (sx - cx + ex - cx) / 2.0, cy + (sy - cy + ey - cy) / 2.0
        # pull the mid-point onto the arc radius
        import math
        ang = math.atan2(my - cy, mx - cx)
        mx, my = cx + R * math.cos(ang), cy + R * math.sin(ang)
        out += [f'  (gr_arc (start {sx:.4f} {sy:.4f}) (mid {mx:.4f} {my:.4f}) '
                f'(end {ex:.4f} {ey:.4f}) (layer "{layer}") (width {w}))']
    return out


_SVG_TOK = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')


def _axis_indicator(x, y, layer='F.SilkS', mirror=False, beam_deg=None):
    """Orientation widget at KiCad (x,y): +Z 'out-of-face' (circle+dot) = main beam /
    boresight, plus in-plane +X (right) / +Y (up) sim axes. The patch radiates out the
    FRONT (patch) face, so boresight/strongest coverage is +Z, perpendicular to the board."""
    R, L = 3.0, 8.0
    out = [f'  (gr_circle (center {x:.3f} {y:.3f}) (end {x+R:.3f} {y:.3f}) (layer "{layer}") (width 0.25))',
           f'  (gr_circle (center {x:.3f} {y:.3f}) (end {x+0.45:.3f} {y:.3f}) (layer "{layer}") (width 0.45) (fill solid))']
    out += _seg(x + R, y, x + R + L, y, layer, 0.25)                       # +X arrow (right)
    out += _seg(x + R + L, y, x + R + L - 1.6, y - 1.3, layer, 0.25)
    out += _seg(x + R + L, y, x + R + L - 1.6, y + 1.3, layer, 0.25)
    out += _txt('+X', x + R + L + 1.0, y + 0.4, layer, 1.1, 'left', mirror)
    out += _seg(x, y - R, x, y - R - L, layer, 0.25)                       # +Y arrow (up)
    out += _seg(x, y - R - L, x - 1.3, y - R - L + 1.6, layer, 0.25)
    out += _seg(x, y - R - L, x + 1.3, y - R - L + 1.6, layer, 0.25)
    out += _txt('+Y', x + 1.0, y - R - L - 0.6, layer, 1.1, 'left', mirror)
    out += _txt('+Z', x - R - 3.6, y + 0.4, layer, 1.0, 'left', mirror)
    return out


def _polar_pattern(cx, cy, r, phi_deg, val_dBi, layer='F.SilkS'):
    """XY-plane (azimuth) RHCP pattern polar, oriented to the BOARD frame: +X right,
    +Y up, +Z out-of-face at centre (= boresight / main beam). Grid circle + axes +
    labels + the pattern curve (radius ∝ normalised gain). Front layer only."""
    out = []
    cir = [(cx + r * math.cos(2*math.pi*k/48), cy + r * math.sin(2*math.pi*k/48))
           for k in range(49)]
    out.append(f'  (gr_poly (pts {_pts_str(cir)}) (layer "{layer}") (width 0.12) (fill none))')
    out += _seg(cx, cy, cx + r + 3, cy, layer, 0.2)                    # +X axis (right)
    out += _seg(cx + r + 3, cy, cx + r + 1.5, cy - 1.2, layer, 0.2)
    out += _seg(cx + r + 3, cy, cx + r + 1.5, cy + 1.2, layer, 0.2)
    out += _txt('+X', cx + r + 3.6, cy + 0.4, layer, 1.0)
    out += _seg(cx, cy, cx, cy - r - 3, layer, 0.2)                    # +Y axis (up = -y)
    out += _seg(cx, cy - r - 3, cx - 1.2, cy - r - 1.5, layer, 0.2)
    out += _seg(cx, cy - r - 3, cx + 1.2, cy - r - 1.5, layer, 0.2)
    out += _txt('+Y', cx + 0.8, cy - r - 3.2, layer, 1.0)
    out.append(f'  (gr_circle (center {cx:.3f} {cy:.3f}) (end {cx+0.5:.3f} {cy:.3f}) '
               f'(layer "{layer}") (width 0.5) (fill solid))')           # +Z out-of-face dot
    out += _txt('+Z', cx + 1.2, cy + 3.0, layer, 0.9)
    if phi_deg and val_dBi:
        vmin, vmax = min(val_dBi), max(val_dBi)
        rng = max(vmax - vmin, 4.0)
        curve = []
        for a, v in zip(phi_deg, val_dBi):
            rr = r * (0.30 + 0.68 * (v - vmin) / rng)
            ar = math.radians(a)
            curve.append((cx + rr * math.cos(ar), cy - rr * math.sin(ar)))   # +Y up
        curve.append(curve[0])
        out.append(f'  (gr_poly (pts {_pts_str(curve)}) (layer "{layer}") (width 0.3) (fill none))')
    return out


def _vtk_elev_cut(output_path):
    """No-re-sim elevation (XZ, phi=0/180) directivity cut from the existing NF2FF VTK.
    Reads <run>/vtk/farfield_rhcp.vtk (Directivity_dBi, 91 theta x 180 phi), returns
    (theta[-90..+90 step 2], dBi, stats) or (None, None, None) if the VTK is absent."""
    try:
        import numpy as np
        vtk = os.path.join(os.path.dirname(os.path.abspath(output_path)), 'vtk', 'farfield_rhcp.vtk')
        L = open(vtk, encoding='utf-8', errors='ignore').read().splitlines()
        si = next(i for i, l in enumerate(L) if l.startswith('SCALARS'))
        lt = next(i for i in range(si, len(L)) if L[i].startswith('LOOKUP_TABLE'))
        vals = []
        for l in L[lt + 1:]:
            l = l.strip()
            if not l or l[0].isalpha():
                break
            vals += [float(x) for x in l.split()]
        g = np.asarray(vals).reshape(91, 180)
        v = np.concatenate([g[1:46, 90][::-1], g[0:46, 0]])     # theta -90..-2 | 0..+90
        th = list(range(-90, 91, 2))
        bs, back = float(g[0, 0]), float(g[90, 0])              # boresight | back lobe (theta=180)
        lvl, cr = bs - 3.0, []
        for i in range(len(v) - 1):
            if (v[i] - lvl) * (v[i + 1] - lvl) < 0:
                cr.append(th[i] + (lvl - v[i]) / (v[i + 1] - v[i]) * (th[i + 1] - th[i]))
        stats = {'boresight': bs, 'back': back, 'fb': bs - back,
                 'lo': min(cr) if cr else None, 'hi': max(cr) if cr else None,
                 'hpbw': (max(cr) - min(cr)) if cr else None}
        return th, [float(x) for x in v], stats
    except Exception as e:
        print(f'  ! elevation cut skipped: {e}')
        return None, None, None


def _elev_chart(th, v, x0, x1, y0, y1, layer, vmin=-6.0, vmax=4.0):
    """Cartesian elevation pattern (directivity dBi vs theta -90..+90, boresight centred),
    drawn in KiCad coords on `layer`. theta is mapped so it reads -90(left)..+90(right) on
    the BACK view (theta=-90 at the higher kicad-x edge). x0<x1, y0=top, y1=bottom."""
    out = []
    cxk, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    def PX(t):
        return cxk - (t / 90.0) * half
    def PY(val):
        val = max(vmin, min(vmax, val))
        return y1 - (val - vmin) / (vmax - vmin) * (y1 - y0)
    out += _seg(x0, y1, x1, y1, layer, 0.15)            # bottom axis
    out += _seg(x0, y0, x1, y0, layer, 0.12)            # top
    out += _seg(x0, y0, x0, y1, layer, 0.12)            # +90 side (view right)
    out += _seg(x1, y0, x1, y1, layer, 0.15)            # -90 side (view left)
    for t in (-90, -45, 0, 45, 90):                     # theta ticks
        out += _seg(PX(t), y1, PX(t), y1 - 1.0, layer, 0.12)
    out += _seg(PX(0), y0, PX(0), y1, layer, 0.12)      # boresight (theta=0) guide
    bs = max(v)                                         # -3 dB half-power line (dashed)
    yl = PY(bs - 3.0)
    x = x0
    while x < x1 - 0.1:
        out += _seg(x, yl, min(x + 1.6, x1), yl, layer, 0.12)
        x += 3.2
    pts = [(PX(t), PY(val)) for t, val in zip(th, v)]   # pattern curve (open polyline)
    for i in range(len(pts) - 1):
        out += _seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], layer, 0.25)
    return out


def _vtk_boresight_beam(output_path):
    """No-re-sim boresight beam footprint from the NF2FF VTK. For each azimuth phi, the
    polar angle theta (deg) where RHCP directivity drops 3 dB below the global peak (the
    FRONT-hemisphere -3 dB beam edge). Returns (phi_deg[180], theta3dB[180], stats) or
    (None, None, None) if the VTK is absent. Grid g[theta_i, phi_i]: theta 0..180 / phi
    0..358, step 2 deg, row-major flat = theta_i*180 + phi_i."""
    try:
        import numpy as np
        vtk = os.path.join(os.path.dirname(os.path.abspath(output_path)), 'vtk', 'farfield_rhcp.vtk')
        L = open(vtk, encoding='utf-8', errors='ignore').read().splitlines()
        si = next(i for i, l in enumerate(L) if l.startswith('SCALARS'))
        lt = next(i for i in range(si, len(L)) if L[i].startswith('LOOKUP_TABLE'))
        vals = []
        for l in L[lt + 1:]:
            l = l.strip()
            if not l or l[0].isalpha():
                break
            vals += [float(x) for x in l.split()]
        g = np.asarray(vals).reshape(91, 180)
        gmax = float(g.max())
        lvl = gmax - 3.0
        phi_deg, t3 = [], []
        for j in range(180):
            te = 90.0                                   # fallback: clamp to horizon if no crossing
            for i in range(45):                         # upper hemisphere only (theta 0..88 deg)
                if (g[i, j] - lvl) >= 0 and (g[i + 1, j] - lvl) < 0:
                    te = i * 2.0 + (lvl - g[i, j]) / (g[i + 1, j] - g[i, j]) * 2.0
                    break
            phi_deg.append(j * 2.0)
            t3.append(float(te))
        ti, pi = np.unravel_index(int(np.argmax(g[:46, :])), g[:46, :].shape)
        stats = {'peak': gmax, 'boresight': float(g[0, 0]),
                 'peak_theta': float(ti * 2), 'peak_phi': float(pi * 2),
                 'hb_min': min(t3), 'hb_max': max(t3), 'hb_mean': sum(t3) / len(t3)}
        return phi_deg, t3, stats
    except Exception as e:
        print(f'  ! boresight beam skipped: {e}')
        return None, None, None


def _boresight_beam(cx, cy, r, phi_deg, theta3dB, stats, layer='F.SilkS', ar3_half_deg=None):
    """Boresight far-field 'beam footprint' = the +Z main beam seen looking INTO the front
    face. Centre = +Z boresight (theta=0); radius grows linearly with polar angle theta out
    to the theta=90 horizon at the rim; angular position = azimuth phi. Same front-view
    mapping as _polar_pattern (+X right, +Y up, CCW), so no flip. The closed -3 dB contour
    shows the real (asymmetric) beam; a dashed circle marks the AR<=3 CP cone; an x marks
    the (off-boresight) gain peak. Front layer only."""
    out = []
    for tr in (30, 60, 90):                             # theta reference rings (90 = horizon = rim)
        rr = r * tr / 90.0
        w = 0.15 if tr == 90 else 0.1
        ring = [(cx + rr * math.cos(2*math.pi*k/48), cy + rr * math.sin(2*math.pi*k/48))
                for k in range(49)]
        out.append(f'  (gr_poly (pts {_pts_str(ring)}) (layer "{layer}") (width {w}) (fill none))')
        out += _txt(f'{tr}', cx - 1.7, cy - rr + 0.3, layer, 0.7)      # ring label (theta deg) up-axis
    out += _seg(cx, cy, cx + r + 3, cy, layer, 0.2)                    # +X axis (right)
    out += _seg(cx + r + 3, cy, cx + r + 1.5, cy - 1.2, layer, 0.2)
    out += _seg(cx + r + 3, cy, cx + r + 1.5, cy + 1.2, layer, 0.2)
    out += _txt('+X', cx + r + 3.6, cy + 0.4, layer, 1.0)
    out += _seg(cx, cy, cx, cy - r - 3, layer, 0.2)                    # +Y axis (up = -y)
    out += _seg(cx, cy - r - 3, cx - 1.2, cy - r - 1.5, layer, 0.2)
    out += _seg(cx, cy - r - 3, cx + 1.2, cy - r - 1.5, layer, 0.2)
    out += _txt('+Y', cx + 0.8, cy - r - 3.2, layer, 1.0)
    out.append(f'  (gr_circle (center {cx:.3f} {cy:.3f}) (end {cx+0.5:.3f} {cy:.3f}) '
               f'(layer "{layer}") (width 0.5) (fill solid))')           # +Z boresight dot
    out += _txt('+Z', cx + 1.1, cy + 2.9, layer, 0.85)
    if ar3_half_deg:                                    # AR<=3 CP cone (dashed circle), worst over phi
        rr = r * ar3_half_deg / 90.0
        n = 48
        for k in range(0, n, 2):
            a0, a1 = 2*math.pi*k/n, 2*math.pi*(k+1)/n
            out += _seg(cx + rr*math.cos(a0), cy + rr*math.sin(a0),
                        cx + rr*math.cos(a1), cy + rr*math.sin(a1), layer, 0.15)
    if phi_deg and theta3dB:                            # -3 dB beam contour (radius = theta/90)
        curve = []
        for a, t in zip(phi_deg, theta3dB):
            rr = r * t / 90.0
            ar = math.radians(a)
            curve.append((cx + rr * math.cos(ar), cy - rr * math.sin(ar)))   # +Y up, CCW
        curve.append(curve[0])
        out.append(f'  (gr_poly (pts {_pts_str(curve)}) (layer "{layer}") (width 0.3) (fill none))')
    if stats and stats.get('peak_theta') is not None:  # gain peak (off-boresight) marker
        pr = r * stats['peak_theta'] / 90.0
        pa = math.radians(stats['peak_phi'])
        px, py = cx + pr*math.cos(pa), cy - pr*math.sin(pa)
        out += _seg(px-0.8, py-0.8, px+0.8, py+0.8, layer, 0.2)
        out += _seg(px-0.8, py+0.8, px+0.8, py-0.8, layer, 0.2)
        out += _txt('peak', px - 5.6, py + 0.4, layer, 0.7)
    return out


def _rocket(x, y, length, layer='F.SilkS', mirror=False, board_w=None):
    """Small rocket silhouette pointing +X (nose at x+length), centred at y. Silk gr_poly."""
    pts = [(1.00, 0.0), (0.60, 0.15), (0.08, 0.15), (-0.04, 0.32), (-0.18, 0.15),
           (-0.18, -0.15), (-0.04, -0.32), (0.08, -0.15), (0.60, -0.15)]
    poly = []
    for px, py in pts:
        X = x + px * length
        Y = y - py * length
        if mirror and board_w is not None:
            X = board_w - X
        poly.append((X, Y))
    return [f'  (gr_poly (pts {_pts_str(poly)}) (layer "{layer}") (width 0) (fill solid))']


def _svg_path_polys(d: str, steps: int = 14) -> list:
    """Flatten an SVG path 'd' string to subpaths [[(x,y),...], ...] in SVG units.

    Handles M/L/H/V/C/S/Q/T/Z (abs+rel) with cubic/quadratic Bézier flattening; arcs
    (A) are approximated by their end-point chord (the logos here don't use arcs).
    """
    toks = _SVG_TOK.findall(d)
    i = 0; subs = []; cur = []
    x = y = sx = sy = 0.0; cmd = None; pcx = pcy = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v

    def cubic(x1, y1, x2, y2, nx, ny):
        for s in range(1, steps + 1):
            t = s / steps; m = 1 - t
            cur.append((m*m*m*x + 3*m*m*t*x1 + 3*m*t*t*x2 + t*t*t*nx,
                        m*m*m*y + 3*m*m*t*y1 + 3*m*t*t*y2 + t*t*t*ny))

    def quad(x1, y1, nx, ny):
        for s in range(1, steps + 1):
            t = s / steps; m = 1 - t
            cur.append((m*m*x + 2*m*t*x1 + t*t*nx, m*m*y + 2*m*t*y1 + t*t*ny))

    while i < len(toks):
        if _SVG_TOK.fullmatch(toks[i]) and toks[i].isalpha():
            cmd = toks[i]; i += 1
        if cmd in ('M', 'm'):
            nx, ny = num(), num()
            if cmd == 'm': nx += x; ny += y
            if cur: subs.append(cur)
            cur = [(nx, ny)]; x = sx = nx; y = sy = ny; cmd = 'L' if cmd == 'M' else 'l'; pcx = None
        elif cmd in ('L', 'l'):
            nx, ny = num(), num()
            if cmd == 'l': nx += x; ny += y
            cur.append((nx, ny)); x, y = nx, ny; pcx = None
        elif cmd in ('H', 'h'):
            nx = num(); nx += x if cmd == 'h' else 0
            cur.append((nx, y)); x = nx; pcx = None
        elif cmd in ('V', 'v'):
            ny = num(); ny += y if cmd == 'v' else 0
            cur.append((x, ny)); y = ny; pcx = None
        elif cmd in ('C', 'c'):
            x1, y1, x2, y2, nx, ny = (num() for _ in range(6))
            if cmd == 'c': x1 += x; y1 += y; x2 += x; y2 += y; nx += x; ny += y
            cubic(x1, y1, x2, y2, nx, ny); pcx, pcy = x2, y2; x, y = nx, ny
        elif cmd in ('S', 's'):
            x2, y2, nx, ny = (num() for _ in range(4))
            if cmd == 's': x2 += x; y2 += y; nx += x; ny += y
            x1 = 2*x - pcx if pcx is not None else x; y1 = 2*y - pcy if pcx is not None else y
            cubic(x1, y1, x2, y2, nx, ny); pcx, pcy = x2, y2; x, y = nx, ny
        elif cmd in ('Q', 'q'):
            x1, y1, nx, ny = (num() for _ in range(4))
            if cmd == 'q': x1 += x; y1 += y; nx += x; ny += y
            quad(x1, y1, nx, ny); pcx, pcy = x1, y1; x, y = nx, ny
        elif cmd in ('T', 't'):
            nx, ny = num(), num()
            if cmd == 't': nx += x; ny += y
            x1 = 2*x - pcx if pcx is not None else x; y1 = 2*y - pcy if pcx is not None else y
            quad(x1, y1, nx, ny); pcx, pcy = x1, y1; x, y = nx, ny
        elif cmd in ('A', 'a'):
            _ = [num() for _ in range(5)]; nx, ny = num(), num()
            if cmd == 'a': nx += x; ny += y
            cur.append((nx, ny)); x, y = nx, ny; pcx = None
        elif cmd in ('Z', 'z'):
            if cur: cur.append((sx, sy)); subs.append(cur); cur = []
            x, y = sx, sy; pcx = None
        else:
            i += 1
    if cur: subs.append(cur)
    return subs


def _svg_silk(svg_file, cx, cy, target_mm, layer='F.SilkS', board_w=None, anchor='bbox'):
    """Place an SVG logo (single/multi-subpath) as filled silk, scaled to `target_mm`
    (longest side), centred at KiCad (cx, cy). `board_w` mirrors it onto a back layer.
    `anchor='centroid'` centres on the area centroid of the largest subpath instead of the
    bbox midpoint (the visual centre of a radial mark like a sunburst around a hole)."""
    try:
        with open(svg_file, encoding='utf-8') as f:
            txt = f.read()
        d = re.search(r'\sd="([^"]+)"', txt, re.S).group(1)
    except Exception as e:
        print(f'  ! logo skipped ({os.path.basename(svg_file)}): {e}')
        return []
    subs = _svg_path_polys(d)
    pts = [q for s in subs for q in s]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    if not xs:
        return []
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = target_mm / max(maxx - minx, maxy - miny, 1e-9)
    midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
    if anchor == 'centroid':                             # area centroid of the largest subpath
        big = max((s for s in subs if len(s) >= 3), default=None,
                  key=lambda s: (max(p[0] for p in s) - min(p[0] for p in s)) *
                                (max(p[1] for p in s) - min(p[1] for p in s)))
        if big:
            A2 = mx = my = 0.0
            for k in range(len(big)):
                x0, y0 = big[k]; x1, y1 = big[(k + 1) % len(big)]
                cr = x0 * y1 - x1 * y0
                A2 += cr; mx += (x0 + x1) * cr; my += (y0 + y1) * cr
            if abs(A2) > 1e-9:
                midx, midy = mx / (3 * A2), my / (3 * A2)
    def _tx(px, py):                                 # SVG y is down, like KiCad y -> no flip
        X = cx + (px - midx) * scale
        Y = cy + (py - midy) * scale
        return (board_w - X if board_w is not None else X, Y)

    polys = [s for s in subs if len(s) >= 3]
    if not polys:
        return []
    # ONE compound polygon via KEYHOLE bridges: take the largest-bbox subpath as the outer
    # boundary, then splice every other subpath in with a ZERO-AREA back-and-forth bridge
    # from the outer's first vertex. Opposite-wound subpaths knock out as HOLES (the emblem's
    # negative-space design) and the doubled bridge edges leave no slivers. Smooth VECTOR.
    def _area(s):
        xs = [q[0] for q in s]; ys = [q[1] for q in s]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))
    bi = max(range(len(polys)), key=lambda k: _area(polys[k]))
    a0 = _tx(*polys[bi][0])
    compound = [_tx(px, py) for px, py in polys[bi]] + [a0]
    for k, s in enumerate(polys):
        if k == bi:
            continue
        s0 = _tx(*s[0])
        compound += [s0] + [_tx(px, py) for px, py in s] + [s0, a0]
    print(f'  logo {os.path.basename(svg_file)}: {len(polys)} subpaths (keyhole), '
          f'{len(compound)} pts -> {target_mm:.0f} mm (vector)')
    return [f'  (gr_poly (pts {_pts_str(compound)}) (layer "{layer}") (width 0) (fill solid))']


def _svg_silk_raster(svg_file, cx, cy, target_mm, layer='F.SilkS', px_mm=0.16, board_w=None):
    """Rasterise an SVG logo (matplotlib, correct fill rule → holes preserved) and emit
    it as run-length silk rectangles. Use for multi-subpath / negative-space logos that
    a direct fill (`_svg_silk`) would blob. `board_w` mirrors onto a back layer."""
    try:
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.path as mpath, matplotlib.patches as mpatches, matplotlib.pyplot as plt
        with open(svg_file, encoding='utf-8') as f:
            d = re.search(r'\sd="([^"]+)"', f.read(), re.S).group(1)
    except Exception as e:
        print(f'  ! raster logo skipped ({os.path.basename(svg_file)}): {e}')
        return []
    subs = [s for s in _svg_path_polys(d) if len(s) >= 3]
    pts = [q for s in subs for q in s]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    scale = target_mm / max(w, h)
    tw, th = w * scale, h * scale
    nx = max(16, int(round(tw / px_mm))); ny = max(16, int(round(th / px_mm)))

    Path = mpath.Path
    verts = []; codes = []
    for s in subs:
        verts.append(s[0]); codes.append(Path.MOVETO)
        verts += s[1:]; codes += [Path.LINETO] * (len(s) - 1)
        verts.append(s[0]); codes.append(Path.CLOSEPOLY)
    fig = plt.figure(figsize=(nx / 100.0, ny / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.add_patch(mpatches.PathPatch(Path(verts, codes), fc='black', ec='none'))
    ax.set_xlim(minx, maxx); ax.set_ylim(maxy, miny)        # invert y: row 0 = top
    fig.canvas.draw()
    arr = np.asarray(fig.canvas.buffer_rgba())[:, :, 0]
    plt.close(fig)
    mask = arr < 128                                          # True = ink
    H, W = mask.shape
    out = []
    for row in range(H):
        c = 0
        while c < W:
            if mask[row, c]:
                c0 = c
                while c < W and mask[row, c]:
                    c += 1
                x0 = cx - tw / 2 + c0 / W * tw; x1 = cx - tw / 2 + c / W * tw
                y0 = cy - th / 2 + row / H * th; y1 = cy - th / 2 + (row + 1) / H * th
                if board_w is not None:
                    x0, x1 = board_w - x0, board_w - x1
                xa, xb = sorted((x0, x1))
                out.append(f'  (gr_rect (start {xa:.3f} {y0:.3f}) (end {xb:.3f} {y1:.3f}) '
                           f'(layer "{layer}") (width 0) (fill solid))')
            else:
                c += 1
    print(f'  logo(raster) {os.path.basename(svg_file)}: {H}x{W}px -> {len(out)} rects')
    return out


def write_kicad_pcb(p: PatchParams, substrate_h: float, output_path: str) -> None:
    """Write a KiCad 7/8 .kicad_pcb for the single-feed corner-truncated RHCP patch.

    All geometry comes from geometry.single_feed_layout(p), the single source of
    truth shared with the FDTD model, so the board reproduces the simulated copper:
    a near-square patch with two diagonally-opposite corners truncated (CP), fed by
    ONE inset microstrip running to a bottom-centre edge-launch SMA. No coupler, no
    isolated-port resistor.
    """
    Lo       = single_feed_layout(p)
    bcx, bcy = Lo['board_center']                 # (0, 0) — patch centred
    sub_hw   = Lo['sub_hw']
    fw       = Lo['fw']
    h        = p.W_mm / 2.0
    board    = 2.0 * sub_hw                       # board edge length [mm]

    # Sim coords (patch-centre origin, +Y up) → KiCad coords (Y-down, (0,0) = TL).
    x_left = bcx - sub_hw
    y_top  = bcy + sub_hw
    def xf(x, y):
        return (x - x_left, y_top - y)

    def rect_k(c0, c1):
        return [xf(x, y) for x, y in _rect_corners(c0, c1)]

    # ── F.Cu copper polygons ──────────────────────────────────────────
    cu_polys = []

    # truncated patch (two diagonal chamfers + the bottom inset notch), at the origin
    cu_polys.append([xf(x, y) for x, y in
                     notched_square_polygon(p.W_mm, Lo['insets'], Lo['trunc'], Lo['diag'])])

    # ── single inset feed → WR-SMA end-launch land (Würth 60312202114514) ────────
    # The 50 Ω feed runs from the −y edge inset (x=0) straight down to the −Y board
    # edge, then necks to the connector's 0.61 mm centre-tab land via a short taper;
    # two flanking F.Cu ground pads (WE's land pattern) take the flat-tab ground legs
    # and are stitched to the B.Cu plane with vias (via section below). At 869.5 MHz
    # the neck is < λ/30 — electrically invisible, so the qualified WE launch is used
    # as-is. The feed is on the patch's mirror axis (x=0) so it does not unbalance the
    # two truncation-split modes.
    feed_y_patch = Lo['feed_y_patch']               # inner end of the inset (joins patch)
    board_ymin   = bcy - sub_hw                      # −Y board edge (launch plane)
    SIG_W, SIG_L    = 0.61, 2.30                     # centre-tab land: width × length
    TAPER_L         = 3.0                            # fw(50 Ω) -> tab-land neck length
    GND_L           = 5.0                            # flanking ground-pad length
    GND_IN, GND_OUT = 3.55, 4.95                     # ground-pad inner/outer edge from centreline
    y_tap = board_ymin + SIG_L                       # tab-land top (taper bottom)
    y_run = y_tap + TAPER_L                          # 50 Ω trace end (taper top)
    # 50 Ω feed trace from the patch inset down to the taper (centred on x=0)
    cu_polys.append(rect_k((-fw / 2, feed_y_patch), (fw / 2, y_run)))
    # neck taper fw -> SIG_W (trapezoid)
    cu_polys.append([xf(x, y) for x, y in (
        (-fw / 2, y_run), (fw / 2, y_run),
        (SIG_W / 2, y_tap), (-SIG_W / 2, y_tap))])
    # centre-tab signal land at the edge
    cu_polys.append(rect_k((-SIG_W / 2, y_tap), (SIG_W / 2, board_ymin)))
    # two flanking F.Cu ground pads (flat-tab ground legs)
    cu_polys.append(rect_k((-GND_OUT, board_ymin), (-GND_IN, board_ymin + GND_L)))
    cu_polys.append(rect_k(( GND_IN, board_ymin), ( GND_OUT, board_ymin + GND_L)))

    # ── B.Cu ground (whole board) + Edge.Cuts ─────────────────────────
    gnd_verts = [(0.0, 0.0), (board, 0.0), (board, board), (0.0, board)]

    # ── marker: edge-launch SMA (bottom-centre) ────────────────────────
    sma_kx, sma_ky = xf(0.0, board_ymin)          # launch at the board edge, centred

    lines = [
        '(kicad_pcb (version 20231231) (generator "sim_to_kicad")',
        f'  (general (thickness {substrate_h:.2f}))',
        '  (paper "A3")',
        '  (layers',
        '    (0 "F.Cu" signal)',
        '    (31 "B.Cu" signal)',
        '    (36 "B.SilkS" user "B.Silkscreen")',
        '    (37 "F.SilkS" user "F.Silkscreen")',
        '    (38 "B.Mask" user)',
        '    (39 "F.Mask" user)',
        '    (44 "Edge.Cuts" user)',
        '    (49 "F.Fab" user)',
        '  )',
        '  (setup (pad_to_mask_clearance 0))',
        '  (net 0 "")',
        '',
    ]

    # F.Cu copper
    for poly in cu_polys:
        lines += [
            '  (gr_poly',
            f'    (pts {_pts_str(poly)})',
            '    (layer "F.Cu") (width 0) (fill solid)',
            '  )',
            '',
        ]

    # B.Cu ground
    lines += [
        '  (gr_poly',
        f'    (pts {_pts_str(gnd_verts)})',
        '    (layer "B.Cu") (width 0) (fill solid)',
        '  )',
        '',
    ]

    # Edge.Cuts - rounded-corner board outline (6 mm radius: cleaner look, RF-neutral)
    lines += _rounded_rect_edge(board, 6.0)
    lines.append('')

    # ── Soldermask KEEP-OUT over ALL top copper (patch + feed + SMA lands) ────────────────
    # The FDTD sim models bare PEC copper; soldermask (~20 µm, εr~3.5) over the patch would
    # pull resonance DOWN ~5-10 MHz and detune the feed, so we OPEN F.Mask over EVERY
    # top-copper polygon -> the etched board matches the simulated copper (no unmodelled
    # dielectric loading - this is what makes NP-140F's known εr actually land on the bench).
    # Exposed copper takes the surface finish (HASL/ENIG) and is protected by the radome.
    # F.Mask polys are negative (= openings). cu_polys are already in KiCad coords.
    mask_polys = list(cu_polys)
    for poly in mask_polys:
        lines += [
            '  (gr_poly',
            f'    (pts {_pts_str(poly)})',
            '    (layer "F.Mask") (width 0) (fill solid)',
            '  )',
            '',
        ]

    # ── B.Mask: expose the bottom-side SMA ground lands ─────────────────────────
    # The WE 60312202114514 is an edge-launch with flat-tab ground wings that wrap the board
    # edge and solder to ground on BOTH faces (the datasheet land pattern shows a Bottom View
    # with the same 7.1/9.9 x 5.0 mm ground lands). Open B.Mask over the solid B.Cu pour under
    # the two ground pads so the bottom wings can be wetted. (Audit fix: B.Mask was never written.)
    bmask_polys = [
        rect_k((-GND_OUT, board_ymin), (-GND_IN, board_ymin + GND_L)),
        rect_k(( GND_IN, board_ymin), ( GND_OUT, board_ymin + GND_L)),
    ]
    for poly in bmask_polys:
        lines += [
            '  (gr_poly',
            f'    (pts {_pts_str(poly)})',
            '    (layer "B.Mask") (width 0) (fill solid)',
            '  )',
            '',
        ]

    # Edge-launch ground stitching: tie the two flanking F.Cu launch pads (centred on
    # x=0) to the B.Cu plane so the WR-SMA flat-tab ground legs see a solid edge ground.
    g_cx = (GND_IN + GND_OUT) / 2.0                  # ground-pad centreline offset
    for _sx in (-1.0, 1.0):
        for _gy in (board_ymin + 1.5, board_ymin + 3.5):
            _vkx, _vky = xf(_sx * g_cx, _gy)
            lines += [
                '  (via',
                f'    (at {_vkx:.4f} {_vky:.4f}) (size 0.8) (drill 0.4)',
                '    (layers "F.Cu" "B.Cu") (net 0)',
                '  )',
                '',
            ]

    # ════════════════ MOUNTING HOLES (4× M3, clear corners) ════════════════
    # The patch is centred with ~38 mm of ground at every corner, so all FOUR corners
    # are clear (the single feed exits the bottom EDGE centre, not a corner). Edge.Cuts
    # circle = routed hole. NYLON standoffs only (metal detunes the ground-plane edge).
    HOLE_D, HOLE_OFF = 3.2, 8.0                        # M3 clearance; inset clears the 6 mm radius
    for mx, my in ((HOLE_OFF, HOLE_OFF),
                   (HOLE_OFF, board - HOLE_OFF),
                   (board - HOLE_OFF, HOLE_OFF),
                   (board - HOLE_OFF, board - HOLE_OFF)):
        lines.append(f'  (gr_circle (center {mx:.4f} {my:.4f}) '
                     f'(end {mx + HOLE_D / 2:.4f} {my:.4f}) (layer "Edge.Cuts") (width 0.1))')
        lines += _txt('M3', mx + 2.6, my + 0.3, 'F.SilkS', 0.9)
    lines.append('')

    # ── shared positions / live performance for the back datasheet ──
    inset_cap = Lo['insets'][0]['depth']
    qkx, qky = xf(0.0, (h + sub_hw) / 2.0)             # QR anchor: clear ground strip above the patch
    res = {}
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(output_path)),
                               'results.json'), encoding='utf-8') as _rf:
            res = json.load(_rf)
    except Exception:
        pass

    # ════════════════ FRONT SILK ════════════════
    bdeg = res.get('ar3_beamwidth_deg', 56) if res else 56
    dmax = res.get('Dmax_dBi', 3.9) if res else 3.9

    # ── TOP-LEFT: datasheet header / description (logos moved to the bottom-left) ──
    epsr = res.get('substrate_epsR', 4.15) if res else 4.15
    s11  = res.get('s11_at_ft_dB', -11.0) if res else -11.0
    arb  = res.get('ar_boresight_dB', 1.6) if res else 1.6
    dx = 11.0                                            # left padding (moved in from the edge)
    lines += _txt('RHCP GROUNDSTATION PATCH', dx, 23.0, 'F.SilkS', 1.7, 'left', bold=True)
    lines += _txt(f'{config.f_target / 1e6:.3f} MHz    RHCP    single-feed corner-truncated',
                  dx, 28.5, 'F.SilkS', 1.2)
    lines += _txt(f'2-layer    {config.substrate_material} eps_r {epsr:.2f}    {substrate_h:.1f} mm    '
                  f'{board:.0f} x {board:.0f} mm', dx, 32.5, 'F.SilkS', 1.1)
    lines += _txt(f'S11 {s11:.0f} dB    Dmax {dmax:.1f} dBi', dx, 36.5, 'F.SilkS', 1.1)
    lines += _txt(f'AR {arb:.1f} dB    AR<=3 beam +/- {bdeg / 2:.0f} deg', dx, 40.5, 'F.SilkS', 1.1)
    lines += _txt('boresight = +Z (out of front face)', dx, 44.5, 'F.SilkS', 1.0)
    lines += _txt('Open Source Hardware', dx, 48.0, 'F.SilkS', 1.0)

    # ── BOTTOM-LEFT clear ground (below the centred patch): logos stacked going up
    #    (open-hardware lowest, our emblem above) on the bottom-left margin centreline ──
    logo_cx = (sub_hw - h) / 2.0                        # centre of the clear bottom-left strip (KiCad x)
    lines += _svg_silk(os.path.join(_ASSETS, 'logo.svg'), logo_cx, 133.0, 16.0)
    lines += _svg_silk(os.path.join(_ASSETS, 'brand-open-source-hardware.svg'), logo_cx, 150.0, 10.0)

    # (Front boresight-beam polar graph removed per request — the bottom-right is left clear;
    #  the elevation pattern still lives on the back-silk datasheet.)

    # ── dimensions: text on the clear ground beside each feature ──
    lines += _txt(f'Patch {p.W_mm:.1f} mm sq', logo_cx - 6.0, 50.0, 'F.SilkS', 1.0)     # left strip, beside patch
    lines += _txt(f'trunc {p.trunc_mm:.1f} mm', logo_cx - 6.0, 54.0, 'F.SilkS', 1.0)    #   corner-chamfer size
    lines += _txt(f'inset {inset_cap:.1f} mm', sma_kx + 4.0, sma_ky - 11.0, 'F.SilkS', 0.95)  # near the feed
    lines += _txt(f'feed 50R w{fw:.2f} mm', sma_kx + 4.0, sma_ky - 14.5, 'F.SilkS', 0.9)

    # SMA part label on bare substrate beside the launch land (no over-pad markers —
    # silk over exposed copper is dropped in fab).
    lines += _txt('WR-SMA 60312202114514', sma_kx + 4.0, sma_ky - 7.0, 'F.SilkS', 1.1)

    # QR on the clear ground strip above the patch, no caption
    qr_sz = 25.5
    lines += _qr_code_lines(
        'https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/tree/main',
        x0=qkx - qr_sz / 2.0, y0=qky - qr_sz / 2.0, size_mm=qr_sz)

    # ════════════════ BACK SILK - datasheet (mirrored to read from the back) ════════════════
    lines += _txt('Ground-station RHCP receive antenna - 869.5 MHz rocket telemetry downlink, '
                  'wide-beam backup', board - 12.0, 8.0, 'B.SilkS', 0.95, 'left', mirror=True)
    lines += _txt('RHCP SINGLE-FEED PATCH  -  DATASHEET', board - 12.0, 14.0,
                  'B.SilkS', 2.2, 'left', mirror=True, bold=True)
    rhcp = 'RHCP' if res.get('rhcp', True) else 'LHCP'
    dtable = [['PARAMETER', 'VALUE'],
              ['Frequency', f'{config.f_target / 1e6:.3f} MHz'],
              ['Polarisation', f'{rhcp} (corner-truncated)'],
              ['Patch (near-square)', f'{p.W_mm:.2f} mm'],
              ['Corner truncation', f'{p.trunc_mm:.2f} mm chamfer'],
              ['Feed 50R / inset', f'{fw:.2f} / {inset_cap:.2f} mm'],
              ['Board', f'{board:.0f} x {board:.0f} mm'],
              ['Substrate', f'{config.substrate_material}  er {config.substrate_epsR}  {substrate_h:.1f} mm']]
    if res:
        dtable += [['Return loss S11', f'{res.get("s11_at_ft_dB", 0):.1f} dB'],
                   ['Axial ratio', f'{res.get("ar_boresight_dB", 0):.2f} dB'],
                   ['AR<=3 beamwidth', f'{res.get("ar3_beamwidth_deg", 0):.0f} deg'],
                   ['Directivity', f'{res.get("Dmax_dBi", 0):.1f} dBi'],
                   ['Realised gain', f'{res.get("realised_gain_dBic", 0):.1f} dBic']]
    lines += _silk_table(dtable, 14.0, 20.0, [36.0, 50.0], 5.6, 'B.SilkS',
                         board_w=board, size=1.2)

    info = ['Hardware: edge-launch SMA (WE 60312202114514); no termination resistor',
            'Mounting: 4x M3, nylon standoffs only',
            'Main beam: boresight +Z, out of the front face',
            'github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry  -  Open Source Hardware',
            'Spaceflight Rocketry Giessen e.V.']
    for k, t in enumerate(info):
        lines += _txt(t, board - 12.0, 112.0 + k * 5.2, 'B.SilkS', 1.25, 'left',
                      mirror=True, bold=(k == len(info) - 1))

    # ── BACK right-side panel (kicad x14..58 == the empty RIGHT column on the back view,
    #    beside the table) : the elevation (XZ) cut the front lacks, sliced no-re-sim from the
    #    NF2FF VTK + a sunburst around the origin (TL) mounting hole.  Geometry is drawn in
    #    final kicad coords (theta mapped so the view reads -90..+90 L->R); text is mirror-left.
    # filled white silk disc under the rays so the mounting hole is FULLY ringed (the rays alone
    # converge to a point and leave green wedge gaps at the hole); the drilled hole then removes
    # the centre -> clean white annulus. Back silk prints over the soldermask, so this is fine.
    _hx, _hy = 8.0, board - 8.0
    lines.append(f'  (gr_circle (center {_hx:.3f} {_hy:.3f}) (end {_hx + 2.4:.3f} {_hy:.3f}) '
                 f'(layer "B.SilkS") (width 0) (fill solid))')
    lines += _svg_silk(os.path.join(_ASSETS, 'corner_deco.svg'),
                       board - 8.0, board - 8.0, 13.0, 'B.SilkS', board_w=board,
                       anchor='centroid')  # sunburst centred on the bottom-left hole (disc guarantees the ring)
    ax = 58.0                                                              # right kicad anchor (mirror-left)
    lines += _txt('ELEVATION PATTERN', ax, 28.0, 'B.SilkS', 1.4, 'left', mirror=True, bold=True)
    lines += _txt('XZ cut  phi = 0   (directivity)', ax, 32.0, 'B.SilkS', 1.0, 'left', mirror=True)
    th_e, v_e, st = _vtk_elev_cut(output_path)
    if th_e:
        lines += _elev_chart(th_e, v_e, 18.0, 56.0, 36.0, 68.0, 'B.SilkS')
        lines += _txt('-3 dB', 55.0, 45.7, 'B.SilkS', 0.8, 'left', mirror=True)  # half-power tag
        lines += _txt('-90', 56.0, 71.5, 'B.SilkS', 0.9, 'left', mirror=True)   # axis labels under ticks
        lines += _txt('0',   36.5, 71.5, 'B.SilkS', 0.9, 'left', mirror=True)
        lines += _txt('+90', 19.5, 71.5, 'B.SilkS', 0.9, 'left', mirror=True)
        lines += _txt('theta (deg)   -   +Z boresight at centre', ax, 75.5,
                      'B.SilkS', 0.9, 'left', mirror=True)
        hp = (f'{st["hpbw"]:.0f} deg ({st["lo"]:+.0f}/{st["hi"]:+.0f})' if st['hpbw'] else 'n/a')
        lines += _txt(f'boresight {st["boresight"]:.1f} dBi   HPBW {hp}   F/B {st["fb"]:.0f} dB',
                      ax, 80.5, 'B.SilkS', 1.0, 'left', mirror=True)
        lines += _txt('DIRECTIVITY (NF2FF); realised gain lower on FR-4-class',
                      ax, 84.5, 'B.SilkS', 0.9, 'left', mirror=True)
    else:
        lines += _txt('(elevation cut unavailable - VTK not found)', ax, 42.0,
                      'B.SilkS', 1.0, 'left', mirror=True)
    lines += _seg(14.0, 88.5, 58.0, 88.5, 'B.SilkS', 0.12)                # separator
    lines += _txt(f'Method: openEMS FDTD  @  {config.f_target / 1e6:.3f} MHz',
                  ax, 92.5, 'B.SilkS', 0.9, 'left', mirror=True)

    lines.append(')')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'KiCad PCB written : {output_path}')
    print(f'  Patch side   W   = {p.W_mm:.4f} mm (near-square)')
    print(f'  Corner trunc     = {p.trunc_mm:.4f} mm chamfer ({Lo["diag"]})')
    print(f'  Feed inset       = {p.inset_y_mm:.4f} mm  (50R w {fw:.2f} mm)')
    print(f'  Board size       = {board:.1f} x {board:.1f} mm')
    print(f'  SMA edge launch  = ({sma_kx:.2f}, {sma_ky:.2f}) mm from board TL (bottom centre)')
    print()
    print('Next steps in KiCad:')
    print('  1. Open the .kicad_pcb - F.Cu = patch + feed, B.Cu = ground. No coupler/resistor.')
    print('  2. The WR-SMA 60312202114514 end-launch land pattern is already drawn at')
    print('     the -Y edge centre: 0.61 mm centre-tab land + two flanking ground pads')
    print('     (stitched to B.Cu). Solder the flat tab to the tab land, ground legs to')
    print('     the flanking pads (top) and the B.Cu plane (bottom edge).')
    print('  3. NOTE: the whole top copper is soldermask-FREE (matches the bare-PEC sim);')
    print('     the fab plates the surface finish (HASL/ENIG) over it - the radome protects it.')
    print('  4. Mounting: 4x M3 holes at clear corners - use NYLON standoffs (a metal one')
    print('     would ground the GP edge to the chassis and detune the antenna).')
    print('  5. File -> Fabrication Outputs -> Gerbers -> Generate.')


def main():
    ap = argparse.ArgumentParser(
        description='Single-feed corner-truncated RHCP patch sim results → KiCad 7/8 PCB file')
    ap.add_argument('json_file', nargs='?',
                    help='Path to results.json written by run.py')
    ap.add_argument('--W',           type=float, help='Patch side [mm]')
    ap.add_argument('--trunc',       type=float, help='Corner truncation (chamfer) [mm]')
    ap.add_argument('--inset',       type=float, help='Feed inset depth [mm]')
    ap.add_argument('--sub_hw',      type=float, help='Substrate / GP half-width [mm]')
    ap.add_argument('--substrate_h', type=float, default=config.substrate_thickness,
                    help=f'Substrate thickness [mm] (default {config.substrate_thickness})')
    ap.add_argument('-o', '--output', default=None,
                    help='Output path (default: patch_antenna.kicad_pcb next to JSON)')
    args = ap.parse_args()

    # Base params: from results.json if given, else config synthesis seeds.
    if args.json_file:
        with open(args.json_file, encoding='utf-8') as f:
            data = json.load(f)
        p     = PatchParams.from_dict(data)
        sub_h = data.get('substrate_h_mm', args.substrate_h)
    else:
        p     = default_params()
        sub_h = args.substrate_h

    # CLI overrides (applied on top of the base params).
    overrides = {}
    if args.W      is not None: overrides['W_mm']       = args.W
    if args.trunc  is not None: overrides['trunc_mm']   = args.trunc
    if args.inset  is not None: overrides['inset_y_mm'] = args.inset
    if args.sub_hw is not None: overrides['sub_hw_mm']  = args.sub_hw
    if overrides:
        p = p.with_(**overrides)

    if not args.json_file and not overrides:
        print('Note: no results.json and no overrides - exporting from config seeds.')

    if args.output:
        output = args.output
    elif args.json_file:
        output = os.path.join(os.path.dirname(os.path.abspath(args.json_file)),
                              'patch_antenna.kicad_pcb')
    else:
        output = 'patch_antenna.kicad_pcb'

    write_kicad_pcb(p, substrate_h=sub_h, output_path=output)


if __name__ == '__main__':
    main()

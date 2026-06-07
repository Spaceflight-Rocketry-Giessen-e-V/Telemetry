# -*- coding: utf-8 -*-
"""openEMS / CSXCAD model builder for the single-feed RHCP patch antenna."""

import numpy as np
from CSXCAD  import ContinuousStructure
from openEMS import openEMS

import config
from src.geometry import patch_polygon_array, single_feed_layout
from src.params import PatchParams


class _Tee:
    """Write to multiple streams simultaneously (used for log tee in run.py)."""

    def __init__(self, *streams):
        self._s = streams

    def write(self, data):
        for s in self._s:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self._s:
            try:
                s.flush()
            except Exception:
                pass

    @property
    def encoding(self):
        return self._s[0].encoding

    def reconfigure(self, **_):
        pass  # already configured; defensive shim so callers can probe stdout


def _dedupe_mesh_lines(mesh, min_gap_mm: float) -> int:
    """Drop near-duplicate grid lines closer than ``min_gap_mm``; return #removed.

    openEMS's ``AddEdges2Grid`` metal-edge rule places 1/3–2/3 fractional lines at
    EVERY copper box edge. Where the inset-notch / feed boxes have edges that fall
    microns apart (floating-point, or the 45° chamfer's staircase) their fractional
    lines also land microns apart — and ``SmoothMeshLines`` only ADDS lines, it never
    removes a near-duplicate. A SINGLE sub-micron cell sets the global Courant timestep
    for the whole domain, so one stray µm gap collapses the FDTD timestep (~75× too
    small): a fixed NrTS then covers a fraction of one RF period and the high-Q patch
    never rings down (off-target resonance, AR≤3 dB beamwidth → 0°).

    Greedy pass per axis: keep the lowest line of each cluster, drop any successor
    within ``min_gap_mm``. With ``min_gap_mm`` well below the intended mesh resolution
    this thins only sub-resolution duplicates and leaves the real mesh intact.
    """
    removed = 0
    for ax in 'xyz':
        lines = np.array(sorted(mesh.GetLines(ax)), dtype=float)
        if lines.size < 2:
            continue
        keep = [lines[0]]
        for L in lines[1:]:
            if L - keep[-1] >= min_gap_mm:
                keep.append(L)
        if len(keep) != lines.size:
            removed += lines.size - len(keep)
            mesh.SetLines(ax, keep)
    return removed


# ══════════════════════════════════════════════════════════════════════════
# Single-feed corner-truncated RHCP patch — build path
# ══════════════════════════════════════════════════════════════════════════


def build_patch_sim(p: PatchParams, NrTS: int, *, vtk_dump: bool = False):
    """Build the single-feed corner-truncated RHCP patch model.

    Returns (FDTD, CSX, port, nf2ff_box) — driven by a PatchParams object.

    A near-square patch (side ``p.W_mm``) has two diagonally-opposite corners
    truncated by ``p.trunc_mm`` (the CP perturbation; diagonal 'BLTR' → RHCP at +z),
    fed by ONE inset microstrip at the centre of the −y edge to depth
    ``p.inset_y_mm``. The feed runs out to a Feed_R-terminated MSL port so the board
    stays finite (nothing crosses the NF2FF surface → clean far-field/efficiency).
    The square board is centred at the origin with PML_8 boundaries. No branch-line
    coupler, no isolated-port resistor (which dumped ~64 % of accepted power).
    """
    z      = config.substrate_thickness
    Lo     = single_feed_layout(p)
    h, fw  = Lo['h'], Lo['fw']
    trunc, diag = Lo['trunc'], Lo['diag']
    sub_hw = Lo['sub_hw']
    insets = Lo['insets']
    mer    = config.mesh_res / 2.0

    # PML clearance guardrail: the board is centred at the origin, so each lateral
    # face clears (SimBox/2 − sub_hw) and the −z face clears SimBox[2]/3. PML_8 eats
    # ~8·mesh_res inside each face; warn if the remaining air gap drops below λ/4
    # (else the finite-GP back-lobe / reactive near-field is clipped, biasing Dmax).
    _pml  = 8.0 * config.mesh_res
    _lamq = config.C0 / config.f_target / 1e-3 / 4.0
    for _nm, _gap in (('x', config.SimBox[0] / 2 - sub_hw),
                      ('y', config.SimBox[1] / 2 - sub_hw),
                      ('z-', config.SimBox[2] / 3.0)):
        if _gap - _pml < _lamq:
            print(f'  ! WARNING: only {_gap - _pml:.0f} mm air to inner PML on {_nm} '
                  f'(< λ/4 = {_lamq:.0f} mm); enlarge config.SimBox.', flush=True)

    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-4)
    FDTD.SetGaussExcite(config.f_target, config.fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    mesh.AddLine('x', [-config.SimBox[0] / 2, config.SimBox[0] / 2])
    mesh.AddLine('y', [-config.SimBox[1] / 2, config.SimBox[1] / 2])
    mesh.AddLine('z', [-config.SimBox[2] / 3, config.SimBox[2] * 2 / 3])

    # ── substrate + ground (square, centred at origin) ─────────────────
    substrate = CSX.AddMaterial('substrate', epsilon=config.substrate_epsR,
                                kappa=config.substrate_kappa)
    substrate.AddBox(priority=0, start=[-sub_hw, -sub_hw, 0], stop=[sub_hw, sub_hw, z])
    mesh.AddLine('z', np.linspace(0, z, config.substrate_cells + 1))
    gnd = CSX.AddMetal('gnd')
    gnd.AddBox(start=[-sub_hw, -sub_hw, 0], stop=[sub_hw, sub_hw, 0], priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    # ── truncated patch with the bottom inset notch ────────────────────
    patch = CSX.AddMetal('patch')
    patch.AddPolygon(patch_polygon_array(p.W_mm, insets, trunc, diag), 'z',
                     elevation=z, priority=10)

    # patch outline + chamfer + inset-notch mesh halos. (AddEdges2Grid can't grid a
    # POLYGON — openEMS automesh returns None for it — so resolve every edge here.)
    crit_x = {-h, h}
    crit_y = {-h, h}
    if trunc > 0:
        crit_x |= {-h + trunc, h - trunc}
        crit_y |= {-h + trunc, h - trunc}
    for ins in insets:                       # single bottom-edge inset
        c, half, d = ins['center'], ins['width'] / 2.0 + ins['gap'], ins['depth']
        crit_y.add(-h + d)
        crit_x |= {c - half, c + half, c - ins['width'] / 2, c + ins['width'] / 2}
        mesh.AddLine('x', np.linspace(c - half, c - ins['width'] / 2, 3))
        mesh.AddLine('x', np.linspace(c + ins['width'] / 2, c + half, 3))
    for xv in sorted(crit_x):
        mesh.AddLine('x', [xv - mer / 3, xv, xv + mer / 3])
    for yv in sorted(crit_y):
        mesh.AddLine('y', [yv - mer / 3, yv, yv + mer / 3])
    # resolve the two 45° chamfers (Cartesian-staircased) with a few local lines so
    # the corner cut is approximated consistently across both modes.
    if trunc > 0:
        corners = [(-h, -h), (h, h)] if diag == 'BLTR' else [(-h, h), (h, -h)]
        for cx, cy in corners:
            mesh.AddLine('x', np.linspace(cx, cx - np.sign(cx) * trunc, 5))
            mesh.AddLine('y', np.linspace(cy, cy - np.sign(cy) * trunc, 5))

    # ── single inset feed (−y edge centre) + MSL input port ────────────
    # A short 50 Ω feed stub terminated at its far end by the MSL port's own Feed_R:
    # the resistor absorbs the backward wave (no open-stub resonance) AND provides a
    # matched source, while the board stays FINITE — nothing crosses the NF2FF surface.
    feed     = CSX.AddMetal('feed')
    port_len = 30.0
    y_stop   = -h - 2.0                       # patch side (meas plane ~12 mm below)
    y_start  = y_stop - port_len             # source side (Feed_R termination here)
    feed.AddBox(start=[-fw / 2, Lo['feed_y_patch'], z],
                stop =[ fw / 2, y_start,            z], priority=10)
    mesh.AddLine('y', np.linspace(y_start, y_stop, 16))   # ≥5 prop lines for MSL port
    port = FDTD.AddMSLPort(1, feed,
                           [-fw / 2, y_start, z],
                           [ fw / 2, y_stop,  0],
                           'y', 'z', excite=1, Feed_R=config.feed_R,
                           FeedShift=8.0, MeasPlaneShift=port_len - 8.0,
                           priority=10)

    # Drop sub-resolution duplicate lines (chamfer staircase / inset gaps) before AND
    # after the smooth so the global Courant timestep is set by the intended cells.
    _dedupe_mesh_lines(mesh, 0.1)
    mesh.SmoothMeshLines('all', config.mesh_res, 1.3)
    _dedupe_mesh_lines(mesh, 0.1)
    nf2ff_box = FDTD.CreateNF2FFBox()

    if vtk_dump:
        pad = config.mesh_res * 0.5
        J_surf = CSX.AddDump('J_patch_surf', dump_type=12, dump_mode=0)
        J_surf.SetFrequency([config.f_target])
        J_surf.AddBox(start=[-h - pad, -h - pad, z], stop=[h + pad, h + pad, z])

    return FDTD, CSX, port, nf2ff_box

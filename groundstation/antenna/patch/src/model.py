# -*- coding: utf-8 -*-
"""openEMS / CSXCAD model builder for the RHCP patch antenna."""

import numpy as np
from CSXCAD  import ContinuousStructure
from openEMS import openEMS

import config
from src.geometry import patch_polygon_array
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
    EVERY copper box edge. The coupler ring + L-feeds are many abutting/overlapping
    boxes, so wherever two of those edges fall microns apart (floating-point or a
    real sub-mm overlap) their fractional lines also land microns apart — and
    ``SmoothMeshLines`` only ADDS lines, it never removes a near-duplicate. A SINGLE
    sub-micron cell sets the global Courant timestep for the whole domain, so one
    stray 1.8 µm gap collapses the FDTD timestep from ~0.3 ps to ~4 fs (~75× too
    small): a fixed NrTS then covers a fraction of one RF period and the high-Q
    patch never rings down (off-target resonance, AR≤3 dB beamwidth → 0°).

    Greedy pass per axis: keep the lowest line of each cluster, drop any successor
    within ``min_gap_mm``. With ``min_gap_mm`` below the intended metal-edge fine
    gap (≈ METAL_EDGE_RES/3) this thins only sub-resolution duplicates and leaves
    the real mesh — including the inset-gap and metal-edge lines — intact.
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
# Flat dual-feed (branch-line coupler) RHCP patch — new build path
# ══════════════════════════════════════════════════════════════════════════


def build_patch_sim(p: PatchParams, NrTS: int, *, stage: str = 'single',
                    vtk_dump: bool = False):
    """Build the flat dual-feed RHCP patch model (staged migration target).

    Returns (FDTD, CSX, port, nf2ff_box) — driven by a PatchParams object.

    stage='single'  Stage 1: square patch + ONE inset microstrip feed + MSLPort.
                    De-risks the patch + MSL-port mechanics and anchors resonance
                    before the coupler exists. RHCP is NOT produced here.
    stage='full'    Stage 2+: adds the branch-line coupler, two equal-length
                    feeds and the isolated-port termination. (Lands next.)
    """
    if stage == 'full':
        return build_full_sim(p, NrTS, vtk_dump=vtk_dump)

    z      = config.substrate_thickness
    sub_hw = p.sub_hw_mm
    W      = p.W_mm
    h      = W / 2.0
    mer    = config.mesh_res / 2.0

    # Guardrail: keep ≥30 mm between board edge and MUR boundary in x/y.
    if 2 * sub_hw + 60 > config.SimBox[0] or 2 * sub_hw + 60 > config.SimBox[1]:
        print(f'  ! WARNING: sub_hw_mm={sub_hw:.1f} leaves <30 mm to MUR boundary '
              f'(SimBox xy = {config.SimBox[0]:.0f}×{config.SimBox[1]:.0f} mm).', flush=True)

    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-4)
    FDTD.SetGaussExcite(config.f_target, config.fc)
    FDTD.SetBoundaryCond(['MUR'] * 6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    mesh.AddLine('x', [-config.SimBox[0] / 2, config.SimBox[0] / 2])
    mesh.AddLine('y', [-config.SimBox[1] / 2, config.SimBox[1] / 2])
    mesh.AddLine('z', [-config.SimBox[2] / 3, config.SimBox[2] * 2 / 3])

    # ── substrate + ground ────────────────────────────────────────────
    substrate = CSX.AddMaterial('substrate',
                                epsilon=config.substrate_epsR,
                                kappa=config.substrate_kappa)
    substrate.AddBox(priority=0, start=[-sub_hw, -sub_hw, 0],
                     stop=[sub_hw, sub_hw, z])
    mesh.AddLine('z', np.linspace(0, z, config.substrate_cells + 1))

    gnd = CSX.AddMetal('gnd')
    gnd.AddBox(start=[-sub_hw, -sub_hw, 0], stop=[sub_hw, sub_hw, 0], priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    # ── feed definitions (per stage) ──────────────────────────────────
    feed_w = config.FEED_W
    gap    = config.INSET_GAP
    if stage == 'single':
        # One inset feed at the centre of the -y edge; resonance / match only.
        insets = [dict(edge='bottom', center=0.0, width=feed_w, gap=gap,
                       depth=p.inset_y_mm)]
    else:
        raise NotImplementedError("unknown stage")  # 'full' is dispatched at the top

    # ── patch (square with inset notches) ─────────────────────────────
    patch = CSX.AddMetal('patch')
    patch.AddPolygon(patch_polygon_array(W, insets), 'z', elevation=z, priority=10)

    # patch outline + notch mesh halos
    crit_x = {-h, h}
    crit_y = {-h, h}
    for ins in insets:
        c, half, d = ins['center'], ins['width'] / 2.0 + ins['gap'], ins['depth']
        if ins['edge'] in ('bottom', 'top'):
            inner = (-h + d) if ins['edge'] == 'bottom' else (h - d)
            crit_y.add(inner)
            crit_x |= {c - half, c + half, c - ins['width'] / 2, c + ins['width'] / 2}
            # resolve the two etch gaps explicitly
            mesh.AddLine('x', np.linspace(c - half, c - ins['width'] / 2, 3))
            mesh.AddLine('x', np.linspace(c + ins['width'] / 2, c + half, 3))
        else:
            inner = (-h + d) if ins['edge'] == 'left' else (h - d)
            crit_x.add(inner)
            crit_y |= {c - half, c + half, c - ins['width'] / 2, c + ins['width'] / 2}
            mesh.AddLine('y', np.linspace(c - half, c - ins['width'] / 2, 3))
            mesh.AddLine('y', np.linspace(c + ins['width'] / 2, c + half, 3))
    for xv in sorted(crit_x):
        mesh.AddLine('x', [xv - mer / 3, xv, xv + mer / 3])
    for yv in sorted(crit_y):
        mesh.AddLine('y', [yv - mer / 3, yv, yv + mer / 3])

    # ── feed line + MSL input port (on-board, source-matched) ─────────
    # A short 50 Ω feed stub terminated at its far end by the MSL port's own
    # Feed_R=50: the resistor absorbs the backward wave (no open-stub resonance
    # like a free end would give) AND provides a matched source, while the board
    # stays FINITE — nothing crosses the NF2FF surface, so the far-field/Dmax are
    # clean. The MSL port still self-computes Z_ref/beta for an honest S11.
    feed     = CSX.AddMetal('feed')
    port_len = 30.0
    y_stop   = -h - 2.0                 # patch side (meas plane ~12 mm below patch)
    y_start  = y_stop - port_len        # source side (Feed_R termination here)
    feed.AddBox(start=[-feed_w / 2, -h + p.inset_y_mm, z],
                stop =[ feed_w / 2, y_start,           z], priority=10)
    mesh.AddLine('y', np.linspace(y_start, y_stop, 16))   # ≥5 prop lines for MSL port
    port = FDTD.AddMSLPort(1, feed,
                           [-feed_w / 2, y_start, z],
                           [ feed_w / 2, y_stop,  0],
                           'y', 'z', excite=1, Feed_R=config.feed_R,
                           FeedShift=8.0, MeasPlaneShift=port_len - 8.0,
                           priority=10)

    # Remove sub-resolution duplicate lines (see _dedupe_mesh_lines) BEFORE the
    # smooth so the graded fill starts from a clean fine resolution and the global
    # Courant timestep is set by the intended ~METAL_EDGE_RES cells, not a stray µm gap.
    _dedupe_mesh_lines(mesh, config.METAL_EDGE_RES / 4.0)
    mesh.SmoothMeshLines('all', config.mesh_res, 1.3)
    _dedupe_mesh_lines(mesh, config.METAL_EDGE_RES / 4.0)   # belt-and-braces: catch any smooth artefacts
    nf2ff_box = FDTD.CreateNF2FFBox()

    if vtk_dump:
        pad   = config.mesh_res * 0.5
        z_mid = z / 2.0
        E_surf = CSX.AddDump('E_patch_surf', dump_type=10, dump_mode=0)
        E_surf.SetFrequency([config.f_target])
        E_surf.AddBox(start=[-h - pad, -h - pad, z_mid - pad / 2],
                      stop =[ h + pad,  h + pad, z_mid + pad / 2])
        J_surf = CSX.AddDump('J_patch_surf', dump_type=12, dump_mode=0)
        J_surf.SetFrequency([config.f_target])
        J_surf.AddBox(start=[-h - pad, -h - pad, z], stop=[h + pad, h + pad, z])

    return FDTD, CSX, port, nf2ff_box


def build_full_sim(p: PatchParams, NrTS: int, *, vtk_dump: bool = False):
    """Stage 2+ full dual-feed model: square patch + branch-line coupler + two
    equal-length L-feeds + isolated-port 50 Ω termination, on the offset finite
    board. LOCKED topology: input=BL, isolated=BR, outputs TL→LEFT(-x)/E_x and
    TR→BOTTOM(-y)/E_y → RHCP at +z. PML_8 boundaries (better absorption / faster
    convergence than MUR). All geometry comes from geometry.dual_feed_layout(p).
    """
    from src.geometry import dual_feed_layout

    z   = config.substrate_thickness
    fr  = config.METAL_EDGE_RES
    mer = config.mesh_res / 2.0
    Lo  = dual_feed_layout(p)
    bcx, bcy = Lo['board_center']
    sub_hw   = Lo['sub_hw']
    h, fw    = Lo['h'], Lo['fw']

    # PML clearance guardrail (build_full_sim previously had none). The board is
    # centred in the domain below, so each lateral face clears (SimBox/2 - sub_hw)
    # and the -z face clears SimBox[2]/3. PML_8 consumes ~8·mesh_res inside each
    # face, so the AIR gap to the inner PML boundary is that minus the PML depth;
    # warn when it drops below λ/4 (otherwise the finite GP's back-lobe / reactive
    # near-field is clipped, biasing Dmax and the wide-angle AR coverage metrics).
    _pml_mm = 8.0 * config.mesh_res
    _lam_q  = config.C0 / config.f_target / 1e-3 / 4.0
    for _nm, _gap in (('x', config.SimBox[0] / 2 - sub_hw),
                      ('y', config.SimBox[1] / 2 - sub_hw),
                      ('z-', config.SimBox[2] / 3.0)):
        if _gap - _pml_mm < _lam_q:
            print(f'  ! WARNING: only {_gap - _pml_mm:.0f} mm air to inner PML on {_nm} '
                  f'(< λ/4 = {_lam_q:.0f} mm); enlarge config.SimBox to de-bias '
                  f'far-field / wide-angle AR.', flush=True)

    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-4)
    FDTD.SetGaussExcite(config.f_target, config.fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    # Centre the domain on the OFFSET board (not the origin): the coupler/feeds push
    # the board into the -x/-y quadrant, so an origin-centred domain crowds the PML
    # against the -x/-y board edges. Centring restores symmetric lateral clearance;
    # z keeps its origin-referenced split (more room on the +z radiating side).
    mesh.AddLine('x', [bcx - config.SimBox[0] / 2, bcx + config.SimBox[0] / 2])
    mesh.AddLine('y', [bcy - config.SimBox[1] / 2, bcy + config.SimBox[1] / 2])
    mesh.AddLine('z', [-config.SimBox[2] / 3, config.SimBox[2] * 2 / 3])

    # ── offset board: substrate + ground ──────────────────────────────
    substrate = CSX.AddMaterial('substrate', epsilon=config.substrate_epsR,
                                kappa=config.substrate_kappa)
    substrate.AddBox(priority=0, start=[bcx - sub_hw, bcy - sub_hw, 0],
                     stop=[bcx + sub_hw, bcy + sub_hw, z])
    mesh.AddLine('z', np.linspace(0, z, config.substrate_cells + 1))
    gnd = CSX.AddMetal('gnd')
    gnd.AddBox(start=[bcx - sub_hw, bcy - sub_hw, 0],
               stop=[bcx + sub_hw, bcy + sub_hw, 0], priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    # ── patch (square + two inset notches) at the origin ──────────────
    patch = CSX.AddMetal('patch')
    patch.AddPolygon(patch_polygon_array(p.W_mm, Lo['insets']), 'z',
                     elevation=z, priority=10)

    # Patch outline + inset-notch mesh halos. CRITICAL: AddEdges2Grid below cannot
    # grid the patch — openEMS's automesh only hints POINT/BOX primitives and
    # returns None for a POLYGON, so the call is a no-op for the patch. Without
    # these explicit triple-line halos the two feedless radiating edges (+x, +y)
    # get NO mesh lines (≈5–13 mm cells) while the feed-bearing -x/-y edges are
    # finely gridded by the feed boxes — an asymmetric mesh that shifts the E_x and
    # E_y resonances differently and breaks the 90° CP quadrature. Mirrors the
    # halo logic in build_patch_sim so every patch edge is resolved symmetrically.
    crit_x = {-h, h}
    crit_y = {-h, h}
    for ins in Lo['insets']:
        c, half, d = ins['center'], ins['width'] / 2.0 + ins['gap'], ins['depth']
        if ins['edge'] in ('bottom', 'top'):
            inner = (-h + d) if ins['edge'] == 'bottom' else (h - d)
            crit_y.add(inner)
            crit_x |= {c - half, c + half, c - ins['width'] / 2, c + ins['width'] / 2}
            mesh.AddLine('x', np.linspace(c - half, c - ins['width'] / 2, 3))
            mesh.AddLine('x', np.linspace(c + ins['width'] / 2, c + half, 3))
        else:
            inner = (-h + d) if ins['edge'] == 'left' else (h - d)
            crit_x.add(inner)
            crit_y |= {c - half, c + half, c - ins['width'] / 2, c + ins['width'] / 2}
            mesh.AddLine('y', np.linspace(c - half, c - ins['width'] / 2, 3))
            mesh.AddLine('y', np.linspace(c + ins['width'] / 2, c + half, 3))
    for xv in sorted(crit_x):
        mesh.AddLine('x', [xv - mer / 3, xv, xv + mer / 3])
    for yv in sorted(crit_y):
        mesh.AddLine('y', [yv - mer / 3, yv, yv + mer / 3])

    # ── coupler ring + two L-feeds (one top-copper net; PEC bonds on overlap) ──
    cu = CSX.AddMetal('cu_top')
    for (x0, y0), (x1, y1) in Lo['coupler_arms']:
        cu.AddBox(start=[x0, y0, z], stop=[x1, y1, z], priority=10)
    for (x0, y0), (x1, y1) in Lo['feed_rects']:
        cu.AddBox(start=[x0, y0, z], stop=[x1, y1, z], priority=10)

    # ── isolated-port short stub (BR → iso_end) + 50 Ω strip-to-ground R ──
    BRx, BRy = Lo['BR']
    ix, iy   = Lo['iso_end']
    cu.AddBox(start=[BRx - fw / 2, BRy + fw / 2, z], stop=[BRx + fw / 2, iy, z], priority=10)
    res = CSX.AddLumpedElement('R_iso', ny='z', caps=True, R=config.feed_R)
    res.AddBox(start=[ix, iy, 0], stop=[ix, iy, z])
    mesh.AddLine('x', [ix - fr, ix, ix + fr])
    mesh.AddLine('y', [iy - fr, iy, iy + fr])

    # ── input stub (BL → stub_end) = MSL feed metal, Feed_R-terminated source ──
    feed = CSX.AddMetal('feed')
    BLx, BLy = Lo['BL']
    _sx, sy  = Lo['stub_end']
    feed.AddBox(start=[BLx - fw / 2, BLy + fw / 2, z], stop=[BLx + fw / 2, sy, z], priority=10)

    # local fine mesh at every top-copper edge (NOT a global fine smooth).
    # The coupler ring + L-feeds are many overlapping boxes, so AddEdges2Grid emits
    # 1/3–2/3 metal-edge lines that can land microns apart where two edges nearly
    # coincide; _dedupe_mesh_lines below clears those before smoothing so the FDTD
    # timestep is not collapsed by a stray sub-micron cell.
    for prop in (patch, cu, feed):
        FDTD.AddEdges2Grid(dirs='xy', properties=prop, metal_edge_res=fr)

    # MSL input port: prop +y from the stub end toward the coupler
    port_len = config.INPUT_STUB - 2.0
    y_start  = sy                          # source side (board edge), Feed_R here
    y_stop   = sy + port_len               # toward the BL junction
    mesh.AddLine('y', np.linspace(y_start, y_stop, 16))   # ≥5 prop lines
    port = FDTD.AddMSLPort(1, feed,
                           [BLx - fw / 2, y_start, z],
                           [BLx + fw / 2, y_stop, 0],
                           'y', 'z', excite=1, Feed_R=config.feed_R,
                           FeedShift=8.0, MeasPlaneShift=port_len - 8.0, priority=10)

    # Drop sub-resolution duplicate lines (overlapping coupler/feed boxes) before
    # AND after the smooth, so the global Courant timestep is set by the intended
    # ~METAL_EDGE_RES cells rather than a stray µm gap (see _dedupe_mesh_lines).
    _dedupe_mesh_lines(mesh, config.METAL_EDGE_RES / 4.0)
    mesh.SmoothMeshLines('all', config.mesh_res, 1.3)
    _dedupe_mesh_lines(mesh, config.METAL_EDGE_RES / 4.0)
    nf2ff_box = FDTD.CreateNF2FFBox()

    if vtk_dump:
        xmin, xmax, ymin, ymax = Lo['copper_bbox']
        J_surf = CSX.AddDump('J_patch_surf', dump_type=12, dump_mode=0)
        J_surf.SetFrequency([config.f_target])
        J_surf.AddBox(start=[xmin, ymin, z], stop=[xmax, ymax, z])

    return FDTD, CSX, port, nf2ff_box

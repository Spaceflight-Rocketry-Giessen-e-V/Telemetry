# -*- coding: utf-8 -*-
"""openEMS / CSXCAD model builder for the RHCP patch antenna."""

import sys

import numpy as np
from CSXCAD  import ContinuousStructure
from openEMS import openEMS

import config
from src.geometry import patch_vertices_array


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
        pass  # already configured


def build_sim(delta_mm: float, y_inset_mm: float, W_patch: float,
              NrTS: int, sub_hw_mm: float = config.SUB_HW_DEFAULT,
              _dbg: bool = False, vtk_dump: bool = False):
    """Build a complete openEMS + CSXCAD model.

    Returns (FDTD, CSX, port, nf2ff_box).
    Does NOT run the simulation or write files.

    sub_hw_mm = half-width of the square substrate / ground plane [mm].
    vtk_dump=True adds frequency-domain E-field and surface-current dump
    boxes for ParaView visualisation (final sim only).
    """
    # Guardrail: keep ≥30 mm between board edge and MUR boundary in x/y.
    if 2 * sub_hw_mm + 60 > config.SimBox[0] or 2 * sub_hw_mm + 60 > config.SimBox[1]:
        print(f'  ! WARNING: sub_hw_mm={sub_hw_mm:.1f} leaves <30 mm to MUR boundary '
              f'(SimBox xy = {config.SimBox[0]:.0f}×{config.SimBox[1]:.0f} mm). '
              f'Far-field accuracy may degrade.', flush=True)
    def _p(msg):
        if _dbg:
            print(f'  [build_sim] {msg}', flush=True)

    _p('creating openEMS + CSXCAD objects')
    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-4)
    _p('SetGaussExcite')
    FDTD.SetGaussExcite(config.f_target, config.fc)
    _p('SetBoundaryCond')
    FDTD.SetBoundaryCond(['MUR'] * 6)

    _p('ContinuousStructure')
    CSX = ContinuousStructure()
    _p('SetCSX')
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    _p('outer domain mesh lines')
    mesh.AddLine('x', [-config.SimBox[0] / 2, config.SimBox[0] / 2])
    mesh.AddLine('y', [-config.SimBox[1] / 2, config.SimBox[1] / 2])
    mesh.AddLine('z', [-config.SimBox[2] / 3,  config.SimBox[2] * 2 / 3])

    # ── Patch: hexagonal polygon with two diagonally truncated corners ──
    # Removes TR (+h,+h) and BL (-h,-h) corners with true 45° cuts,
    # breaking symmetry along the +45° diagonal → RHCP at broadside (+z).
    h = W_patch / 2
    d = delta_mm
    z = config.substrate_thickness

    patch_pts = patch_vertices_array(W_patch, delta_mm)

    _p(f'AddMetal patch polygon  h={h:.2f} d={d:.2f} z={z}')
    patch = CSX.AddMetal('patch')
    patch.AddPolygon(patch_pts, 'z', elevation=z, priority=10)

    _p('patch edge mesh lines')
    mer = config.mesh_res / 2
    for xv in sorted({-h, -h + d, h - d, h}):
        mesh.AddLine('x', [xv - mer / 3, xv, xv + mer / 3])
    for yv in sorted({-h, -h + d, h - d, h}):
        mesh.AddLine('y', [yv - mer / 3, yv, yv + mer / 3])

    _p('AddMaterial substrate')
    sub_hw    = sub_hw_mm
    substrate = CSX.AddMaterial('substrate',
                                epsilon=config.substrate_epsR,
                                kappa=config.substrate_kappa)
    _p('substrate.AddBox')
    substrate.AddBox(priority=0,
                     start=[-sub_hw, -sub_hw, 0],
                     stop =[ sub_hw,  sub_hw, config.substrate_thickness])
    _p('substrate z mesh lines')
    mesh.AddLine('z', np.linspace(0, config.substrate_thickness,
                                  config.substrate_cells + 1))

    _p('AddMetal gnd')
    gnd = CSX.AddMetal('gnd')
    _p('gnd.AddBox')
    gnd.AddBox(start=[-sub_hw, -sub_hw, 0],
               stop =[ sub_hw,  sub_hw, 0], priority=10)
    _p('AddEdges2Grid gnd')
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    _p('feed port mesh lines')
    y_feed = -W_patch / 2 + y_inset_mm
    mesh.AddLine('x', [-mer / 3, 0.0, mer / 3])
    mesh.AddLine('y', [y_feed - mer / 3, y_feed, y_feed + mer / 3])
    _p(f'AddLumpedPort  y_feed={y_feed:.2f}')
    port = FDTD.AddLumpedPort(1, config.feed_R,
                               [0, y_feed, 0],
                               [0, y_feed, config.substrate_thickness],
                               'z', 1.0, priority=5, edges2grid='xy')

    _p('SmoothMeshLines')
    mesh.SmoothMeshLines('all', config.mesh_res, 1.3)
    _p('CreateNF2FFBox')
    nf2ff_box = FDTD.CreateNF2FFBox()

    if vtk_dump:
        _p('vtk_dump: adding frequency-domain surface field dumps')
        # E_patch_surf — E-field DFT phasor at substrate mid-plane.
        # J_patch_surf — surface current density DFT phasor at patch conductor.
        # Both accumulate during the FDTD run and write one VTK file each.
        # Requires openEMS >= r700 for DumpType=10/12 (frequency-domain).
        pad   = config.mesh_res * 0.5
        z_mid = config.substrate_thickness / 2.0

        E_surf = CSX.AddDump('E_patch_surf', dump_type=10, dump_mode=0)
        E_surf.SetFrequency([config.f_target])
        E_surf.AddBox(
            start=[-h - pad, -h - pad, z_mid - pad / 2],
            stop =[ h + pad,  h + pad, z_mid + pad / 2]
        )

        J_surf = CSX.AddDump('J_patch_surf', dump_type=12, dump_mode=0)
        J_surf.SetFrequency([config.f_target])
        J_surf.AddBox(
            start=[-h - pad, -h - pad, config.substrate_thickness],
            stop =[ h + pad,  h + pad, config.substrate_thickness]
        )
        _p('vtk_dump: E_patch_surf and J_patch_surf dump boxes added')

    _p('done')
    return FDTD, CSX, port, nf2ff_box

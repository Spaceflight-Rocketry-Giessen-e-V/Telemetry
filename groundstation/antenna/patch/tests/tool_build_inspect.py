# -*- coding: utf-8 -*-
"""Build inspector — geometry, mesh, smallest gaps and Courant timestep (no solve).

Constructs build_patch_sim at NrTS=1 and reports, WITHOUT running a simulation:
  * the realised geometry / board size / analytical seeds (a fast geometry +
    port-API regression gate),
  * the full mesh-line counts and per-axis min/max gaps,
  * the LOCATION of the smallest gaps on each axis (a single sub-cell collapses the
    global FDTD timestep — see model._dedupe_mesh_lines), and
  * the Courant timestep implied by the smallest cell + how many RF periods NrTS_opt
    would cover.
Pass ``--banner`` to additionally run a tiny NrTS=300 solve with verbose=2 so
openEMS prints its own timestep banner.

Merges the former build_check (build / geometry / margin) and mesh_diag (gap
locator / timestep) harnesses.

    python tests/tool_build_inspect.py               # default W, report only
    python tests/tool_build_inspect.py 85.0          # override patch side W
    python tests/tool_build_inspect.py 85.0 --banner # also read the engine timestep banner
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import shutil
import sys
import tempfile

import numpy as np

import config
from src.geometry import single_feed_layout
from src.model import build_patch_sim
from src.params import default_params


def _mesh_cells(mesh):
    nx = len(mesh.GetLines('x'))
    ny = len(mesh.GetLines('y'))
    nz = len(mesh.GetLines('z'))
    return nx, ny, nz, nx * ny * nz


def _report_axis_gaps(mesh, ax, n=6):
    """Print the n smallest consecutive-line gaps on `ax` and where they sit."""
    lines = np.array(mesh.GetLines(ax))
    d = np.diff(lines)
    order = np.argsort(d)
    print(f'  axis {ax}: {len(lines)} lines, min gap {d.min():.4f} mm, max {d.max():.2f} mm'
          f'  (ratio {d.max()/d.min():.0f})')
    print(f'    {n} smallest gaps:')
    for i in order[:n]:
        print(f'      {lines[i]:9.4f} -> {lines[i+1]:9.4f}   d = {d[i]:.4f} mm')
    print(f'    gaps < 0.05 mm: {np.sum(d < 0.05)}   gaps < 0.2 mm: {np.sum(d < 0.2)}')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    pos    = [a for a in sys.argv[1:] if not a.startswith('-')]
    banner = '--banner' in sys.argv
    W = float(pos[0]) if pos else default_params().W_mm
    p = default_params().with_(W_mm=W)
    Lo = single_feed_layout(p)

    print('=' * 66)
    print('BUILD INSPECTOR  (NrTS=1, no solve)')
    print('=' * 66)
    print('Analytical seeds (config):')
    print(f'  W_lp   = {config.W_lp:7.2f} mm   eps_eff = {config.eps_eff:.3f}')
    print(f'  L_lp   = {config.L_lp:7.2f} mm   dL      = {config.dL:.3f} mm')
    print(f'  mesh_res = {config.mesh_res:.2f} mm   substrate_kappa = {config.substrate_kappa:.4f} S/m')
    print(f'  f_target = {config.f_target/1e6:.2f} MHz   fc = {config.fc/1e6:.0f} MHz')
    print('\nPatchParams (defaults, W override applied):')
    for k, v in p.to_dict().items():
        print(f'  {k:12s} = {v:8.3f} mm')

    print('\nRealised layout (single_feed_layout):')
    xmin, xmax, ymin, ymax = Lo['copper_bbox']
    print(f'  patch side W      = {p.W_mm:.2f} mm   (half {Lo["h"]:.2f} mm)')
    print(f'  corner truncation = {Lo["trunc"]:.2f} mm chamfer ({Lo["diag"]})')
    print(f'  feed inset / pt   = {p.inset_y_mm:.2f} mm at {Lo["feed_fp"]}')
    print(f'  copper bbox       = x[{xmin:.1f}, {xmax:.1f}]  y[{ymin:.1f}, {ymax:.1f}] mm')
    print(f'  copper extent     = {xmax-xmin:.1f} x {ymax-ymin:.1f} mm')
    print(f'  board half-width  = {Lo["sub_hw"]:.2f} mm  ->  board edge {Lo["sub_hw"]*2:.1f} mm'
          f'  (param sub_hw {p.sub_hw_mm:.1f})')
    print(f'  board centre      = ({Lo["board_center"][0]:.2f}, {Lo["board_center"][1]:.2f}) mm')

    # margin check: every copper edge must sit >= BOARD_MARGIN inside the board
    bcx, bcy = Lo['board_center']; shw = Lo['sub_hw']
    margins = [xmin - (bcx - shw), (bcx + shw) - xmax,
               ymin - (bcy - shw), (bcy + shw) - ymax]
    print(f'  copper->edge gaps = {[round(m,1) for m in margins]} mm'
          f'  (min {min(margins):.1f}, need >= {config.BOARD_MARGIN:.1f})')
    assert min(margins) >= config.BOARD_MARGIN - 1e-6, 'copper too close to board edge!'

    print('\nBuilding full FDTD model (NrTS=1)...')
    FDTD, CSX, port, nf2ff = build_patch_sim(p, 1)
    mesh = CSX.GetGrid()
    nx, ny, nz, ncell = _mesh_cells(mesh)
    print(f'  mesh lines        = {nx} x {ny} x {nz}  ->  {ncell:,} cells')
    print(f'  port object       = {type(port).__name__}')
    print(f'  nf2ff box         = {type(nf2ff).__name__}')

    print('\nMesh gaps (the smallest cell sets the global Courant timestep):')
    for ax in 'xyz':
        _report_axis_gaps(mesh, ax)

    # Courant timestep estimate from the smallest cell on each axis
    dx = np.diff(mesh.GetLines('x')).min() * 1e-3
    dy = np.diff(mesh.GetLines('y')).min() * 1e-3
    dz = np.diff(mesh.GetLines('z')).min() * 1e-3
    dt = 1.0 / (config.C0 * np.sqrt(1/dx**2 + 1/dy**2 + 1/dz**2))
    print(f'\n  Courant dt (from min cell)  ~ {dt*1e15:.3f} fs')
    print(f'  NrTS_opt={config.NrTS_opt} covers ~{dt*config.NrTS_opt*1e9:.3f} ns'
          f'  ({dt*config.NrTS_opt*config.f_target:.1f} RF periods at f_target)')
    print('  (need >= ~30-50 periods for a high-Q patch to ring down)')

    if banner:
        print('\nRunning NrTS=300 to read the engine timestep banner...')
        sp = tempfile.mkdtemp(prefix='buildinspect_')
        try:
            FDTD2, _CSX2, _p2, _n2 = build_patch_sim(p, 300)
            FDTD2.Run(sp, verbose=2, cleanup=True, numThreads=1)
        finally:
            shutil.rmtree(sp, ignore_errors=True)

    print('\nBUILD OK — geometry, mesh and ports constructed without error.')
    print('=' * 66)


if __name__ == '__main__':
    main()

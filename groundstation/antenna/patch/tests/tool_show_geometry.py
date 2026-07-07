# -*- coding: utf-8 -*-
"""Tool — build the single-feed CP geometry at given dims and open it in AppCSXCAD.

Geometry only (NrTS=1, no FDTD solve). Writes a CSXCAD XML and launches the
AppCSXCAD viewer on it so the truncated patch + inset feed + board can be inspected.
The subprocess.call blocks until the viewer window is closed (run this in the
background if you don't want to wait).

    python tests/tool_show_geometry.py             # config seeds
    python tests/tool_show_geometry.py 82.5 8.25   # explicit W, truncation
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import subprocess
import sys

import config
from src.geometry import single_feed_layout
from src.model import build_patch_sim
from src.params import default_params


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    W     = float(sys.argv[1]) if len(sys.argv) > 1 else default_params().W_mm
    trunc = float(sys.argv[2]) if len(sys.argv) > 2 else default_params().trunc_mm
    p = default_params().with_(W_mm=W, trunc_mm=trunc)
    Lo = single_feed_layout(p)

    print(f'Geometry: near-square patch W={W:.1f} mm, truncation {trunc:.2f} mm, '
          f'inset {p.inset_y_mm:.1f} mm, board {Lo["sub_hw"]*2:.1f} mm')

    FDTD, CSX, _port, _nf = build_patch_sim(p, 1)   # NrTS=1, geometry only
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       f'geometry_review_W{W:.1f}_T{trunc:.1f}.xml')
    CSX.Write2XML(out)
    print(f'XML written: {out}')

    try:
        from CSXCAD import AppCSXCAD_BIN
        print(f'Launching AppCSXCAD ({AppCSXCAD_BIN}) — close the window when done.')
        subprocess.call([AppCSXCAD_BIN, out])
        print('AppCSXCAD closed.')
    except Exception as exc:
        print(f'Could not launch AppCSXCAD: {exc}')
        print(f'Open this file manually in AppCSXCAD: {out}')


if __name__ == '__main__':
    main()

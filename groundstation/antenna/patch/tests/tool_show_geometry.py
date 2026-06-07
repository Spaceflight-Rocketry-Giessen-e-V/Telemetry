# -*- coding: utf-8 -*-
"""Tool — build the dual-feed geometry at given dims and open it in AppCSXCAD.

Geometry only (NrTS=1, no FDTD solve). Writes a CSXCAD XML and launches the
AppCSXCAD viewer on it so the patch + branch-line coupler + feeds + stubs can be
inspected. The subprocess.call blocks until the viewer window is closed (run this
in the background if you don't want to wait).

    python tests/tool_show_geometry.py            # W=84.6, inset=16 (current best)
    python tests/tool_show_geometry.py 84.6 16    # explicit W, inset
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import subprocess
import sys

import config
from src.geometry import dual_feed_layout
from src.model import build_full_sim
from src.params import default_params


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    W     = float(sys.argv[1]) if len(sys.argv) > 1 else 84.6
    inset = float(sys.argv[2]) if len(sys.argv) > 2 else 16.0
    p = default_params().with_(W_mm=W, inset_x_mm=inset, inset_y_mm=inset)
    Lo = dual_feed_layout(p)

    print(f'Geometry: square patch W={W} mm, inset={inset} mm, coupler arm '
          f'{p.cpl_arm_mm} mm, board {Lo["sub_hw"]*2:.1f} mm')

    FDTD, CSX, _port, _nf = build_full_sim(p, 1)   # NrTS=1, geometry only
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       f'geometry_review_W{W:.1f}_ins{inset:.1f}.xml')
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

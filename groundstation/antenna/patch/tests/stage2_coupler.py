# -*- coding: utf-8 -*-
"""Stage 2 (coupler sub-gate) — branch-line (90-degree hybrid) S-parameters.

Validation gate (docs/migration-plan.md / Stage-2 design review): build ONLY the
square coupler ring + four 50-ohm corner stubs, put an MSL port on each corner
(port1 excited, ports 2-4 matched via Feed_R=50), and measure the 4-port S-params.
This EMPIRICALLY identifies which corners are the -3 dB / 90-degree OUTPUTS, which
corner is ISOLATED, and the input match -- the convention-proof way to lock the
feed routing before building the full patch model (a topology guess broke the
first design: in a branch-line the isolated port is ADJACENT to the input and the
diagonal corner is a live output -- this test confirms it for our exact geometry).

Ports (corner labels): 1=BL (excited input), 2=TL, 3=BR, 4=TR.
branch_line_rects uses w_h=CPL_W50 (horizontal arms) and w_v=CPL_W35 (vertical arms).

Targets at 869.52 MHz: two of {S21,S31,S41} ~ -3 dB (balanced within ~1 dB) and
90 deg apart = OUTPUTS; the smallest = ISOLATED (< -15..-20 dB); S11 < -15 dB.

Usage:
    python tests/stage2_coupler.py
    COUPLER_NRTS=60000 COUPLER_ARM=47 python tests/stage2_coupler.py
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import shutil
import sys
import tempfile

import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS

import config
from src.geometry import branch_line_rects

NrTS = int(os.environ.get('COUPLER_NRTS', '40000'))
ARM  = float(os.environ.get('COUPLER_ARM', str(config.CPL_ARM)))
W50  = config.CPL_W50
W35  = config.CPL_W35
Z    = config.substrate_thickness
STUB = 25.0          # 50-ohm corner stub length (hosts each MSL port)
PLEN = 22.0          # MSL port region length within a stub


def _add_rect(prop, x0, y0, x1, y1):
    prop.AddBox(start=[x0, y0, Z], stop=[x1, y1, Z], priority=10)


def build():
    a     = ARM / 2.0
    x_out = a + STUB
    sub_x = x_out + 12.0
    sub_y = a + 12.0

    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-4)
    FDTD.SetGaussExcite(config.f_target, config.fc)
    FDTD.SetBoundaryCond(['MUR'] * 6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    mesh.AddLine('x', [-160.0, 160.0])
    mesh.AddLine('y', [-140.0, 140.0])
    mesh.AddLine('z', [-90.0, 150.0])

    substrate = CSX.AddMaterial('substrate', epsilon=config.substrate_epsR,
                                kappa=config.substrate_kappa)
    substrate.AddBox(priority=0, start=[-sub_x, -sub_y, 0], stop=[sub_x, sub_y, Z])
    mesh.AddLine('z', np.linspace(0, Z, config.substrate_cells + 1))
    gnd = CSX.AddMetal('gnd')
    gnd.AddBox(start=[-sub_x, -sub_y, 0], stop=[sub_x, sub_y, 0], priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    metal = CSX.AddMetal('coupler')
    arms, corners = branch_line_rects(0.0, 0.0, ARM, w_h=W50, w_v=W35)
    for (x0, y0), (x1, y1) in arms:
        _add_rect(metal, x0, y0, x1, y1)
    # four 50-ohm corner stubs, colinear with the horizontal 50-ohm arms
    _add_rect(metal, -x_out, -a - W50 / 2, -a, -a + W50 / 2)   # BL  (-x)
    _add_rect(metal, -x_out,  a - W50 / 2, -a,  a + W50 / 2)   # TL  (-x)
    _add_rect(metal,  a,     -a - W50 / 2,  x_out, -a + W50 / 2)  # BR (+x)
    _add_rect(metal,  a,      a - W50 / 2,  x_out,  a + W50 / 2)  # TR (+x)

    # ── explicit fine mesh ONLY near the copper ──────────────────────
    # config.mesh_res (~13 mm) is far too coarse for 3-5 mm strips, so add local
    # fine lines here. The SINGLE SmoothMeshLines(mesh_res) at the end then grades
    # from these out to the coarse background. Do NOT SmoothMeshLines at the
    # fine (0.4 mm) scale — that forces a sub-mm mesh on the WHOLE domain (~500 M
    # cells, the bug that wedged the first run).
    for yv in (-a, a):                       # across the 50-ohm horizontal strips/stubs
        mesh.AddLine('y', np.linspace(yv - W50 / 2 - 0.3, yv + W50 / 2 + 0.3, 7))
    for xv in (-a, a):                       # across the 35-ohm vertical arms
        mesh.AddLine('x', np.linspace(xv - W35 / 2 - 0.3, xv + W35 / 2 + 0.3, 7))
    mesh.AddLine('x', np.linspace(-x_out, x_out, 90))   # along arms + both stubs
    mesh.AddLine('y', np.linspace(-a, a, 40))           # along vertical arms

    # ── four MSL ports (prop along x, exc along z); port1=BL excited ──
    def mslport(nr, x_outer, yc, into_plus_x, excite):
        x0 = x_outer
        x1 = x_outer + (PLEN if into_plus_x else -PLEN)
        return FDTD.AddMSLPort(nr, metal,
                               [x0, yc - W50 / 2, Z], [x1, yc + W50 / 2, 0],
                               'x', 'z', excite=excite, Feed_R=config.feed_R,
                               FeedShift=8.0, MeasPlaneShift=PLEN - 8.0, priority=10)
    p1 = mslport(1, -x_out, -a, True,  1)   # BL  input
    p2 = mslport(2, -x_out,  a, True,  0)   # TL
    p3 = mslport(3,  x_out, -a, False, 0)   # BR
    p4 = mslport(4,  x_out,  a, False, 0)   # TR

    mesh.SmoothMeshLines('all', config.mesh_res, 1.3)
    return FDTD, CSX, (p1, p2, p3, p4)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    FDTD, _CSX, ports = build()
    sp = tempfile.mkdtemp(prefix='coupler_')
    try:
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))
        f = np.linspace(config.f_target - 120e6, config.f_target + 120e6, 121)
        for p in ports:
            p.CalcPort(sp, f)
        i0 = int(np.argmin(np.abs(f - config.f_target)))
        a1 = ports[0].uf_inc[i0]
        names = ['S11(BL/in)', 'S21(TL)', 'S31(BR)', 'S41(TR)']
        print(f'\nBranch-line coupler  (arm={ARM:.1f} mm  W50={W50}  W35={W35}  '
              f'NrTS={NrTS}  f={config.f_target/1e6:.2f} MHz)')
        print(f'{"param":>12} {"|S| dB":>9} {"phase deg":>10}')
        S = {}
        for n, p in enumerate(ports):
            s = (p.uf_ref[i0] / a1) if n else (p.uf_ref[i0] / a1)
            S[names[n]] = s
            print(f'{names[n]:>12} {20*np.log10(abs(s)+1e-30):>9.2f} {np.degrees(np.angle(s)):>10.1f}')
        # identify outputs (two largest of S21/S31/S41) and their phase diff
        outs = sorted([('S21(TL)', S['S21(TL)']), ('S31(BR)', S['S31(BR)']),
                       ('S41(TR)', S['S41(TR)'])], key=lambda kv: -abs(kv[1]))
        (n1, v1), (n2, v2), (n3, v3) = outs
        dphi = (np.degrees(np.angle(v1)) - np.degrees(np.angle(v2)) + 180) % 360 - 180
        print(f'\n  OUTPUTS (two strongest): {n1} {20*np.log10(abs(v1)):+.2f} dB, '
              f'{n2} {20*np.log10(abs(v2)):+.2f} dB   |   ISOLATED: {n3} '
              f'{20*np.log10(abs(v3)):+.2f} dB')
        print(f'  output phase diff ({n1} - {n2}) = {dphi:+.1f} deg   '
              f'(target |Δ|≈90; balance Δ|S|={20*np.log10(abs(v1))-20*np.log10(abs(v2)):+.2f} dB)')
        print(f'  input match S11 = {20*np.log10(abs(S["S11(BL/in)"])):+.2f} dB')
    finally:
        shutil.rmtree(sp, ignore_errors=True)


if __name__ == '__main__':
    main()

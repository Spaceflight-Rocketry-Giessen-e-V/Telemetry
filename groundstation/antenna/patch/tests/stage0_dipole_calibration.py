# -*- coding: utf-8 -*-
"""Stage 0 — NF2FF calibration against a lossless half-wave dipole.

A center-fed thin half-wave dipole in free space (PEC metal, air, no loss) has a
KNOWN peak directivity of 2.15 dBi and ~100 % radiation efficiency. This harness
builds one, runs a short FDTD, and checks that the project's NF2FF + port post-
processing reproduces both — the calibration that makes the absolute efficiency /
realised-gain numbers (postproc._band_sweep) trustworthy.

It pins down two things the patch results depend on:

  1. openEMS ``nf2ff.Dmax`` is a LINEAR directivity ratio, NOT dBi. The dipole's
     Dmax ≈ 1.64 → 10·log10 = 2.15 dBi (metrics.directivity_dbi). Reporting the raw
     ratio as "dBi" under-reads directivity by that log.
  2. η_rad = Prad / P_acc is absolute-correct: a lossless dipole gives ≈ 1.00, so a
     low η on the patch (≈ 3 %: branch-line coupler dumping the feed mismatch into the
     isolated-port resistor) is PHYSICAL, not an NF2FF normalisation artefact.

Gate (printed PASS/FAIL): directivity within ±0.5 dB of 2.15 dBi, η_rad within
[0.90, 1.05], and η_tot ≈ (1 − |Γ|²) within ±5 %.

Usage:
    python tests/stage0_dipole_calibration.py
    STAGE0_NRTS=20000 python tests/stage0_dipole_calibration.py   # faster / coarser
"""

import _bootstrap  # noqa: F401  — openEMS DLL discovery + project root on sys.path (keep first)

import os
import shutil
import sys
import tempfile

import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0

import config
from src.metrics import directivity_dbi, radiation_efficiency

NrTS = int(os.environ.get('STAGE0_NRTS', '30000'))

DIPOLE_DIRECTIVITY_DBI = 2.15   # textbook half-wave dipole peak directivity


def run_dipole(f0: float = None) -> dict:
    """Build + run the lossless half-wave dipole; return calibration metrics."""
    f0  = f0 or config.f_target
    fc  = config.fc
    lam = C0 / f0 / 1e-3                       # mm
    L   = 0.47 * lam                           # ~half-wave (slightly short → resonant)
    gap = 2.0                                  # feed gap (mm)
    rad = 1.0                                  # half-width of the square wire (mm)
    res = C0 / (f0 + fc) / 1e-3 / 20.0         # ~λ/20 mesh (mm)
    air = 0.6 * lam                            # ≥ λ/2 clearance to the PML
    box = np.array([2 * (rad + air), 2 * (rad + air), 2 * (L / 2 + air)])

    FDTD = openEMS(NrTS=NrTS, EndCriteria=1e-5)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
    mesh.AddLine('x', [-box[0] / 2, 0, box[0] / 2])
    mesh.AddLine('y', [-box[1] / 2, 0, box[1] / 2])
    mesh.AddLine('z', [-box[2] / 2, box[2] / 2])

    dip = CSX.AddMetal('dipole')
    dip.AddBox(start=[-rad, -rad,  gap / 2], stop=[rad, rad,  L / 2], priority=10)
    dip.AddBox(start=[-rad, -rad, -L / 2  ], stop=[rad, rad, -gap / 2], priority=10)
    # resolve the wire + the feed gap (gap < λ/20, so it must be meshed explicitly or
    # the lumped-port box collapses on snapping), + a centre line so the voltage probe
    # (integrated at the box centre) stays a clean 1-D line.
    mesh.AddLine('z', np.linspace(-L / 2, L / 2, 81))
    mesh.AddLine('z', [-gap / 2, -gap / 4, 0.0, gap / 4, gap / 2])
    mesh.AddLine('x', [-rad, 0.0, rad]); mesh.AddLine('y', [-rad, 0.0, rad])

    # Lumped port across the gap. The box needs x/y AREA (the current probe is a loop
    # in the plane ⟂ to z; a zero-area box degenerates to a point → snapping fails),
    # while the voltage probe runs up the centre line.
    port = FDTD.AddLumpedPort(1, 50, [-rad, -rad, -gap / 2], [rad, rad, gap / 2],
                              'z', excite=1, priority=12)
    mesh.SmoothMeshLines('all', res, 1.4)
    nf2ff = FDTD.CreateNF2FFBox()

    sp = tempfile.mkdtemp(prefix='stage0_dipole_')
    try:
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=(os.cpu_count() or 0))
        f  = np.array([f0])
        port.CalcPort(sp, f)
        th = np.arange(0.0, 180.001, 1.0)
        ph = np.arange(0.0, 360.0, 2.0)
        r  = nf2ff.CalcNF2FF(sp, list(f), theta=th, phi=list(ph), center=[0, 0, 0])
        Prad = float(r.Prad[0])
        Pacc = float(np.real(port.P_acc[0])); Pinc = float(np.real(port.P_inc[0]))
        gamma = float(np.abs(port.uf_ref[0] / port.uf_inc[0]))
        return dict(D_dBi=float(directivity_dbi(r.Dmax[0])),
                    eta_rad=float(radiation_efficiency(Prad, Pacc)),
                    eta_tot=float(radiation_efficiency(Prad, Pinc)),
                    gamma=gamma)
    finally:
        shutil.rmtree(sp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print(f'Stage-0 NF2FF calibration — lossless half-wave dipole  (NrTS={NrTS}, '
          f'f={config.f_target/1e6:.1f} MHz)')
    r = run_dipole()
    eta_tot_expect = 1.0 - r['gamma'] ** 2

    d_ok   = abs(r['D_dBi'] - DIPOLE_DIRECTIVITY_DBI) <= 0.5
    er_ok  = 0.90 <= r['eta_rad'] <= 1.05
    et_ok  = abs(r['eta_tot'] - eta_tot_expect) <= 0.05

    print(f'  directivity   : {r["D_dBi"]:+.2f} dBi   (expect {DIPOLE_DIRECTIVITY_DBI:+.2f}'
          f' ± 0.5)   [{"PASS" if d_ok else "FAIL"}]')
    print(f'  η_rad         : {r["eta_rad"]*100:.1f} %    (expect ~100 %)            '
          f'[{"PASS" if er_ok else "FAIL"}]')
    print(f'  η_tot         : {r["eta_tot"]*100:.1f} %    (expect 1-|Γ|² = '
          f'{eta_tot_expect*100:.1f} %)   [{"PASS" if et_ok else "FAIL"}]')
    print(f'  |Γ| = {r["gamma"]:.3f}  (S11 = {20*np.log10(r["gamma"]):.1f} dB)')

    ok = d_ok and er_ok and et_ok
    print(f'\n  CALIBRATION {"PASSED — NF2FF directivity & efficiency are trustworthy." if ok else "FAILED — do NOT trust absolute efficiency/realised gain."}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

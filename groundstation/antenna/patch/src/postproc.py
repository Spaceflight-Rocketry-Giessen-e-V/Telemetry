# -*- coding: utf-8 -*-
"""Post-processing: S11, axial ratio, impedance, far-field, VTK output, results.json."""

import glob
import json
import os
import shutil

import numpy as np

import config
from src import plotting
from src.metrics import axial_ratio_db, s11_db


_PARAVIEW_README = """\
RHCP Patch Antenna — ParaView visualisation guide
==================================================

{header}

1. FAR-FIELD RADIATION PATTERN  (farfield_rhcp.vtk)
-----------------------------------------------------
This is the 3D radiation pattern as a closed surface mesh.
Each vertex direction in space; radius = directivity shape.
The SCALARS field "Directivity_dBi" holds the true dBi values.

Steps:
  a. File > Open > farfield_rhcp.vtk  → Apply.
  b. Change colouring from "Solid Color" to "Directivity_dBi".
  c. Click the rainbow auto-scale button.
  d. View > Orientation Axes  (+Z = boresight / sky).

2. SURFACE STANDING-WAVE ANIMATION  (E_patch_surf/ and J_patch_surf/ subfolders)
----------------------------------------------------------------------------------
Files are in two subfolders:
  E_patch_surf/  — E-field phasor snapshots at the substrate mid-plane
                   (reveals TM010 resonant mode)
  J_patch_surf/  — surface current phasor snapshots on the patch conductor
                   (reveals CP mode splitting and feed coupling)

Each subfolder contains files named  *_p=000.vtr  *_p=017.vtr  ... (every ~17°
through one full RF cycle), plus _abs.vtr (magnitude) and _arg.vtr (phase angle).

QUICKEST WAY: use the auto-generated script load_in_paraview.py (same folder).
  pvpython load_in_paraview.py          ← batch mode
  — or paste into  View > Tools > Python Console  while ParaView is open.

Manual step-by-step:
  a. File > Open > E_patch_surf > E_patch_surf_*_p=*.vtr
     Select all files, ParaView groups them as a time series  → Apply.
  b. Press Play in the Animation toolbar to cycle through RF phases.
  c. Colour by the field array shown in Properties > Coloring.

Tip for J_patch_surf:
  Use Filters > Glyph (Arrow, scale by magnitude) to visualise the rotating
  surface current.  Smooth circular rotation = correct RHCP balance.
  Figure-eight or wobbling = truncation needs adjustment.

If the subfolders are absent:
  export_vtk_surf may be False in run.py, or the openEMS build does not
  support DumpType=10/12 (requires >= r700).
"""


class PostProcessor:
    """Runs full post-processing on the final FDTD simulation.

    After calling run(), access the computed antenna parameters via
    the results property, which returns a dict suitable for results.json
    and KiCad export.
    """

    def __init__(self, port, nf2ff_box, run_dir, sim_path, graphs_path, vtk_path,
                 opt_W, opt_delta, opt_y_inset, opt_log,
                 opt_sub_hw=None,
                 post_proc_only=False, export_vtk_surf=True):
        self._port           = port
        self._nf2ff          = nf2ff_box
        self._run_dir        = run_dir
        self._sim_path       = sim_path
        self._graphs_path    = graphs_path
        self._vtk_path       = vtk_path
        self.opt_W           = opt_W
        self.opt_delta       = opt_delta
        self.opt_y_inset     = opt_y_inset
        self.opt_sub_hw      = (float(opt_sub_hw) if opt_sub_hw is not None
                                else config.SUB_HW_DEFAULT)
        self.opt_log         = opt_log
        self._post_proc_only = post_proc_only
        self._export_vtk_surf = export_vtk_surf
        self._results        = None

    # ── public interface ──────────────────────────────────────────────

    def run(self):
        """Compute all metrics, write graphs, VTK files, and results.json."""
        self._s11_sweep()
        self._axial_ratio_sweep()
        self._farfield()
        self._write_vtk_farfield()
        self._copy_standing_wave_vtk()
        self._write_paraview_script()
        self._opt_trace_plots()
        self._write_results_json()
        self._write_paraview_readme()
        self._print_summary()

    @property
    def results(self) -> dict:
        if self._results is None:
            raise RuntimeError('call run() before accessing results')
        return self._results

    # ── internal steps ────────────────────────────────────────────────

    def _s11_sweep(self):
        f_sweep = np.linspace(
            max(100e6, config.f_target - config.fc),
            config.f_target + config.fc, 401)
        self._port.CalcPort(self._sim_path, f_sweep)

        s11_dB = s11_db(self._port.uf_ref, self._port.uf_inc)
        Zin    = self._port.uf_tot / self._port.if_tot

        # CP operating frequency: centroid of matched bandwidth (works for both
        # single-mode and split-mode patches; robust at coarse and fine grids).
        # NOTE: intentionally NOT metrics.cp_center_freq — this reporting path
        # also needs s11_at_res and falls back to f_target (not argmin) when the
        # patch never matches below -10 dB, so the two must stay distinct.
        mask = s11_dB < -10
        if mask.any():
            weights    = -s11_dB[mask]
            f_res      = float(np.average(f_sweep[mask], weights=weights))
            s11_at_res = float(np.interp(f_res, f_sweep, s11_dB))
        else:
            f_res      = config.f_target
            s11_at_res = float(np.interp(config.f_target, f_sweep, s11_dB))

        # Detect individual mode frequencies for reporting (fine 401-pt grid)
        dsign = np.sign(np.diff(s11_dB))
        lmin  = np.where((dsign[:-1] <= 0) & (dsign[1:] > 0))[0] + 1
        lmin  = lmin[s11_dB[lmin] < -10]
        if len(lmin) >= 2:
            lmin       = lmin[np.argsort(s11_dB[lmin])[:2]]
            lmin.sort()
            f_mode1    = float(f_sweep[lmin[0]])
            f_mode2    = float(f_sweep[lmin[1]])
            mode_split = f_mode2 - f_mode1
        else:
            f_mode1 = f_mode2 = f_res
            mode_split = 0.0

        if mask.any():
            print(f'\nCP centre: {f_res/1e6:.2f} MHz  '
                  f'(S11 = {s11_at_res:.1f} dB  '
                  f'offset = {(f_res-config.f_target)/1e6:+.2f} MHz)')
            if mode_split > 5e6:
                print(f'  Mode split: {f_mode1/1e6:.2f} / {f_mode2/1e6:.2f} MHz  '
                      f'(delta = {mode_split/1e6:.1f} MHz)')
        else:
            print('\nNo resonance found below -10 dB — using f_target for far-field.')

        self._f_sweep    = f_sweep
        self._s11_dB     = s11_dB
        self._Zin        = Zin
        self._f_res      = f_res
        self._s11_at_res = s11_at_res
        self._f_mode1    = f_mode1
        self._f_mode2    = f_mode2
        self._mode_split = mode_split

        plotting.plot_s11(
            f_sweep, s11_dB,
            config.f_target, f_res, s11_at_res,
            self.opt_W, self.opt_delta,
            os.path.join(self._graphs_path, 's11.png'),
            f_mode1=f_mode1, f_mode2=f_mode2)

        plotting.plot_impedance(
            f_sweep, np.real(Zin), np.imag(Zin),
            config.f_target,
            os.path.join(self._graphs_path, 'input_impedance.png'))

    def _axial_ratio_sweep(self):
        print('Computing axial ratio sweep...')
        f_ar = np.linspace(
            max(100e6, config.f_target - config.fc),
            config.f_target + config.fc, 101)
        res_ar = self._nf2ff.CalcNF2FF(
            self._sim_path, f_ar,
            theta=[1.0, 2.0, 3.0],
            phi=[0., 90., 180., 270.],
            center=[0, 0, 1e-3],
            outfile=os.path.join(self._sim_path, 'nf2ff_ar.h5'))

        # True axial ratio AR = (R+L)/|R-L| in dB (≥0); handedness from sign of
        # (R-L). Uses the same metrics.axial_ratio_db as the optimiser so opt
        # and final agree.
        ar_vs_f_raw = np.empty(len(f_ar))
        rhcp_vs_f   = np.empty(len(f_ar), dtype=bool)
        for n in range(len(f_ar)):
            ar_vs_f_raw[n], rhcp_vs_f[n] = axial_ratio_db(
                res_ar.E_cprh[n], res_ar.E_cplh[n])
        _w = 5
        ar_vs_f = np.convolve(ar_vs_f_raw, np.ones(_w) / _w, mode='same')
        ar_vs_f[:_w // 2]  = ar_vs_f_raw[:_w // 2]
        ar_vs_f[-_w // 2:] = ar_vs_f_raw[-_w // 2:]

        self._f_ar        = f_ar
        self._ar_vs_f     = ar_vs_f
        self._ar_vs_f_raw = ar_vs_f_raw
        self._ar_at_ft    = float(np.interp(config.f_target, f_ar, ar_vs_f))
        self._rhcp_at_ft  = bool(rhcp_vs_f[int(np.argmin(np.abs(f_ar - config.f_target)))])

        # CP (AR ≤ 3 dB) bandwidth, for reporting
        in_band = ar_vs_f <= 3.0
        if in_band.any():
            self._ar_bw = float(f_ar[in_band].max() - f_ar[in_band].min())
        else:
            self._ar_bw = 0.0

        print(f'AR at f_target: {self._ar_at_ft:.1f} dB  '
              f'({"RHCP" if self._rhcp_at_ft else "LHCP"} dominant)  '
              f'[AR≤3 dB bandwidth ≈ {self._ar_bw/1e6:.1f} MHz]')

        plotting.plot_axial_ratio(
            f_ar, ar_vs_f, ar_vs_f_raw,
            config.f_target,
            os.path.join(self._graphs_path, 'axial_ratio.png'),
            rhcp=self._rhcp_at_ft)

    def _farfield(self):
        # 2D cuts
        theta_2d = np.arange(-180.0, 180.0, 2.0)
        res_2d   = self._nf2ff.CalcNF2FF(
            self._sim_path, self._f_res, theta_2d, [0., 90.],
            center=[0, 0, 1e-3])
        E_norm_2d = (20.0 * np.log10(res_2d.E_norm[0] /
                     np.max(res_2d.E_norm[0]) + 1e-30) + res_2d.Dmax[0])
        plotting.plot_farfield_2d(
            theta_2d, E_norm_2d, self._f_res, res_2d.Dmax[0],
            os.path.join(self._graphs_path, 'farfield_2d.png'))

        # 3D pattern
        theta_3d = np.arange(  0.0, 181.0, 2.0)
        phi_3d   = np.arange(  0.0, 360.0, 2.0)
        res_3d   = self._nf2ff.CalcNF2FF(
            self._sim_path, self._f_res, theta_3d, phi_3d,
            center=[0, 0, 1e-3])
        E_3d  = res_3d.E_norm[0]
        self._Dmax = res_3d.Dmax[0]
        E_dBi = 20.0 * np.log10(E_3d / np.max(E_3d) + 1e-12) + self._Dmax
        E_lin = np.maximum(E_dBi + 20, 0)
        E_lin = E_lin / np.max(E_lin)

        TH, PH = np.meshgrid(np.deg2rad(theta_3d), np.deg2rad(phi_3d), indexing='ij')
        self._X    = E_lin * np.sin(TH) * np.cos(PH)
        self._Y    = E_lin * np.sin(TH) * np.sin(PH)
        self._Z    = E_lin * np.cos(TH)
        self._E_lin  = E_lin
        self._E_dBi  = E_dBi

        plotting.plot_farfield_3d(
            self._X, self._Y, self._Z, E_lin, E_dBi,
            self._f_res, self._Dmax,
            os.path.join(self._graphs_path, 'farfield_3d.png'))

    def _write_vtk_farfield(self):
        vtk_ff = os.path.join(self._vtk_path, 'farfield_rhcp.vtk')
        try:
            ntheta, nphi = self._X.shape
            N = ntheta * nphi
            M = (ntheta - 1) * (nphi - 1)

            pts  = np.column_stack([self._X.ravel(),
                                    self._Y.ravel(),
                                    self._Z.ravel()])
            scal = self._E_dBi.ravel()

            ii = np.arange(ntheta - 1)
            jj = np.arange(nphi  - 1)
            I, J = np.meshgrid(ii, jj, indexing='ij')
            I = I.ravel(); J = J.ravel()
            p00 = I * nphi + J
            p01 = I * nphi + J + 1
            p10 = (I + 1) * nphi + J
            p11 = (I + 1) * nphi + J + 1
            quads = np.column_stack([np.full(M, 4), p00, p01, p11, p10])

            with open(vtk_ff, 'w', encoding='utf-8') as fh:
                fh.write('# vtk DataFile Version 3.0\n')
                fh.write(f'RHCP Patch Far-Field at {self._f_res/1e6:.4f} MHz'
                         f'  Dmax={self._Dmax:.2f} dBi\n')
                fh.write('ASCII\nDATASET POLYDATA\n')
                fh.write(f'POINTS {N} float\n')
                np.savetxt(fh, pts,   fmt='%.6f')
                fh.write(f'POLYGONS {M} {M * 5}\n')
                np.savetxt(fh, quads, fmt='%d')
                fh.write(f'POINT_DATA {N}\n')
                fh.write('SCALARS Directivity_dBi float 1\nLOOKUP_TABLE default\n')
                np.savetxt(fh, scal, fmt='%.4f')
            print(f'Far-field VTK written: {vtk_ff}')
        except Exception as e:
            print(f'VTK write failed: {e}')

    def _copy_standing_wave_vtk(self):
        if self._post_proc_only or not self._export_vtk_surf:
            return
        any_found = False
        for name in ('E_patch_surf', 'J_patch_surf'):
            sub  = os.path.join(self._vtk_path, name)
            os.makedirs(sub, exist_ok=True)
            srcs = glob.glob(os.path.join(self._sim_path, f'{name}*.vt?'))
            count = 0
            for src in srcs:
                dst = os.path.join(sub, os.path.basename(src))
                try:
                    shutil.copy2(src, dst)
                    count += 1
                except Exception as e:
                    print(f'  VTK copy failed ({os.path.basename(src)}): {e}')
            if count:
                print(f'Surface VTK ({name}): {count} files → {sub}')
                any_found = True
            else:
                print(f'Surface VTK ({name}): no files found in sim_data/')
        if not any_found:
            print('  openEMS DumpType=10/12 may not be supported by this build (needs >= r700)')

    def _opt_trace_plots(self):
        if not self.opt_log:
            return
        p0 = [x for x in self.opt_log if x['phase'] == '0']
        plotting.plot_opt_phase0(
            p0, config.f_target, self.opt_W,
            os.path.join(self._graphs_path, 'opt_phase0_width.png'))
        plotting.plot_opt_trace(
            self.opt_log, self.opt_W,
            os.path.join(self._graphs_path, 'opt_trace.png'))

    def _write_results_json(self):
        self._results = {
            'W_mm':               round(self.opt_W, 4),
            'delta_mm':           round(self.opt_delta, 4),
            'y_inset_mm':         round(self.opt_y_inset, 4),
            'sub_hw_mm':          round(self.opt_sub_hw, 4),
            'gp_edge_mm':         round(self.opt_sub_hw * 2, 4),
            'f_target_MHz':       config.f_target / 1e6,
            'substrate_h_mm':     config.substrate_thickness,
            'substrate_epsR':     config.substrate_epsR,
            'substrate_material': 'NP-140F',
        }
        path = os.path.join(self._run_dir, 'results.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._results, f, indent=2)
        print(f'Results JSON  : {path}')
        print(f'  → run: python -m src.kicad_export "{path}"')

    def _write_paraview_readme(self):
        header = (f'Simulation: {config.f_target/1e6:.4f} MHz target, '
                  f'resonance {self._f_res/1e6:.2f} MHz, '
                  f'Dmax = {self._Dmax:.1f} dBi')
        path = os.path.join(self._vtk_path, 'HOW_TO_OPEN_IN_PARAVIEW.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(_PARAVIEW_README.format(header=header))

    def _write_paraview_script(self):
        """Write load_in_paraview.py to vtk/ — run with pvpython or paste into ParaView console."""
        script = f'''\
# Auto-generated by run.py  ({config.f_target/1e6:.4f} MHz  Dmax≈{self._Dmax:.1f} dBi)
# Usage:
#   pvpython load_in_paraview.py          (batch render, then open with paraview --script)
#   paste into  ParaView > Tools > Python Console  (interactive)
#
# Requires ParaView >= 5.10 with Python support (pvpython / pvbatch).

from paraview.simple import *
import os, glob

_HERE = os.path.dirname(os.path.abspath(__file__))

Render()  # open default view

# ── 1. Far-field radiation pattern ───────────────────────────────────────────
_ff_path = os.path.join(_HERE, 'farfield_rhcp.vtk')
if os.path.exists(_ff_path):
    ff = LegacyVTKReader(FileNames=[_ff_path])
    RenameSource('Far-field {config.f_target/1e6:.2f} MHz', ff)
    Show(ff)
    dp = GetDisplayProperties(ff)
    ColorBy(dp, ('POINTS', 'Directivity_dBi'))
    dp.SetScalarBarVisibility(GetActiveViewOrCreate('RenderView'), True)
    GetActiveViewOrCreate('RenderView').ResetCamera()
    Render()
    print('Loaded far-field pattern.')
else:
    print('farfield_rhcp.vtk not found.')

# ── 2. Surface E-field animation (phase sequence) ────────────────────────────
_e_dir   = os.path.join(_HERE, 'E_patch_surf')
_e_files = sorted(glob.glob(os.path.join(_e_dir, '*_p=*.vtr')))
if _e_files:
    e_src = XMLRectilinearGridReader(FileNames=_e_files)
    RenameSource('E-field surface (phase anim)', e_src)
    e_src.UpdatePipeline()
    Show(e_src)
    scene = GetAnimationScene()
    scene.NumberOfFrames = len(_e_files)
    scene.PlayMode = 'Sequence'
    print(f'Loaded E-field animation: {{len(_e_files)}} frames.')
else:
    print('E_patch_surf not found — export_vtk_surf may be False.')

# ── 3. Surface J-field animation (phase sequence) ────────────────────────────
_j_dir   = os.path.join(_HERE, 'J_patch_surf')
_j_files = sorted(glob.glob(os.path.join(_j_dir, '*_p=*.vtr')))
if _j_files:
    j_src = XMLRectilinearGridReader(FileNames=_j_files)
    RenameSource('J-field surface (phase anim)', j_src)
    j_src.UpdatePipeline()
    Show(j_src)
    print(f'Loaded J-field animation: {{len(_j_files)}} frames.')
else:
    print('J_patch_surf not found.')

Render()
print('Done.  Use Animation View (View > Animation View) to play the phase sequence.')
'''

        path = os.path.join(self._vtk_path, 'load_in_paraview.py')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(script)
        print(f'ParaView script  : {path}')

    def _print_summary(self):
        s11_at_ft = float(np.interp(config.f_target, self._f_sweep, self._s11_dB))
        print(f"""
{'═'*55}
  RHCP PATCH ANTENNA — {config.f_target/1e6:.2f} MHz
{'═'*55}
  Substrate  : NP-140F  εr={config.substrate_epsR}  tanδ={config.substrate_tanD}  h={config.substrate_thickness} mm
  Patch side : {self.opt_W:.2f} mm
  Truncation : {self.opt_delta:.2f} mm  (Δ/W = {self.opt_delta/self.opt_W:.3f})
  Feed inset : {self.opt_y_inset:.2f} mm
  Gnd plane  : {self.opt_sub_hw*2:.1f} × {self.opt_sub_hw*2:.1f} mm
  S11 @ f0   : {s11_at_ft:.1f} dB
  f_CP_centre: {self._f_res/1e6:.2f} MHz  (offset {(self._f_res-config.f_target)/1e6:+.2f} MHz){f'  [modes: {self._f_mode1/1e6:.1f} / {self._f_mode2/1e6:.1f} MHz  split {self._mode_split/1e6:.1f} MHz]' if self._mode_split > 5e6 else ''}
  AR  @ f0   : {self._ar_at_ft:.1f} dB  ({'RHCP' if self._rhcp_at_ft else 'LHCP'} dominant)  [AR≤3 dB BW ≈ {self._ar_bw/1e6:.1f} MHz]
  Dmax       : {self._Dmax:.1f} dBi  @ {self._f_res/1e6:.2f} MHz
  Sim data   : {self._sim_path}
  Graphs     : {self._graphs_path}
  ParaView   : {self._vtk_path}
{'═'*55}""")

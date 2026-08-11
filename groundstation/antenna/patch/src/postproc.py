# -*- coding: utf-8 -*-
"""Post-processing for the single-feed corner-truncated RHCP patch.

Driven by a ``PatchParams`` object and the ``build_patch_sim`` MSL-port model. Adds
the wide-beam COVERAGE reporting the backup-antenna role needs: AR and RHCP gain
over an elevation cone, the AR<=3 dB beamwidth, the worst AR over the coverage
cone, and the RHCP sense — alongside the S11 / AR-vs-f / far-field / efficiency /
VTK outputs. Writes a results.json keyed by the PatchParams fields so the KiCad
export re-derives the same board via geometry.single_feed_layout().
"""

import glob
import json
import os
import shutil

import numpy as np

import config
from src import plotting
from src.geometry import single_feed_layout
from src.metrics import (axial_ratio_db, s11_db, ar_beamwidth_deg,
                         worst_ar_over_cone, min_gain_over_cone,
                         directivity_dbi, radiation_efficiency)
from src.params import PatchParams


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

2. SURFACE CURRENT ANIMATION  (J_patch_surf/ subfolder)
----------------------------------------------------------------------------------
  J_patch_surf/  — surface current phasor snapshots on the top copper
                   (truncated patch + feed; reveals the rotating CP current).

Each subfolder contains files named  *_p=000.vtr  *_p=017.vtr  ... (every ~17°
through one full RF cycle), plus _abs.vtr (magnitude) and _arg.vtr (phase angle).

QUICKEST WAY: use the auto-generated script load_in_paraview.py (same folder).
  pvpython load_in_paraview.py          ← batch mode
  — or paste into  View > Tools > Python Console  while ParaView is open.

Tip for J_patch_surf:
  Use Filters > Glyph (Arrow, scale by magnitude) to visualise the rotating
  surface current.  Smooth circular rotation over the patch = correct RHCP
  balance; a wobble / figure-eight means the truncation/resonance needs tuning.

If the subfolder is absent:
  export_vtk_surf may be False in run.py, or the openEMS build does not
  support DumpType=12 (requires >= r700).
"""


class PostProcessor:
    """Runs full post-processing on the final FDTD simulation.

    After calling run(), access the computed antenna parameters via the
    ``results`` property, which returns a dict suitable for results.json and the
    KiCad export.
    """

    def __init__(self, port, nf2ff_box, run_dir, sim_path, graphs_path, vtk_path,
                 params: PatchParams, opt_log,
                 post_proc_only=False, export_vtk_surf=True):
        self._port            = port
        self._nf2ff           = nf2ff_box
        self._run_dir         = run_dir
        self._sim_path        = sim_path
        self._graphs_path     = graphs_path
        self._vtk_path        = vtk_path
        self.params           = params
        self.opt_log          = opt_log
        self._post_proc_only  = post_proc_only
        self._export_vtk_surf = export_vtk_surf
        self._results         = None
        # realised board (the layout may grow sub_hw to fit the patch + margin)
        self._layout          = single_feed_layout(params)

    # ── public interface ──────────────────────────────────────────────

    def run(self):
        """Compute all metrics, write graphs, VTK files, and results.json."""
        self._s11_sweep()
        self._axial_ratio_sweep()
        self._farfield()
        self._band_sweep()
        self._coverage_cuts()
        self._write_vtk_farfield()
        self._copy_standing_wave_vtk()
        self._write_paraview_script()
        self._opt_trace_plots()
        self._write_results_json()
        self._summary_sheet()
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

        # Complex reflection Γ = uf_ref/uf_inc (referenced to the port's 50 Ω line):
        # S11, VSWR and the Smith locus all derive from this ONE quantity, so they agree.
        gamma  = self._port.uf_ref / self._port.uf_inc
        s11_dB = s11_db(self._port.uf_ref, self._port.uf_inc)
        # De-embedded, match-CONSISTENT input impedance Zin = Z0·(1+Γ)/(1−Γ), derived from
        # the SAME reflection Γ as S11/VSWR so all three agree. Preferred over the raw
        # uf_tot/if_tot terminal impedance, which mixes in the standing-wave phase along the
        # feed stub and so doesn't read as the 50 Ω-referred match the antenna achieves.
        Z0  = float(config.feed_R)
        Zin = Z0 * (1.0 + gamma) / (1.0 - gamma)
        # Power flows into the network at each f (for radiation efficiency in _band_sweep).
        # P_acc = accepted (incident − reflected); P_inc = incident (available). η_rad uses
        # P_acc (excludes mismatch), η_tot / realised gain uses P_inc (includes mismatch).
        self._gamma_sweep = gamma
        self._P_acc_sweep = 0.5 * np.real(self._port.uf_tot
                                          * np.conj(self._port.if_tot))
        self._P_inc_sweep = 0.5 * np.real(self._port.uf_inc
                                          * np.conj(self._port.if_inc))

        # CP operating frequency: -S11-weighted centroid of the matched band
        # (robust for single-mode and split-mode patches at coarse & fine grids).
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

        title_note = (f'W = {self.params.W_mm:.1f} mm  '
                      f'trunc = {self.params.trunc_mm:.1f} mm')
        plotting.plot_s11(
            f_sweep, s11_dB,
            config.f_target, f_res, s11_at_res,
            title_note,
            os.path.join(self._graphs_path, 's11.png'),
            f_mode1=f_mode1, f_mode2=f_mode2)

        plotting.plot_impedance(
            f_sweep, np.real(Zin), np.imag(Zin),
            config.f_target,
            os.path.join(self._graphs_path, 'input_impedance.png'))
        plotting.plot_vswr(
            f_sweep, np.abs(self._gamma_sweep), config.f_target,
            os.path.join(self._graphs_path, 'vswr.png'))
        plotting.plot_smith(
            self._gamma_sweep, f_sweep, config.f_target,
            config.f_target - 60e6, config.f_target + 60e6,
            os.path.join(self._graphs_path, 'smith.png'))

    def _band_sweep(self):
        """Directivity, realised gain & efficiency + AR-beamwidth vs frequency.

        One multi-frequency NF2FF call over a FINE full sphere gives, per f: the peak
        directivity (dBi = 10·log10(Dmax), Dmax being openEMS's LINEAR ratio), the
        total radiated power Prad, the boresight RHCP directivity, boresight AR, and
        the AR≤3 dB beamwidth. Combined with the port accepted/incident power (from
        _s11_sweep) this yields the radiation efficiency η_rad = Prad/P_acc, total
        efficiency η_tot = Prad/P_inc, and realised gain = directivity + 10·log10(η_tot).

        η is dipole-validated (a lossless half-wave dipole gives η_rad ≈ 1.00 and
        Dmax → 2.19 dBi vs the textbook 2.15), so η here is PHYSICAL: it captures the
        FR-4 dielectric loss + any feed mismatch (copper is PEC in-sim). As a guard the
        efficiency outputs are still gated on a sanity check (0 < η_rad ≲ 1) and dropped
        to directivity-only if it fails.
        """
        print('Computing band sweep (directivity / efficiency / AR-beamwidth vs frequency)...')
        f_band = np.linspace(config.f_target - 50e6, config.f_target + 50e6, 21)
        # FINE full sphere: 2° in θ, 15° in φ (keeps 0/45/90/135 for the AR cuts) so the
        # Prad solid-angle integral and Dmax are accurate (verified: Prad converged vs a
        # 1°/2° sphere to <1%). Center at the patch (origin), not the offset board centre.
        th = np.arange(0.0, 180.1, 2.0)
        ph = np.arange(0.0, 360.0, 15.0)
        res = self._nf2ff.CalcNF2FF(
            self._sim_path, list(f_band), theta=th, phi=list(ph),
            center=[0, 0, 1e-3], outfile=os.path.join(self._sim_path, 'nf2ff_band.h5'))

        th_cone = th[th <= 90.0]
        ph_cov  = np.array([0.0, 45.0, 90.0, 135.0])
        j_cov   = [int(np.argmin(np.abs(ph - p))) for p in ph_cov]
        i0      = 1 if len(th) > 1 else 0          # off-axis ring (RHCP/LHCP singular on-axis)

        directivity = np.empty(len(f_band))        # dBi
        bs_rhcp     = np.empty(len(f_band))        # dBic
        ar_bs       = np.empty(len(f_band))
        ar_bw       = np.empty(len(f_band))
        Prad        = np.asarray(res.Prad, dtype=float)
        for n in range(len(f_band)):
            D_dBi = float(directivity_dbi(res.Dmax[n]))
            E_rh = res.E_cprh[n]; E_lh = res.E_cplh[n]
            Emax = float(np.max(res.E_norm[n]))
            directivity[n] = D_dBi
            bs_rhcp[n] = D_dBi + 20.0 * np.log10(abs(E_rh[0, 0]) / Emax + 1e-12)
            ar_bs[n] = axial_ratio_db(np.array([E_rh[i0, 0]]),
                                      np.array([E_lh[i0, 0]]))[0]
            ar_w = np.array([
                max(axial_ratio_db(np.array([E_rh[(1 if i == 0 else i), j]]),
                                   np.array([E_lh[(1 if i == 0 else i), j]]))[0]
                    for j in j_cov)
                for i in range(len(th_cone))])
            ar_bw[n] = ar_beamwidth_deg(th_cone, ar_w)

        # ── efficiency & realised gain (η dipole-validated; see docstring) ──────────
        P_acc = np.interp(f_band, self._f_sweep, self._P_acc_sweep)
        P_inc = np.interp(f_band, self._f_sweep, self._P_inc_sweep)
        eta_rad = radiation_efficiency(Prad, P_acc)            # radiated / accepted
        eta_tot = radiation_efficiency(Prad, P_inc)            # radiated / incident
        # Clip η_tot to ≤1 before the realised-gain log: radiated power can never exceed
        # incident, so realised gain can never exceed directivity. An off-target NF2FF
        # normalisation artefact (η_tot[n] slightly >1 at a band edge) would otherwise
        # plot a non-physical realised-gain spike ABOVE the directivity curve (the
        # f_target sanity gate only checks the single target point).
        realised_gain = directivity + 10.0 * np.log10(np.clip(eta_tot, 1e-12, 1.0))

        i_ft = int(np.argmin(np.abs(f_band - config.f_target)))
        eta_rad_ft = float(eta_rad[i_ft]); eta_tot_ft = float(eta_tot[i_ft])
        # Trust gate: radiated power can never exceed accepted (η_rad ≤ 1); a small
        # tolerance covers solid-angle discretisation. If it fails, the NF2FF/port
        # normalisation is suspect — drop to directivity-only (the old safe behaviour).
        self._eff_ok = bool(np.isfinite(eta_rad_ft) and 0.0 < eta_rad_ft <= 1.05)
        self._eta_rad   = eta_rad_ft if self._eff_ok else float('nan')
        self._eta_tot   = eta_tot_ft if self._eff_ok else float('nan')
        # realised gain at f_target, referenced to the authoritative 3-D Dmax (_farfield)
        self._realised_gain_dBi = (float(self._Dmax) + 10.0 * np.log10(eta_tot_ft)
                                   if self._eff_ok else float('nan'))

        self._band_f = f_band
        D_ft = float(np.interp(config.f_target, f_band, directivity))
        if self._eff_ok:
            print(f'  directivity @ target ≈ {D_ft:.1f} dBi   '
                  f'η_rad {eta_rad_ft*100:.1f}%  η_tot {eta_tot_ft*100:.1f}%   '
                  f'realised gain ≈ {self._realised_gain_dBi:.1f} dBic')
            if eta_rad_ft < 0.10:
                print(f'  ! LOW radiation efficiency ({eta_rad_ft*100:.1f}%): most accepted '
                      f'power is dissipated (dielectric / feed mismatch), NOT radiated. '
                      f'Realised gain is far below directivity — re-tune the match.')
        else:
            print(f'  directivity @ target ≈ {D_ft:.1f} dBi   '
                  f'(η_rad={eta_rad_ft:.2f} failed sanity gate → efficiency/realised gain '
                  f'dropped; NF2FF/port normalisation suspect)')

        plotting.plot_gain_vs_freq(
            f_band, directivity, bs_rhcp, config.f_target,
            os.path.join(self._graphs_path, 'directivity_vs_freq.png'),
            realised_gain_dBi=(realised_gain if self._eff_ok else None),
            eta_rad=(eta_rad if self._eff_ok else None),
            eta_tot=(eta_tot if self._eff_ok else None))
        plotting.plot_ar_beamwidth_vs_freq(
            f_band, ar_bw, ar_bs, config.f_target,
            os.path.join(self._graphs_path, 'ar_beamwidth_vs_freq.png'),
            cover_cone_deg=config.COVER_CONE_DEG)

    def _axial_ratio_sweep(self):
        print('Computing axial ratio sweep...')
        # FINE grid around f_target. The single-feed CP AR null is only a few-MHz wide, so
        # a coarse grid (≈5 MHz/pt) + a wide boxcar smoothing (the old 5-pt over 5 MHz/pt =
        # 25 MHz window) refilled the null and turned a ~0.4 dB minimum into a reported ~5 dB
        # — the headline AR was a SMOOTHING ARTEFACT, not the antenna. Resolve at 0.5 MHz over
        # ±80 MHz where the null lives; sparse context points each side keep the plot shoulders.
        f_fine   = np.linspace(config.f_target - 80e6, config.f_target + 80e6, 321)  # 0.5 MHz/pt
        f_ctx_lo = np.linspace(max(100e6, config.f_target - config.fc),
                               config.f_target - 80e6, 20, endpoint=False)
        f_ctx_hi = np.linspace(config.f_target + 85e6, config.f_target + config.fc, 20)
        f_ar = np.unique(np.concatenate([f_ctx_lo, f_fine, f_ctx_hi]))
        res_ar = self._nf2ff.CalcNF2FF(
            self._sim_path, list(f_ar),
            theta=[1.0, 2.0, 3.0],
            phi=[0., 90., 180., 270.],
            center=[0, 0, 1e-3],
            outfile=os.path.join(self._sim_path, 'nf2ff_ar.h5'))

        # True axial ratio AR = (R+L)/|R-L| in dB (≥0); handedness from sign of
        # (R-L). Same metrics.axial_ratio_db the optimiser uses, so opt and final
        # agree on the metric.
        ar_vs_f_raw = np.empty(len(f_ar))
        rhcp_vs_f   = np.empty(len(f_ar), dtype=bool)
        for n in range(len(f_ar)):
            ar_vs_f_raw[n], rhcp_vs_f[n] = axial_ratio_db(
                res_ar.E_cprh[n], res_ar.E_cplh[n])
        # LIGHT 3-pt (≈1.5 MHz) smoothing only — tames single-point FDTD spikes while
        # PRESERVING the few-MHz null (a wide window over-reads the AR; see above).
        _w = 3
        _half = _w // 2                    # parenthesise: -_w // 2 == -3, not -(2)
        ar_vs_f = np.convolve(ar_vs_f_raw, np.ones(_w) / _w, mode='same')
        ar_vs_f[:_half]  = ar_vs_f_raw[:_half]
        ar_vs_f[-_half:] = ar_vs_f_raw[-_half:]

        self._f_ar        = f_ar
        self._ar_vs_f     = ar_vs_f
        self._ar_vs_f_raw = ar_vs_f_raw
        self._ar_at_ft    = float(np.interp(config.f_target, f_ar, ar_vs_f))
        self._rhcp_at_ft  = bool(rhcp_vs_f[int(np.argmin(np.abs(f_ar - config.f_target)))])
        # AR null (frequency of minimum AR). For a correctly-tuned CP patch this sits on
        # f_target; its offset is THE tuning diagnostic — note it tracks ~7 MHz BELOW the
        # S11 centroid, so matching alone does not centre the CP (the optimiser centres this).
        i_null            = int(np.argmin(ar_vs_f))
        self._f_ar_null   = float(f_ar[i_null])
        self._ar_min      = float(ar_vs_f[i_null])

        # CP (AR ≤ 3 dB) bandwidth: the CONTIGUOUS band straddling the null (not the global
        # min/max extent, which a far-off spike could inflate).
        in_band = ar_vs_f <= 3.0
        if in_band[i_null]:
            lo = i_null
            while lo > 0 and in_band[lo - 1]:
                lo -= 1
            hi = i_null
            while hi < len(in_band) - 1 and in_band[hi + 1]:
                hi += 1
            self._ar_bw = float(f_ar[hi] - f_ar[lo])
        elif in_band.any():
            self._ar_bw = float(f_ar[in_band].max() - f_ar[in_band].min())
        else:
            self._ar_bw = 0.0

        print(f'AR at f_target: {self._ar_at_ft:.2f} dB  '
              f'({"RHCP" if self._rhcp_at_ft else "LHCP"} dominant)  '
              f'[null {self._f_ar_null/1e6:.2f} MHz ({(self._f_ar_null-config.f_target)/1e6:+.1f}), '
              f'AR_min {self._ar_min:.2f} dB, AR≤3 BW ≈ {self._ar_bw/1e6:.1f} MHz]')

        plotting.plot_axial_ratio(
            f_ar, ar_vs_f, ar_vs_f_raw,
            config.f_target,
            os.path.join(self._graphs_path, 'axial_ratio.png'),
            rhcp=self._rhcp_at_ft)

    def _farfield(self):
        # Evaluate the pattern at the OPERATING frequency f_target, not the matched
        # centroid f_res. The antenna is spec'd at 869.52 MHz and the optimiser
        # selected every coverage metric at f_target; reporting Dmax/pattern at f_res
        # would describe a different frequency and could flatter a design whose
        # resonance has drifted off f_target. f_res is still reported as resonance.
        f_eval = config.f_target
        # 2D cuts. openEMS Dmax is the LINEAR directivity ratio → dBi via directivity_dbi
        # (10·log10); using it raw under-reads the dBi scale by that log (see metrics).
        theta_2d = np.arange(-180.0, 180.0, 2.0)
        res_2d   = self._nf2ff.CalcNF2FF(
            self._sim_path, f_eval, theta_2d, [0., 90.],
            center=[0, 0, 1e-3])
        D2 = float(directivity_dbi(res_2d.Dmax[0]))
        E_norm_2d = (20.0 * np.log10(res_2d.E_norm[0] /
                     np.max(res_2d.E_norm[0]) + 1e-30) + D2)
        plotting.plot_farfield_2d(
            theta_2d, np.squeeze(E_norm_2d[:, 0]), np.squeeze(E_norm_2d[:, 1]),
            f_eval, D2,
            os.path.join(self._graphs_path, 'farfield_2d.png'))

        # Polar co/cross-pol patterns (RHCP co-pol + LHCP cross-pol) in 3 principal
        # planes: XZ (φ=0) / YZ (φ=90) elevation cuts + XY (θ=90) azimuth/horizon cut.
        # All referenced to ONE Dmax/Emax (the boresight-containing cut) so the absolute
        # dBi scale is consistent across panels (the XY horizon cut is correctly low).
        Emax2 = float(np.max(res_2d.E_norm[0]))
        def _cdb(E):
            return 20.0 * np.log10(np.abs(E) / Emax2 + 1e-12) + D2
        phi_xy = np.arange(0.0, 360.0, 2.0)
        res_xy = self._nf2ff.CalcNF2FF(self._sim_path, f_eval, theta=[90.0],
                                       phi=list(phi_xy), center=[0, 0, 1e-3])
        plotting.plot_pattern_polar(
            [('XZ-plane (φ = 0°)',  theta_2d, _cdb(res_2d.E_cprh[0][:, 0]), _cdb(res_2d.E_cplh[0][:, 0])),
             ('YZ-plane (φ = 90°)', theta_2d, _cdb(res_2d.E_cprh[0][:, 1]), _cdb(res_2d.E_cplh[0][:, 1])),
             ('XY-plane (θ = 90°)', phi_xy,   _cdb(res_xy.E_cprh[0][0, :]), _cdb(res_xy.E_cplh[0][0, :]))],
            f_eval, D2,
            os.path.join(self._graphs_path, 'pattern_polar.png'))

        # XY-plane (θ=90°, azimuth) RHCP pattern, downsampled, for the on-board KiCad polar
        _xy_rh = _cdb(res_xy.E_cprh[0][0, :])
        self._xy_phi_deg  = [float(a) for a in phi_xy[::5]]
        self._xy_rhcp_dBi = [float(v) for v in _xy_rh[::5]]

        # 3D pattern (authoritative Dmax over the full sphere)
        theta_3d = np.arange(  0.0, 181.0, 2.0)
        phi_3d   = np.arange(  0.0, 360.0, 2.0)
        res_3d   = self._nf2ff.CalcNF2FF(
            self._sim_path, f_eval, theta_3d, phi_3d,
            center=[0, 0, 1e-3])
        E_3d  = res_3d.E_norm[0]
        self._Dmax = float(directivity_dbi(res_3d.Dmax[0]))   # authoritative peak directivity (dBi)
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
            f_eval, self._Dmax,
            os.path.join(self._graphs_path, 'farfield_3d.png'))

    def _coverage_cuts(self):
        """AR and RHCP gain over an elevation cone — the wide-beam coverage read.

        One NF2FF call (θ = 0..90°, φ = 0/45/90/135°) at f_res. Per (θ, φ): true
        axial ratio and RHCP partial directivity (referenced to this call's own
        Dmax / peak |E|, which is self-consistent because the broadside peak lies
        inside the grid). The coverage scalars use the WORST AR over φ and the MIN
        RHCP gain over φ at each θ, then the shared metrics helpers — the same
        helpers (and worst-over-φ convention) the optimiser worker selects on.
        """
        print('Computing coverage cuts (AR / gain vs elevation)...')
        # At the OPERATING frequency f_target (the optimiser selected here), not f_res.
        th = np.arange(0.0, 90.1, 2.0)
        ph = np.array([0.0, 45.0, 90.0, 135.0])
        res = self._nf2ff.CalcNF2FF(
            self._sim_path, config.f_target, theta=th, phi=list(ph),
            center=[0, 0, 1e-3],
            outfile=os.path.join(self._sim_path, 'nf2ff_cone.h5'))

        Dmax = float(directivity_dbi(res.Dmax[0]))   # peak directivity in dBi (linear→dB)
        E_rh = res.E_cprh[0]               # (n_theta, n_phi) complex
        E_lh = res.E_cplh[0]
        E_no = res.E_norm[0]               # (n_theta, n_phi) real magnitude
        Emax = float(np.max(E_no))

        n_th, n_ph = E_rh.shape
        ar_by_phi   = np.empty((n_th, n_ph))
        gain_by_phi = np.empty((n_th, n_ph))
        for i in range(n_th):
            # AR: the RHCP/LHCP basis is singular exactly on-axis, so use the next
            # ring for θ=0 (matches the optimiser worker's j0=1) — else a spurious
            # on-axis AR can inflate worst_ar_over_cone vs what was selected on.
            i_ar = 1 if (i == 0 and n_th > 1) else i
            for j in range(n_ph):
                ar_by_phi[i, j] = axial_ratio_db(
                    np.array([E_rh[i_ar, j]]), np.array([E_lh[i_ar, j]]))[0]
                gain_by_phi[i, j] = Dmax + 20.0 * np.log10(
                    abs(E_rh[i, j]) / Emax + 1e-12)
        ar_worst   = ar_by_phi.max(axis=1)     # worst azimuth cut
        gain_worst = gain_by_phi.min(axis=1)   # worst azimuth cut

        self._cone_theta    = th
        self._cone_phi      = ph
        self._ar_by_phi     = ar_by_phi
        self._ar_worst      = ar_worst
        self._gain_by_phi   = gain_by_phi
        self._gain_worst    = gain_worst
        self._ar3_bw_deg    = float(ar_beamwidth_deg(th, ar_worst))
        self._worst_ar_cone = float(worst_ar_over_cone(th, ar_worst,
                                                       config.COVER_CONE_DEG))
        self._min_gain_cone = float(min_gain_over_cone(th, gain_worst,
                                                       config.COVER_CONE_DEG))
        g_mean = gain_by_phi.mean(axis=1)
        self._peak_gain_theta = float(th[int(np.argmax(g_mean))])

        print(f'  AR≤3 dB beamwidth: {self._ar3_bw_deg:.0f}°   '
              f'worst AR over {config.COVER_CONE_DEG:.0f}° cone: {self._worst_ar_cone:.1f} dB')
        print(f'  min RHCP gain over cone: {self._min_gain_cone:.1f} dBic   '
              f'(peak gain at θ ≈ {self._peak_gain_theta:.0f}°)')

        plotting.plot_ar_vs_theta(
            th, ar_by_phi, ph, ar_worst, config.f_target,
            os.path.join(self._graphs_path, 'ar_vs_theta.png'),
            ar_max=config.AR_MAX_DB, beamwidth_deg=self._ar3_bw_deg,
            cone_half_deg=config.COVER_CONE_DEG)
        # Overlay the realised-gain curve (directivity × η_tot) when η is trustworthy,
        # so the absolute level — below directivity by the dielectric + mismatch loss —
        # is visible against the gain floor.
        realised_off = (10.0 * np.log10(self._eta_tot)
                        if getattr(self, '_eff_ok', False)
                        and np.isfinite(getattr(self, '_eta_tot', float('nan')))
                        else None)
        plotting.plot_gain_vs_theta(
            th, gain_by_phi, ph, gain_worst, config.f_target,
            os.path.join(self._graphs_path, 'gain_vs_theta.png'),
            gain_floor=config.GAIN_FLOOR_DBIC, cone_half_deg=config.COVER_CONE_DEG,
            realized_offset_dB=realised_off)

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
                fh.write(f'RHCP Patch Far-Field at {config.f_target/1e6:.4f} MHz'
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
            print('  openEMS DumpType=12 may not be supported by this build (needs >= r700)')

    def _opt_trace_plots(self):
        if not self.opt_log:
            return
        plotting.plot_opt_width(
            self.opt_log, config.f_target,
            os.path.join(self._graphs_path, 'opt_width.png'))
        plotting.plot_opt_trace(
            self.opt_log,
            os.path.join(self._graphs_path, 'opt_trace.png'))

    def _write_results_json(self):
        gp_edge = round(self._layout['sub_hw'] * 2.0, 4)   # realised board edge
        s11_at_ft = float(np.interp(config.f_target, self._f_sweep, self._s11_dB))
        self._results = {
            # ── PatchParams fields (KiCad export re-derives the board from these) ──
            **{k: round(float(v), 4) for k, v in self.params.to_dict().items()},
            # ── realised board / fab info ──
            'gp_edge_mm':         gp_edge,
            'substrate_h_mm':     config.substrate_thickness,
            'substrate_epsR':     config.substrate_epsR,
            'substrate_tanD':     config.substrate_tanD,
            'substrate_material': config.substrate_material,
            # ── performance summary ──
            'f_target_MHz':       config.f_target / 1e6,
            'f_res_MHz':          round(self._f_res / 1e6, 4),
            's11_at_ft_dB':       round(s11_at_ft, 2),
            's11_at_res_dB':      round(self._s11_at_res, 2),
            'ar_boresight_dB':    round(self._ar_at_ft, 3),
            'ar_min_dB':          round(self._ar_min, 3),
            'ar_null_MHz':        round(self._f_ar_null / 1e6, 3),
            'ar3_freq_bw_MHz':    round(self._ar_bw / 1e6, 2),
            'rhcp':               bool(self._rhcp_at_ft),
            'ar3_beamwidth_deg':  round(self._ar3_bw_deg, 1),
            'worst_ar_cone_dB':   round(self._worst_ar_cone, 3),
            # NOTE: min_gain_cone_dBic is DIRECTIVITY-referenced (peak-pattern, no η). The
            # link-budget-ready number is min_realised_gain_cone_dBic = that + 10·log10(η_tot)
            # (≈ −5.8 dB on this FR-4 board). Quote the realised value in any budget.
            'min_gain_cone_dBic': round(self._min_gain_cone, 3),
            'min_realised_gain_cone_dBic': (round(self._min_gain_cone + 10.0 * np.log10(self._eta_tot), 3)
                                            if self._eff_ok else None),
            'cover_cone_deg':     config.COVER_CONE_DEG,
            'Dmax_dBi':           round(float(self._Dmax), 3),
            'peak_gain_theta_deg': round(self._peak_gain_theta, 1),
            # ── efficiency & realised gain (dipole-validated NF2FF; see _band_sweep) ──
            # η_rad = Prad/P_acc (excludes mismatch), η_tot = Prad/P_inc (includes it),
            # realised gain = Dmax_dBi + 10·log10(η_tot). null when the sanity gate fails.
            'eta_rad':            (round(self._eta_rad, 4) if self._eff_ok else None),
            'eta_tot':            (round(self._eta_tot, 4) if self._eff_ok else None),
            'realised_gain_dBic': (round(self._realised_gain_dBi, 3) if self._eff_ok else None),
            # XY-plane (azimuth) RHCP pattern for the KiCad board polar
            'xy_phi_deg':         [round(a, 1) for a in getattr(self, '_xy_phi_deg', [])],
            'xy_rhcp_dBi':        [round(v, 2) for v in getattr(self, '_xy_rhcp_dBi', [])],
        }
        path = os.path.join(self._run_dir, 'results.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._results, f, indent=2)
        print(f'Results JSON  : {path}')
        print(f'  → run: python -m src.kicad_export "{path}"')

    def _summary_sheet(self):
        """One-glance datasheet table of the headline parameters (summary_sheet.png)."""
        r = self._results
        def _g(k, fmt='{}', dflt='—'):
            v = r.get(k)
            return dflt if v is None or (isinstance(v, float) and np.isnan(v)) else fmt.format(v)
        rows = [
            ['Operating frequency',          f"{r['f_target_MHz']:.3f} MHz"],
            ['CP centre / resonance',        f"{r['f_res_MHz']:.2f} MHz  ({r['s11_at_res_dB']:.1f} dB)"],
            ['Return loss @ f0',             f"{r['s11_at_ft_dB']:.1f} dB"],
            ['Polarisation',                 f"{'RHCP' if r['rhcp'] else 'LHCP'}  (axial ratio {r['ar_boresight_dB']:.2f} dB)"],
            ['AR ≤ 3 dB beamwidth',     f"{r['ar3_beamwidth_deg']:.0f}°"],
            ['Worst AR over ±45° cone', f"{r['worst_ar_cone_dB']:.1f} dB"],
            ['Peak directivity',             f"{r['Dmax_dBi']:.1f} dBi"],
            ['Realised gain (×η)',
                (f"{r['realised_gain_dBic']:.1f} dBic   "
                 f"(η_rad {r['eta_rad']*100:.0f}%, η_tot {r['eta_tot']*100:.0f}%)"
                 if r.get('realised_gain_dBic') is not None
                 else 'efficiency unavailable (NF2FF/port sanity gate failed)')],
            ['Min RHCP gain over cone',
                (f"{r['min_realised_gain_cone_dBic']:.1f} dBic realised  "
                 f"({r['min_gain_cone_dBic']:.1f} directivity)"
                 if r.get('min_realised_gain_cone_dBic') is not None
                 else f"{r['min_gain_cone_dBic']:.1f} dBic (directivity)")],
            ['Substrate',                    f"{r['substrate_material']}  εr {r['substrate_epsR']}  {r['substrate_h_mm']} mm"],
            ['Board (ground plane)',         f"{r['gp_edge_mm']:.0f} × {r['gp_edge_mm']:.0f} mm"],
            ['Patch / corner truncation',    f"{r['W_mm']:.1f} mm sq / {r['trunc_mm']:.1f} mm chamfer"],
        ]
        plotting.plot_summary_sheet(
            rows, f"RHCP Single-Feed Patch — {r['f_target_MHz']:.3f} MHz",
            os.path.join(self._graphs_path, 'summary_sheet.png'),
            footnote='Directivity is the pattern peak; realised gain = directivity × η_tot '
                     '(η dipole-validated). In-sim loss = FR-4 dielectric + mismatch '
                     '(copper is modelled as PEC). openEMS (FDTD).')

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
    RenameSource('Far-field {config.f_target/1e6:.3f} MHz', ff)
    Show(ff)
    dp = GetDisplayProperties(ff)
    ColorBy(dp, ('POINTS', 'Directivity_dBi'))
    dp.SetScalarBarVisibility(GetActiveViewOrCreate('RenderView'), True)
    GetActiveViewOrCreate('RenderView').ResetCamera()
    Render()
    print('Loaded far-field pattern.')
else:
    print('farfield_rhcp.vtk not found.')

# ── 2. Surface current animation (phase sequence) ────────────────────────────
_j_dir   = os.path.join(_HERE, 'J_patch_surf')
_j_files = sorted(glob.glob(os.path.join(_j_dir, '*_p=*.vtr')))
if _j_files:
    j_src = XMLRectilinearGridReader(FileNames=_j_files)
    RenameSource('J-field surface (phase anim)', j_src)
    j_src.UpdatePipeline()
    Show(j_src)
    scene = GetAnimationScene()
    scene.NumberOfFrames = len(_j_files)
    scene.PlayMode = 'Sequence'
    print(f'Loaded J-field animation: {{len(_j_files)}} frames.')
else:
    print('J_patch_surf not found — export_vtk_surf may be False.')

Render()
print('Done.  Use Animation View (View > Animation View) to play the phase sequence.')
'''

        path = os.path.join(self._vtk_path, 'load_in_paraview.py')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(script)
        print(f'ParaView script  : {path}')

    def _print_summary(self):
        p = self.params
        s11_at_ft = float(np.interp(config.f_target, self._f_sweep, self._s11_dB))
        sense = 'RHCP' if self._rhcp_at_ft else 'LHCP  (FLIP truncation diagonal — wrong sense!)'
        print(f"""
{'═'*60}
  SINGLE-FEED CORNER-TRUNCATED RHCP PATCH — {config.f_target/1e6:.3f} MHz
{'═'*60}
  Substrate  : {config.substrate_material}  εr={config.substrate_epsR}  tanδ={config.substrate_tanD}  h={config.substrate_thickness} mm
  Patch side : {p.W_mm:.2f} mm (near-square)
  Truncation : {p.trunc_mm:.2f} mm chamfer on two diagonal corners  ({self._layout['diag']})
  Feed inset : {p.inset_y_mm:.2f} mm  (single inset, −y edge centre)
  Board      : {self._layout['sub_hw']*2:.1f} × {self._layout['sub_hw']*2:.1f} mm  (realised; param sub_hw → {p.sub_hw_mm*2:.0f} mm)
  S11 @ f0   : {s11_at_ft:.1f} dB
  f_CP_centre: {self._f_res/1e6:.2f} MHz  (offset {(self._f_res-config.f_target)/1e6:+.2f} MHz){f'  [modes: {self._f_mode1/1e6:.1f} / {self._f_mode2/1e6:.1f} MHz  split {self._mode_split/1e6:.1f} MHz]' if self._mode_split > 5e6 else ''}
  AR @ f0    : {self._ar_at_ft:.2f} dB  ({sense})  [null {self._f_ar_null/1e6:.2f} MHz ({(self._f_ar_null-config.f_target)/1e6:+.1f}), AR_min {self._ar_min:.2f} dB, AR≤3 BW ≈ {self._ar_bw/1e6:.1f} MHz]
  Coverage   : AR≤3 dB beam {self._ar3_bw_deg:.0f}°   worst AR / {config.COVER_CONE_DEG:.0f}° cone {self._worst_ar_cone:.1f} dB
             : min RHCP gain / cone {self._min_gain_cone:.1f} dBic directivity{f' = {self._min_gain_cone + 10.0*np.log10(self._eta_tot):.1f} dBic realised' if getattr(self, '_eff_ok', False) else ''}   (peak gain θ≈{self._peak_gain_theta:.0f}°)
  Dmax       : {self._Dmax:.1f} dBi  @ {config.f_target/1e6:.2f} MHz
  Efficiency : {f'η_rad {self._eta_rad*100:.1f}%   η_tot {self._eta_tot*100:.1f}%   realised gain {self._realised_gain_dBi:.1f} dBic' if getattr(self, '_eff_ok', False) else 'unavailable (NF2FF/port sanity gate failed)'}
  Sim data   : {self._sim_path}
  Graphs     : {self._graphs_path}
  ParaView   : {self._vtk_path}
{'═'*60}""")

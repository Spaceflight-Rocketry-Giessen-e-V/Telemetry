# -*- coding: utf-8 -*-
"""All matplotlib figure creation and saving.  No FDTD / NF2FF calls here.

Figure set (datasheet-style characterisation of the dual-feed RHCP patch):

  Frequency domain (radio-facing):
    return_loss.png        S11 vs f, with the -10 dB match band shaded
    vswr.png               VSWR vs f
    smith.png              S11 locus on a 50 Ω Smith chart
    input_impedance.png    de-embedded Zin = 50·(1+Γ)/(1-Γ)  (R + jX)
    axial_ratio.png        boresight AR vs f, AR<=3 dB band
    directivity_vs_freq.png  directivity / realised gain / radiation+total efficiency vs f
    ar_beamwidth_vs_freq.png  AR<=3 dB elevation beamwidth + boresight AR vs f

  Spatial (the pattern):
    ar_vs_theta.png        AR vs elevation, per-φ cuts + worst-over-φ
    gain_vs_theta.png      RHCP directivity vs elevation, per-φ + min-over-φ
    pattern_polar.png      polar XZ/YZ cuts, RHCP co-pol + LHCP cross-pol
    farfield_2d.png        cartesian XZ/YZ directivity cuts, full sphere
    farfield_3d.png        3D directivity pattern

  Summary:
    summary_sheet.png      key-parameter table (one-glance datasheet block)

NOTE on "gain": the per-angle pattern plots show DIRECTIVITY (pattern shape, in dBi =
10·log10(openEMS Dmax)). Realised gain (directivity × total efficiency η_tot, i.e. incl.
FR-4 dielectric + isolated-port-resistor + mismatch loss; copper is PEC in-sim) is
reported in directivity_vs_freq.png, gain_vs_theta.png and summary_sheet.png — for the
branch-line-coupler feed it is many dB below directivity (the coupler dumps the patch
mismatch into the isolated-port resistor), so the two are kept distinct.
"""

import matplotlib
matplotlib.use('Agg')                       # headless / background-safe
import matplotlib.pyplot as plt
import numpy as np

# Thin target-frequency marker used on every 2D frequency-domain plot
_TARGET_LINE = dict(color='#888888', linestyle='--', linewidth=0.6, alpha=0.55)


def _save(fig, out_path):
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# Frequency-domain plots
# ══════════════════════════════════════════════════════════════════════════════

def plot_s11(f_sweep, s11_dB, f_target, f_res, s11_at_res,
             title_note, out_path, f_mode1=None, f_mode2=None):
    """Return loss (S11) vs frequency, with the -10 dB match band shaded."""
    fig, ax = plt.subplots()
    ax.plot(f_sweep / 1e6, s11_dB, 'k-', linewidth=2, label='$S_{11}$')

    # shade the contiguous -10 dB band around the target
    below = s11_dB < -10.0
    if below.any():
        fb = f_sweep[below] / 1e6
        ax.axvspan(fb.min(), fb.max(), color='green', alpha=0.07,
                   label=f'-10 dB band ({fb.max() - fb.min():.0f} MHz)')

    ax.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    ax.axvline(x=f_res / 1e6, color='b', linestyle='-', linewidth=1.5,
               label=f'CP centre {f_res/1e6:.2f} MHz  ({s11_at_res:.1f} dB)')
    if f_mode1 and f_mode2 and abs(f_mode2 - f_mode1) > 5e6:
        for fm, lab in ((f_mode1, 'Mode 1'), (f_mode2, 'Mode 2')):
            ax.axvline(x=fm / 1e6, color='steelblue', linestyle=':', linewidth=0.9,
                       label=f'{lab}  {fm/1e6:.1f} MHz')
    ax.axhline(y=-10, color='gray', linestyle=':', linewidth=1, label='-10 dB')
    ax.grid(True); ax.legend(loc='upper right', fontsize='small')
    ax.set_ylabel('Return loss $S_{11}$ (dB)'); ax.set_xlabel('Frequency (MHz)')
    ax.set_title(f'Return Loss — target {f_target/1e6:.3f} MHz  '
                 f'CP centre {f_res/1e6:.2f} MHz  ({title_note})')
    _save(fig, out_path)


def plot_vswr(f_sweep, gamma_mag, f_target, out_path):
    """VSWR = (1+|Γ|)/(1-|Γ|) vs frequency."""
    vswr = (1.0 + gamma_mag) / np.maximum(1.0 - gamma_mag, 1e-6)
    fig, ax = plt.subplots()
    ax.plot(f_sweep / 1e6, vswr, 'k-', linewidth=2, label='VSWR')
    for v, c in ((2.0, 'green'), (1.5, '0.6')):
        ax.axhline(y=v, color=c, linestyle='--', linewidth=1, label=f'VSWR {v:g} : 1')
    ax.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    v_ft = float(np.interp(f_target, f_sweep, vswr))
    ax.plot(f_target / 1e6, v_ft, 'ro', label=f'{v_ft:.2f} : 1 @ target')
    ax.set_ylim(1, min(10, np.nanmax(vswr) * 1.1))
    ax.grid(True); ax.legend(loc='upper right', fontsize='small')
    ax.set_ylabel('VSWR'); ax.set_xlabel('Frequency (MHz)')
    ax.set_title('Voltage Standing Wave Ratio (50 Ω)')
    _save(fig, out_path)


def _draw_smith_grid(ax):
    """Draw a light 50 Ω Smith-chart grid (constant-R circles, constant-X arcs)."""
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), 'k-', linewidth=1.2)           # |Γ|=1 boundary
    ax.plot([-1, 1], [0, 0], 'k-', linewidth=0.6)                  # real axis
    clip = plt.Circle((0, 0), 1.0, transform=ax.transData)
    for R in (0.2, 0.5, 1.0, 2.0, 5.0):                            # constant resistance
        c = plt.Circle((R / (R + 1.0), 0.0), 1.0 / (R + 1.0),
                       fill=False, color='0.75', linewidth=0.6)
        ax.add_patch(c); c.set_clip_path(clip)
    for X in (0.2, 0.5, 1.0, 2.0, 5.0):                            # constant reactance
        for s in (+1.0, -1.0):
            c = plt.Circle((1.0, s / X), 1.0 / X,
                           fill=False, color='0.85', linewidth=0.5)
            ax.add_patch(c); c.set_clip_path(clip)


def plot_smith(gamma, f_sweep, f_target, f_lo, f_hi, out_path):
    """S11 reflection locus on a 50 Ω Smith chart, coloured by frequency.

    Only the in-band slice [f_lo, f_hi] is drawn (the full ±fc span loops the whole
    chart and hides the operating behaviour).
    """
    sel = (f_sweep >= f_lo) & (f_sweep <= f_hi)
    g, fs = gamma[sel], f_sweep[sel]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
    _draw_smith_grid(ax)
    sc = ax.scatter(g.real, g.imag, c=fs / 1e6, cmap='viridis', s=10, zorder=4)
    g_ft = (np.interp(f_target, f_sweep, gamma.real)
            + 1j * np.interp(f_target, f_sweep, gamma.imag))
    ax.plot(g_ft.real, g_ft.imag, 'r*', markersize=18, zorder=5,
            label=f'{f_target/1e6:.1f} MHz')
    ax.plot(0, 0, 'k+', markersize=10)                            # 50 Ω centre
    cb = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label('Frequency (MHz)')
    ax.legend(loc='upper left', fontsize='small')
    ax.set_title(f'Smith Chart (50 Ω) — {f_lo/1e6:.0f}–{f_hi/1e6:.0f} MHz')
    _save(fig, out_path)


def plot_impedance(f_sweep, Zin_real, Zin_imag, f_target, out_path):
    """De-embedded input impedance Zin = 50·(1+Γ)/(1-Γ) (the match-consistent view)."""
    fig, ax = plt.subplots()
    ax.plot(f_sweep / 1e6, Zin_real, 'k-',  linewidth=2, label=r'$\Re\{Z_{in}\}$')
    ax.plot(f_sweep / 1e6, Zin_imag, 'r--', linewidth=2, label=r'$\Im\{Z_{in}\}$')
    ax.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    ax.axhline(y=50, color='gray', linestyle=':', linewidth=0.8, label='50 Ω')
    ax.axhline(y=0,  color='gray', linestyle='-', linewidth=0.4)
    r_ft = float(np.interp(f_target, f_sweep, Zin_real))
    x_ft = float(np.interp(f_target, f_sweep, Zin_imag))
    ax.plot(f_target / 1e6, r_ft, 'ko'); ax.plot(f_target / 1e6, x_ft, 'rs')
    ax.grid(True); ax.legend(loc='best', fontsize='small')
    ax.set_ylabel('Zin (Ω)'); ax.set_xlabel('Frequency (MHz)')
    ax.set_title(f'Input Impedance (50 Ω-referred) — '
                 f'{r_ft:.0f} {x_ft:+.0f}j Ω @ target')
    _save(fig, out_path)


def plot_axial_ratio(f_ar, ar_vs_f, ar_vs_f_raw, f_target, out_path, rhcp=True):
    """Boresight axial ratio vs frequency: ≥0, 0 dB = perfect circular, ≤3 dB usable."""
    fig, ax = plt.subplots()
    ax.plot(f_ar / 1e6, ar_vs_f, 'b-', linewidth=2, label='Axial Ratio (smoothed)')
    ax.plot(f_ar / 1e6, ar_vs_f_raw, 'b-', linewidth=0.5, alpha=0.3, label='Raw AR')
    ax.fill_between(f_ar / 1e6, 0, 3, alpha=0.08, color='green', label='AR ≤ 3 dB band')
    ax.axhline(y=3, color='r', linestyle='--', linewidth=1, label='3 dB CP limit')
    ax.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    below = ar_vs_f <= 3.0
    if below.any():
        fb = f_ar[below] / 1e6
        ax.annotate(f'AR≤3 dB ≈ {fb.max()-fb.min():.0f} MHz',
                    xy=(f_target/1e6, 0.4), ha='center', fontsize='small', color='green')
    ax.set_ylim(bottom=0); ax.grid(True); ax.legend(loc='upper right', fontsize='small')
    ax.set_ylabel('Axial Ratio (dB)   [0 = perfect circular]')
    ax.set_xlabel('Frequency (MHz)')
    ax.set_title(f'Boresight Axial Ratio — {"RHCP" if rhcp else "LHCP"}-dominant Patch')
    _save(fig, out_path)


def plot_gain_vs_freq(f, directivity_dBi, rhcp_boresight_dBic, f_target, out_path,
                      realised_gain_dBi=None, eta_rad=None, eta_tot=None):
    """Peak directivity, boresight RHCP directivity, and (if given) realised gain vs f.

    Directivity (dBi = 10·log10(openEMS Dmax)) is normalisation-independent. When the
    dipole-validated efficiency is trustworthy, the realised-gain curve (directivity +
    10·log10(η_tot)) and the radiation/total efficiency (right axis, %) are overlaid so
    the absolute level — far below directivity when a branch-line coupler dumps the
    patch mismatch into the isolated-port resistor — is visible. If η is unavailable
    (sanity gate failed) only the directivity curves are drawn.
    """
    fig, ax = plt.subplots()
    ax.plot(f / 1e6, directivity_dBi, 'k-', linewidth=2, label='Peak directivity (dBi)')
    ax.plot(f / 1e6, rhcp_boresight_dBic, 'b-', linewidth=2,
            label='Boresight RHCP directivity (dBic)')
    d_ft = float(np.interp(f_target, f, directivity_dBi))
    ax.plot(f_target / 1e6, d_ft, 'ko', label=f'{d_ft:.1f} dBi @ target')
    if realised_gain_dBi is not None:
        ax.plot(f / 1e6, realised_gain_dBi, color='purple', linestyle='-.', linewidth=2,
                label='Realised gain (×η_tot, dBic)')
        g_ft = float(np.interp(f_target, f, realised_gain_dBi))
        ax.plot(f_target / 1e6, g_ft, 'o', color='purple', label=f'{g_ft:.1f} dBic @ target')
    ax.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    ax.grid(True)
    ax.set_xlabel('Frequency (MHz)'); ax.set_ylabel('Directivity / realised gain (dB)')

    if eta_rad is not None or eta_tot is not None:
        axR = ax.twinx()
        if eta_rad is not None:
            axR.plot(f / 1e6, np.asarray(eta_rad) * 100.0, color='green',
                     linestyle=':', linewidth=1.6, label='η_rad (%)')
        if eta_tot is not None:
            axR.plot(f / 1e6, np.asarray(eta_tot) * 100.0, color='darkorange',
                     linestyle=':', linewidth=1.6, label='η_tot (%)')
        axR.set_ylabel('Efficiency (%)'); axR.set_ylim(bottom=0)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = axR.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc='best', fontsize='small')
        ax.set_title('Directivity, Realised Gain & Efficiency vs Frequency')
    else:
        ax.legend(loc='best', fontsize='small')
        ax.set_title('Directivity vs Frequency  (efficiency unavailable — see notes)')
    _save(fig, out_path)


def plot_ar_beamwidth_vs_freq(f, ar_bw_deg, ar_boresight_dB, f_target, out_path,
                              cover_cone_deg=45.0):
    """AR≤3 dB elevation beamwidth (left) and boresight AR (right) vs frequency."""
    fig, axL = plt.subplots()
    axR = axL.twinx()
    l1, = axL.plot(f / 1e6, ar_bw_deg, 'b-', linewidth=2.2, label='AR≤3 dB beamwidth (°)')
    l2, = axR.plot(f / 1e6, ar_boresight_dB, 'r--', linewidth=1.5, label='boresight AR (dB)')
    axL.axhline(y=2 * cover_cone_deg, color='gray', linestyle=':', linewidth=0.9,
                label=f'full {cover_cone_deg:.0f}° cone ({2*cover_cone_deg:.0f}°)')
    axR.axhline(y=3, color='r', linestyle=':', linewidth=0.8)
    axL.axvline(x=f_target / 1e6, **_TARGET_LINE)
    bw_ft = float(np.interp(f_target, f, ar_bw_deg))
    axL.plot(f_target / 1e6, bw_ft, 'bo', label=f'{bw_ft:.0f}° @ target')
    axL.set_xlabel('Frequency (MHz)')
    axL.set_ylabel('AR ≤ 3 dB beamwidth (deg)'); axL.set_ylim(bottom=0)
    axR.set_ylabel('Boresight AR (dB)'); axR.set_ylim(bottom=0)
    axL.grid(True)
    axL.legend(handles=[l1, l2], loc='upper right', fontsize='small')
    axL.set_title('Coverage vs Frequency — AR≤3 dB beamwidth & boresight AR')
    _save(fig, out_path)


# ══════════════════════════════════════════════════════════════════════════════
# Spatial (pattern) plots
# ══════════════════════════════════════════════════════════════════════════════

def plot_ar_vs_theta(theta_deg, ar_by_phi, phi_deg, ar_worst, f_res, out_path,
                     ar_max=3.0, beamwidth_deg=None, cone_half_deg=45.0):
    """AR vs elevation θ: one line per φ cut + the worst-over-φ envelope."""
    fig, ax = plt.subplots()
    for j, phi in enumerate(phi_deg):
        ax.plot(theta_deg, ar_by_phi[:, j], linewidth=0.9, alpha=0.55, label=f'φ = {phi:.0f}°')
    ax.plot(theta_deg, ar_worst, 'b-', linewidth=2.2, label='worst over φ')
    ax.fill_between(theta_deg, 0, ar_max, alpha=0.08, color='green', label=f'AR ≤ {ar_max:.0f} dB')
    ax.axhline(y=ar_max, color='r', linestyle='--', linewidth=1, label=f'{ar_max:.0f} dB CP limit')
    ax.axvline(x=cone_half_deg, color='#888888', linestyle=':', linewidth=0.8,
               label=f'{cone_half_deg:.0f}° cone edge')
    if beamwidth_deg:
        edge = beamwidth_deg / 2.0
        ax.axvline(x=edge, color='gold', linestyle='-', linewidth=1.3,
                   label=f'AR≤{ar_max:.0f} edge {edge:.0f}° (BW {beamwidth_deg:.0f}°)')
    ax.set_ylim(bottom=0); ax.grid(True); ax.legend(loc='upper left', fontsize='small')
    ax.set_ylabel('Axial Ratio (dB)   [0 = perfect circular]')
    ax.set_xlabel('Elevation θ from boresight (deg)')
    ax.set_title(f'Axial Ratio vs Elevation — {f_res/1e6:.3f} MHz')
    _save(fig, out_path)


def plot_gain_vs_theta(theta_deg, gain_by_phi, phi_deg, gain_worst, f_res, out_path,
                       gain_floor=2.0, cone_half_deg=45.0, realized_offset_dB=None):
    """RHCP directivity (dBic) vs elevation θ: per-φ cuts + the min-over-φ envelope.

    If realized_offset_dB is given (= 10·log10 total-efficiency), a faint realised-gain
    curve (directivity + offset) is overlaid so the absolute level is visible too.
    """
    fig, ax = plt.subplots()
    for j, phi in enumerate(phi_deg):
        ax.plot(theta_deg, gain_by_phi[:, j], linewidth=0.9, alpha=0.55, label=f'φ = {phi:.0f}°')
    ax.plot(theta_deg, gain_worst, 'k-', linewidth=2.2, label='directivity, min over φ')
    if realized_offset_dB is not None:
        ax.plot(theta_deg, gain_worst + realized_offset_dB, color='purple',
                linestyle='-.', linewidth=1.6,
                label=f'realised gain (×η, {realized_offset_dB:+.1f} dB)')
    ax.axhline(y=gain_floor, color='r', linestyle='--', linewidth=1,
               label=f'gain floor {gain_floor:.1f} dBic')
    ax.axvline(x=cone_half_deg, color='#888888', linestyle=':', linewidth=0.8,
               label=f'{cone_half_deg:.0f}° cone edge')
    ax.grid(True); ax.legend(loc='lower left', fontsize='small')
    ax.set_ylabel('RHCP directivity / gain (dBic)')
    ax.set_xlabel('Elevation θ from boresight (deg)')
    ax.set_title(f'RHCP Gain vs Elevation — {f_res/1e6:.3f} MHz')
    _save(fig, out_path)


def plot_pattern_polar(cuts, f_res, dmax, out_path, floor_dBi=-25.0):
    """Polar co/cross-pol patterns: RHCP (co-pol) + LHCP (cross-pol), one subplot per cut.

    `cuts` = list of (name, angle_deg, rhcp_dBi, lhcp_dBi) so each cut carries its own
    polar angle — θ for the XZ/YZ elevation cuts (0 = boresight, top), φ for the XY
    azimuth cut. Floor clamps the radial axis so pattern nulls don't blow up.
    """
    n = len(cuts)
    fig, axes = plt.subplots(1, n, figsize=(5.6 * n, 6.0),
                             subplot_kw={'projection': 'polar'})
    if n == 1:
        axes = [axes]
    r_top = float(np.ceil(max(dmax, 0.0) + 1.0))
    for ax, (name, ang, rhcp, lhcp) in zip(axes, cuts):
        t = np.deg2rad(ang)
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.plot(t, np.clip(rhcp, floor_dBi, None), 'b-',  linewidth=2.0, label='RHCP (co)')
        ax.plot(t, np.clip(lhcp, floor_dBi, None), 'r--', linewidth=1.4, label='LHCP (cross)')
        ax.set_ylim(floor_dBi, r_top)
        ax.set_rlabel_position(135)
        ax.set_title(name, pad=14)
        ax.grid(True, alpha=0.4)
    axes[0].legend(loc='lower left', bbox_to_anchor=(-0.1, -0.12), fontsize='small')
    fig.suptitle(f'Radiation Pattern (directivity, dBi) — {f_res/1e6:.3f} MHz  '
                 f'(Dmax {dmax:.1f} dBi)', fontsize=12)
    _save(fig, out_path)


def plot_farfield_2d(theta_deg, dir_xz, dir_yz, f_res, Dmax, out_path):
    """Cartesian XZ / YZ directivity cuts over the full sphere (−180..180°)."""
    fig, ax = plt.subplots()
    ax.plot(theta_deg, dir_xz, 'k-',  linewidth=2, label='XZ-plane (φ = 0°)')
    ax.plot(theta_deg, dir_yz, 'r--', linewidth=2, label='YZ-plane (φ = 90°)')
    ax.axvline(x=0, color='#888888', linestyle='--', linewidth=0.6, alpha=0.55,
               label='Boresight (θ = 0°)')
    ax.axhline(y=Dmax - 3, color='#888888', linestyle=':', linewidth=0.6, alpha=0.55,
               label=f'−3 dB ({Dmax-3:.1f} dBi)')
    # front-to-back: boresight vs ±180
    fb = Dmax - float(np.interp(180.0, theta_deg, dir_xz, period=360))
    ax.grid(True); ax.legend(loc='lower center', fontsize='small')
    ax.set_ylabel('Directivity (dBi)'); ax.set_xlabel('Theta (deg)')
    ax.set_title(f'Far-field cuts — {f_res/1e6:.3f} MHz  '
                 f'(Dmax {Dmax:.1f} dBi, F/B ≈ {fb:.0f} dB)')
    _save(fig, out_path)


def plot_farfield_3d(X, Y, Z, E_lin, E_dBi, f_res, Dmax, out_path):
    """3D directivity pattern surface, coloured by dBi."""
    fig3d = plt.figure(figsize=(9, 8))
    ax3d  = fig3d.add_subplot(111, projection='3d')
    ax3d.plot_surface(X, Y, Z, facecolors=plt.cm.jet(E_lin),
                      rstride=1, cstride=1, linewidth=0, antialiased=True, alpha=0.95)
    m = plt.cm.ScalarMappable(cmap='jet'); m.set_array(E_dBi)
    cb = fig3d.colorbar(m, ax=ax3d, shrink=0.55, pad=0.08); cb.set_label('Directivity (dBi)')
    ax3d.set_title(f'3D RHCP Radiation Pattern — {f_res/1e6:.3f} MHz   (Dmax {Dmax:.1f} dBi)')
    ax3d.set_xlabel('X'); ax3d.set_ylabel('Y'); ax3d.set_zlabel('Z (boresight)')
    ax3d.set_box_aspect([1, 1, 1]); ax3d.view_init(elev=22, azim=-60)
    _save(fig3d, out_path)


# ══════════════════════════════════════════════════════════════════════════════
# Summary sheet
# ══════════════════════════════════════════════════════════════════════════════

def plot_summary_sheet(rows, title, out_path, footnote=None):
    """Render a key-parameter table as a one-glance datasheet block.

    `rows` = list of (parameter, value) string pairs.
    """
    fig, ax = plt.subplots(figsize=(10.0, 0.42 * len(rows) + 1.4))
    ax.axis('off')
    tbl = ax.table(cellText=rows, colLabels=['Parameter', 'Value'],
                   colWidths=[0.40, 0.60], cellLoc='left', loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.4)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('0.8')
        if r == 0:
            cell.set_facecolor('#27408b'); cell.set_text_props(color='w', weight='bold')
        elif r % 2:
            cell.set_facecolor('#f2f4f8')
    ax.set_title(title, fontsize=13, weight='bold', pad=12)
    if footnote:
        ax.annotate(footnote, xy=(0.5, -0.02), xycoords='axes fraction',
                    ha='center', va='top', fontsize=8, color='0.4')
    _save(fig, out_path)


# ══════════════════════════════════════════════════════════════════════════════
# Optimisation traces (only emitted during an optimisation run; not part of the
# single-sim datasheet set). PatchParams log schema.
# ══════════════════════════════════════════════════════════════════════════════

_PHASE_CFG = {
    'GRID': ('steelblue', 'GRID screen (W×arm, coarse NrTS)'),
    'CONF': ('crimson',   'CONFIRM (full NrTS)'),
    'W':  ('purple',     'Phase W — width (resonance)'),
    'I':  ('darkorange', 'Phase I — inset (match)'),
    'C':  ('darkgreen',  'Phase C — coupler arm (AR)'),
    'W2': ('navy',       'Phase W2 — width re-tune'),
    'GP': ('crimson',    'Phase GP — ground plane (beam)'),
}


def plot_opt_width(opt_log, f_target, out_path):
    """f_res vs patch side W, one line per coupler-arm value (the 2-D grid)."""
    pts = [x for x in opt_log
           if x.get('ok', True) and x['phase'] in ('GRID', 'CONF', 'W', 'W2')]
    if not pts:
        return
    fig, ax = plt.subplots()
    arms = sorted({round(x['p'].cpl_arm_mm, 2) for x in pts})
    for arm in arms:
        sub = sorted((x for x in pts if round(x['p'].cpl_arm_mm, 2) == arm),
                     key=lambda x: x['p'].W_mm)
        ax.plot([x['p'].W_mm for x in sub], [x['f_res'] / 1e6 for x in sub],
                'o-', label=f'coupler arm {arm:.1f} mm')
    best = min(pts, key=lambda x: abs(x['f_res'] - f_target))
    ax.axhline(y=f_target / 1e6, label=f'Target {f_target/1e6:.3f} MHz', **_TARGET_LINE)
    ax.scatter([best['p'].W_mm], [best['f_res'] / 1e6],
               color='gold', s=120, zorder=5, label='Closest to target')
    ax.set_xlabel('Patch side W (mm)'); ax.set_ylabel('Resonant frequency (MHz)')
    ax.set_title('Optimisation — Resonance vs Patch Size (per coupler arm)')
    ax.legend(loc='best', fontsize='small'); ax.grid(True)
    _save(fig, out_path)


def plot_opt_trace(opt_log, out_path):
    """Boresight AR (left axis) and AR≤3 dB beamwidth (right axis) per opt run."""
    if not opt_log:
        return
    fig, axL = plt.subplots()
    axR = axL.twinx()
    for i, x in enumerate(opt_log):
        col = _PHASE_CFG.get(x['phase'], ('gray', x['phase']))[0]
        axL.scatter(i, x.get('ar_dB', 99.0), color=col, marker='o', zorder=3)
        axR.scatter(i, x.get('ar_bw_deg', 0.0), color=col, marker='x', zorder=3)
    seen = []
    for x in opt_log:
        if x['phase'] not in seen:
            seen.append(x['phase'])
    handles = [plt.Line2D([], [], color=_PHASE_CFG.get(ph, ('gray', ph))[0],
                          marker='o', linestyle='',
                          label=_PHASE_CFG.get(ph, ('gray', ph))[1]) for ph in seen]
    axL.axhline(y=3, color='r', linestyle='--', linewidth=1)
    axL.set_ylim(bottom=0); axL.set_xlabel('Optimisation run #')
    axL.set_ylabel('Boresight AR (dB)  [● , 3 dB limit]')
    axR.set_ylabel('AR ≤ 3 dB beamwidth (deg)  [×]')
    axL.set_title('Optimisation Trace — AR & beamwidth per run')
    axL.legend(handles=handles, loc='best', fontsize='small'); axL.grid(True)
    _save(fig, out_path)

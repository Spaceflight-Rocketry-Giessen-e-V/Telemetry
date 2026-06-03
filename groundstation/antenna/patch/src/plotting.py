# -*- coding: utf-8 -*-
"""All matplotlib figure creation and saving.  No FDTD / NF2FF calls here."""

import matplotlib.pyplot as plt
import numpy as np

# Thin target-frequency marker used on every 2D frequency-domain plot
_TARGET_LINE = dict(color='#888888', linestyle='--', linewidth=0.6, alpha=0.55)


def plot_s11(f_sweep, s11_dB, f_target, f_res, s11_at_res,
             opt_W, opt_delta, out_path,
             f_mode1=None, f_mode2=None):
    plt.figure()
    plt.plot(f_sweep / 1e6, s11_dB, 'k-', linewidth=2, label='$S_{11}$')
    plt.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.2f} MHz',
                **_TARGET_LINE)
    plt.axvline(x=f_res / 1e6, color='b', linestyle='-', linewidth=1.5,
                label=f'CP centre {f_res/1e6:.2f} MHz  ({s11_at_res:.1f} dB)')
    if f_mode1 and f_mode2 and abs(f_mode2 - f_mode1) > 5e6:
        plt.axvline(x=f_mode1 / 1e6, color='steelblue', linestyle=':', linewidth=0.9,
                    label=f'Mode 1  {f_mode1/1e6:.1f} MHz')
        plt.axvline(x=f_mode2 / 1e6, color='steelblue', linestyle=':', linewidth=0.9,
                    label=f'Mode 2  {f_mode2/1e6:.1f} MHz')
    plt.axhline(y=-10, color='gray', linestyle=':', linewidth=1, label='-10 dB')
    plt.grid()
    plt.legend(loc='upper right', fontsize='small')
    plt.ylabel('S-Parameter (dB)'); plt.xlabel('Frequency (MHz)')
    plt.title(f'RHCP Patch S11 — target {f_target/1e6:.2f} MHz  '
              f'CP centre {f_res/1e6:.2f} MHz  '
              f'(W = {opt_W:.1f} mm  Δ/W = {opt_delta/opt_W:.3f})')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_axial_ratio(f_ar, ar_vs_f, ar_vs_f_raw, f_target, out_path, rhcp=True):
    # True axial ratio: ≥0, 0 dB = perfect circular, ≤3 dB = usable CP band.
    plt.figure()
    plt.plot(f_ar / 1e6, ar_vs_f, 'b-', linewidth=2, label='Axial Ratio (smoothed)')
    plt.plot(f_ar / 1e6, ar_vs_f_raw, 'b-', linewidth=0.5, alpha=0.3, label='Raw AR')
    plt.fill_between(f_ar / 1e6, 0, 3, alpha=0.08, color='green',
                     label='AR ≤ 3 dB band')
    plt.axhline(y=3, color='r', linestyle='--', linewidth=1, label='3 dB CP limit')
    plt.axhline(y=0, color='gray', linestyle=':', linewidth=0.8, label='0 dB (ideal CP)')
    plt.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.2f} MHz',
                **_TARGET_LINE)
    plt.ylim(bottom=0)
    plt.grid()
    plt.legend(loc='best', fontsize='small')
    plt.ylabel('Axial Ratio (dB)   [0 = perfect circular]')
    plt.xlabel('Frequency (MHz)')
    _hand = 'RHCP' if rhcp else 'LHCP'
    plt.title(f'Axial Ratio — {_hand}-dominant Patch {f_target/1e6:.2f} MHz')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_impedance(f_sweep, Zin_real, Zin_imag, f_target, out_path):
    plt.figure()
    plt.plot(f_sweep / 1e6, Zin_real, 'k-',  linewidth=2,
             label=r'$\Re\{Z_{in}\}$')
    plt.plot(f_sweep / 1e6, Zin_imag, 'r--', linewidth=2,
             label=r'$\Im\{Z_{in}\}$')
    plt.axvline(x=f_target / 1e6, label=f'Target {f_target/1e6:.2f} MHz',
                **_TARGET_LINE)
    plt.axhline(y=50, color='gray', linestyle=':', linewidth=0.8, label='50 Ω')
    plt.grid()
    plt.legend(loc='best', fontsize='small')
    plt.ylabel('Zin (Ω)'); plt.xlabel('Frequency (MHz)')
    plt.title('Input Impedance — RHCP Patch')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_farfield_2d(theta_deg, E_norm_2d, f_res, Dmax, out_path):
    plt.figure()
    plt.plot(theta_deg, np.squeeze(E_norm_2d[:, 0]), 'k-',  linewidth=2,
             label='xz-plane (φ = 0°)')
    plt.plot(theta_deg, np.squeeze(E_norm_2d[:, 1]), 'r--', linewidth=2,
             label='yz-plane (φ = 90°)')
    plt.axvline(x=0,   color='#888888', linestyle='--', linewidth=0.6, alpha=0.55,
                label='Boresight (θ = 0°)')
    plt.axhline(y=Dmax - 3, color='#888888', linestyle=':', linewidth=0.6, alpha=0.55,
                label=f'−3 dB ({Dmax-3:.1f} dBi)')
    plt.grid()
    plt.legend(loc='lower center', fontsize='small')
    plt.ylabel('Directivity (dBi)'); plt.xlabel('Theta (deg)')
    plt.title(f'Far-field cuts — {f_res/1e6:.2f} MHz  (Dmax = {Dmax:.1f} dBi)')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_farfield_3d(X, Y, Z, E_lin, E_dBi, f_res, Dmax, out_path):
    fig3d = plt.figure(figsize=(8, 7))
    ax3d  = fig3d.add_subplot(111, projection='3d')
    ax3d.plot_surface(X, Y, Z, facecolors=plt.cm.jet(E_lin),
                      linewidth=0, antialiased=True, alpha=0.9)
    m = plt.cm.ScalarMappable(cmap='jet')
    m.set_array(E_dBi)
    cb = fig3d.colorbar(m, ax=ax3d, shrink=0.5, pad=0.1)
    cb.set_label('Directivity (dBi)')
    ax3d.set_title(f'3D RHCP Radiation Pattern — {f_res/1e6:.2f} MHz\n'
                   f'Dmax = {Dmax:.1f} dBi')
    ax3d.set_xlabel('X'); ax3d.set_ylabel('Y'); ax3d.set_zlabel('Z')
    ax3d.set_box_aspect([1, 1, 1])
    fig3d.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig3d)


def plot_opt_phase0(phase0_log, f_target, opt_W, out_path):
    if not phase0_log:
        return
    best = min(phase0_log, key=lambda x: abs(x['f_res'] - f_target))
    sorted_log = sorted(phase0_log, key=lambda x: x['W'])
    fig, ax = plt.subplots()
    ax.plot([x['W'] for x in sorted_log],
            [x['f_res'] / 1e6 for x in sorted_log],
            'o-', color='purple', label='f_res(W)')
    ax.axhline(y=f_target / 1e6, label=f'Target {f_target/1e6:.2f} MHz',
               **_TARGET_LINE)
    ax.scatter([best['W']], [best['f_res'] / 1e6],
               color='gold', s=120, zorder=5, label='Selected W')
    ax.set_xlabel('Patch side W (mm)')
    ax.set_ylabel('Resonant frequency (MHz)')
    ax.set_title('Phase 0 — Frequency vs Patch Size')
    ax.legend(loc='best', fontsize='small'); ax.grid()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_opt_trace(opt_log, opt_W, out_path):
    fig, ax = plt.subplots()
    phase_cfg = {
        '1': ('navy',       'Phase 1 — coarse Δ sweep'),
        '2': ('darkorange', 'Phase 2 — inset sweep'),
        '3': ('darkgreen',  'Phase 3 — fine Δ sweep'),
    }
    for ph, (col, lbl) in phase_cfg.items():
        pts = [x for x in opt_log if x['phase'] == ph]
        if not pts:
            continue
        ax.scatter([x['dr'] for x in pts],
                   [x['ar_dB'] for x in pts],
                   color=col, label=lbl, zorder=3)
    ax.axhline(y=3, color='r', linestyle='--', linewidth=1, label='3 dB CP limit')
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=1, label='0 dB (ideal CP)')
    ax.set_ylim(bottom=0)
    ax.set_xlabel('Δ/W')
    ax.set_ylabel('Axial Ratio at f_target (dB)')
    ax.set_title('Optimisation Trace — AR vs Truncation Ratio\n'
                 f'(W = {opt_W:.1f} mm,  Phase-0b correction)')
    ax.legend(loc='best', fontsize='small'); ax.grid()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

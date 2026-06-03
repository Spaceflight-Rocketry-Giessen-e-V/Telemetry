# -*- coding: utf-8 -*-
"""
RHCP Patch Antenna — Ground Station for Sounding Rocket
========================================================
Central entry point.  Edit the switches below and run:

    python run.py

All physical constants and derived values live in config.py.
"""

# ═══════════════════════ USER SWITCHES ════════════════════════════
# ── Run mode (pick at most one) ───────────────────────────────────
preview_only    = False  # write XML + open AppCSXCAD, then exit
single_sim_only = False  # one high-fidelity sim at current dims, skip optimisation
post_proc_only  = False  # skip FDTD entirely, re-run post-processing on existing sim_data

# ── Warm-start / dimension source ────────────────────────────────
# Set warm_start to seed the optimisation (or single sim) from known-good dims.
# Leave as None for a cold start from the analytical formula.
warm_start = {
#    'W_mm':       82.9389,
    'W_mm':       84.0,
    'delta_mm':    8.2939,
    'y_inset_mm':  5.8057,
#    'sub_hw_mm':  75.0,   # optional — half-edge of board; default 75 (=150 mm board)
}

# reuse_best: load dims from the most-recent results.json and use them as
# warm_start (overrides the dict above).  Combined with single_sim_only=True
# this reproduces the old "run one final sim at previous best dims" behaviour.
# Combined with single_sim_only=False it re-runs the full optimisation from
# those dims as a warm start.
reuse_best        = True
reuse_results_dir = None  # folder to load results.json from; None = auto-find latest

# ── Output options ────────────────────────────────────────────────
export_kicad    = True  # generate patch_antenna.kicad_pcb after final sim
export_vtk_surf = False   # copy E/J surface-field .vtr files into vtk/ subfolders
                         # (set False to skip ~46 files and save disk space)

# ── Post-processing overrides (only used when post_proc_only=True) ─
# Copy the "Final geometry for PCB" values from a previous run's log.
# Leave as None to fall back to warm_start / analytical dims.
pp_dims = None
# pp_dims = {'W_mm': 84.04, 'delta_mm': 9.61, 'y_inset_mm': 2.44}
# ══════════════════════════════════════════════════════════════════


# ─────────────────────────── implementation ──────────────────────────────
# Only lightweight stdlib is imported at module scope so `import run` works
# without openEMS installed (handy for smoke tests).  The heavy dependencies
# (config, src.*, matplotlib, CSXCAD/openEMS) are imported inside the functions
# that need them, and only when run() actually executes.
import atexit
import datetime as _dt
import os
import subprocess
import sys


def setup_console_and_backend():
    """UTF-8 console on Windows + a display-capable matplotlib backend."""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    # Backend must be selected before any other module imports pyplot.
    import matplotlib
    try:
        matplotlib.use('TkAgg')
    except Exception:
        try:
            matplotlib.use('Qt5Agg')
        except Exception:
            pass


def setup_run_dirs():
    """Create the timestamped run-directory tree.

    sim_data is intentionally NOT pre-created — openEMS.Run() requires it absent.
    Returns (run_dir, sim_path, graphs_path, vtk_path).
    """
    timestamp   = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir     = os.path.join(os.getcwd(), f'RHCP_Patch_{timestamp}')
    sim_path    = os.path.join(run_dir, 'sim_data')
    graphs_path = os.path.join(run_dir, 'graphs')
    vtk_path    = os.path.join(run_dir, 'vtk')
    os.makedirs(graphs_path, exist_ok=True)
    os.makedirs(vtk_path,    exist_ok=True)
    return run_dir, sim_path, graphs_path, vtk_path


def setup_logging(run_dir):
    """Tee stdout to console + simulation.log; return the open log file."""
    from src.model import _Tee
    log_file = open(os.path.join(run_dir, 'simulation.log'),
                    'w', encoding='utf-8', errors='replace')
    atexit.register(log_file.close)
    sys.stdout = _Tee(sys.stdout, log_file)
    return log_file


def resolve_dimensions():
    """Resolve starting geometry: analytical, then warm_start / reuse_best.

    Returns (W_cp, delta_init, y_inset_init, sub_hw_init, ws, reuse_run_dir)
    where ws is the effective warm-start dict (or None) and reuse_run_dir is the
    source run folder when reuse_best loaded a results.json (else None).
    """
    import config
    from src.optimizer import _find_latest_results_json, _load_results_json

    W_cp         = config.W_cp
    delta_init   = W_cp * config._delta_frac
    y_inset_init = W_cp * config._y_inset_frac
    sub_hw_init  = config.SUB_HW_DEFAULT

    ws            = warm_start  # effective warm-start (reuse_best may override)
    reuse_run_dir = None

    if reuse_best:
        rj = reuse_results_dir
        if rj is None:
            rj = _find_latest_results_json()
        elif os.path.isdir(rj):
            cand = os.path.join(rj, 'results.json')
            old  = os.path.join(rj, 'images', 'results.json')
            rj   = cand if os.path.exists(cand) else (old if os.path.exists(old) else None)
        if not rj or not os.path.exists(str(rj)):
            print('\nERROR: reuse_best=True but no results.json found.')
            print('  Set reuse_results_dir to a previous RHCP_Patch_* folder, or leave None.')
            sys.exit(1)
        try:
            rW, rd, ryi, rsh = _load_results_json(rj)
        except Exception as e:
            print(f'\nERROR reading results.json: {e}')
            sys.exit(1)
        ws            = {'W_mm': rW, 'delta_mm': rd, 'y_inset_mm': ryi, 'sub_hw_mm': rsh}
        reuse_run_dir = os.path.dirname(os.path.abspath(str(rj)))
        print(f'\nreuse_best: loaded {rj}')
        print(f'  → using as warm_start  (W={rW:.4f}  Δ={rd:.4f}  '
              f'yi={ryi:.4f}  sub_hw={rsh:.2f} mm)')

    if ws is not None:
        W_cp         = float(ws['W_mm'])
        delta_init   = float(ws['delta_mm'])
        y_inset_init = float(ws['y_inset_mm'])
        sub_hw_init  = float(ws.get('sub_hw_mm', config.SUB_HW_DEFAULT))
        print(f'\nWarm-start dims:')
        print(f'  W = {W_cp:.4f} mm   Δ = {delta_init:.4f} mm   '
              f'yi = {y_inset_init:.4f} mm   sub_hw = {sub_hw_init:.2f} mm')
        if not reuse_best:
            print(f'  Phase 0/1/2 sweep windows tightened around these values.')
    else:
        print(f'\nAnalytical initial dimensions:')
        print(f'  Patch side   W = {W_cp:.1f} mm  (analytical x 0.86 shrink)')
        print(f'  Feed inset  yi = {y_inset_init:.1f} mm')
        print(f'  Truncation   Δ = {delta_init:.1f} mm  (Δ/W = {config._delta_frac:.3f})')
        print(f'  Ground plane = {sub_hw_init*2:.0f} × {sub_hw_init*2:.0f} mm  (Phase 4 will sweep)')

    return W_cp, delta_init, y_inset_init, sub_hw_init, ws, reuse_run_dir


def maybe_preview(run_dir, delta_init, y_inset_init, W_cp, sub_hw_init):
    """Write the initial-geometry XML and open AppCSXCAD.

    Returns True when the caller should exit now (preview_only).
    """
    from src.model import build_sim

    print('\n--- Writing initial geometry for preview ---', flush=True)
    _FDTD_prev, CSX_prev, _, _ = build_sim(delta_init, y_inset_init, W_cp, NrTS=1,
                                           sub_hw_mm=sub_hw_init)
    csx_file = os.path.join(run_dir, 'rhcp_patch_init.xml')
    CSX_prev.Write2XML(csx_file)
    print(f'XML written: {csx_file}', flush=True)

    try:
        from CSXCAD import AppCSXCAD_BIN
        print('Launching AppCSXCAD — close window to continue...', flush=True)
        ret = subprocess.call([AppCSXCAD_BIN, csx_file])
        if ret != 0:
            print(f'AppCSXCAD exited with code {ret} — continuing.', flush=True)
    except Exception as exc:
        print(f'AppCSXCAD not available: {exc}', flush=True)
        print(f'Open manually: {csx_file}', flush=True)
        if preview_only:
            input('Press ENTER to continue...')

    return preview_only


def run_single_sim(sim_path, dims):
    """single_sim_only: one high-fidelity sim at the resolved dims."""
    import config
    from src.model import build_sim
    opt_W, opt_delta, opt_y_inset, opt_sub_hw = dims

    print(f'\n{"="*60}')
    print(f'single_sim_only=True — one high-fidelity sim  (NrTS = {config.NrTS_final})')
    print(f'  W = {opt_W:.2f} mm   Δ = {opt_delta:.2f} mm   '
          f'y_inset = {opt_y_inset:.2f} mm   sub_hw = {opt_sub_hw:.2f} mm')
    print(f'{"="*60}')
    FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
        opt_delta, opt_y_inset, opt_W, config.NrTS_final,
        sub_hw_mm=opt_sub_hw, vtk_dump=export_vtk_surf)
    FDTD_f.Run(sim_path, verbose=1, cleanup=True)
    return opt_W, opt_delta, opt_y_inset, opt_sub_hw, [], port_f, nf2ff_f


def run_optimize(sim_path, W_cp, ws, sub_hw_init):
    """Full six-phase optimisation followed by a final high-fidelity sim."""
    import config
    from src.model import build_sim
    from src.optimizer import Optimizer, n_opt, phases_label, resolve_workers

    par   = resolve_workers()
    n_run = n_opt()
    secs  = (n_run / par * config.NrTS_opt / 40000 * 90
             + config.NrTS_final / 40000 * 90)
    eta   = _dt.datetime.now() + _dt.timedelta(seconds=secs)
    print(f'\n{"="*60}')
    print(f'Starting optimisation  ({n_run} FDTD runs  NrTS = {config.NrTS_opt})')
    print(f'  Phases: {phases_label()}')
    print(f'  Workers: {par}  |  Rough wall-clock estimate: ~{int(secs/60)} min'
          f'  (ETA ~{eta.strftime("%H:%M")})')
    print(f'{"="*60}')
    opt = Optimizer(W_cp, warm_start=ws, sub_hw_init=sub_hw_init)
    opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log = opt.run()

    print('\n--- Final high-fidelity simulation (with VTK field dumps) ---')
    print(f'  W = {opt_W:.2f} mm   Δ = {opt_delta:.2f} mm   '
          f'y_inset = {opt_y_inset:.2f} mm   sub_hw = {opt_sub_hw:.2f} mm   '
          f'NrTS = {config.NrTS_final}')
    FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
        opt_delta, opt_y_inset, opt_W, config.NrTS_final,
        sub_hw_mm=opt_sub_hw, vtk_dump=export_vtk_surf)
    FDTD_f.Run(sim_path, verbose=1, cleanup=True)
    return opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log, port_f, nf2ff_f


def setup_post_proc_only(dims, reuse_run_dir):
    """post_proc_only: rebuild the model (no Run) so post-proc can read sim_data.

    Returns (opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log,
             port_f, nf2ff_f, pp_sim_path).
    """
    import config
    from src.model import build_sim
    W_cp, delta_init, y_inset_init, sub_hw_init = dims

    # Guard: post-proc needs an existing, populated sim_data. The freshly created
    # run's own sim_data is empty, so without a source run there is nothing to
    # read and CalcPort/CalcNF2FF would fail cryptically.
    if reuse_run_dir is None:
        print('\nERROR: post_proc_only=True but no existing sim_data to read.')
        print('  Set reuse_best=True (auto-find latest run), or reuse_results_dir to a')
        print('  previous RHCP_Patch_* folder, or run a simulation first.')
        sys.exit(1)
    pp_sim_path = os.path.join(reuse_run_dir, 'sim_data')
    if not os.path.isdir(pp_sim_path) or not os.listdir(pp_sim_path):
        print(f'\nERROR: post_proc_only source sim_data is missing or empty:\n  {pp_sim_path}')
        sys.exit(1)
    print(f'post_proc_only: reading sim_data from {pp_sim_path}')

    if pp_dims is not None:
        opt_W       = float(pp_dims['W_mm'])
        opt_delta   = float(pp_dims['delta_mm'])
        opt_y_inset = float(pp_dims['y_inset_mm'])
        opt_sub_hw  = float(pp_dims.get('sub_hw_mm', sub_hw_init))
        print(f'post_proc_only: W={opt_W} mm  Δ={opt_delta} mm  '
              f'yi={opt_y_inset} mm  sub_hw={opt_sub_hw} mm')
    else:
        opt_W, opt_delta, opt_y_inset, opt_sub_hw = (
            W_cp, delta_init, y_inset_init, sub_hw_init)
        print('post_proc_only: no pp_dims override — using warm_start / analytical dims.')

    _FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
        opt_delta, opt_y_inset, opt_W, config.NrTS_final,
        sub_hw_mm=opt_sub_hw)
    return (opt_W, opt_delta, opt_y_inset, opt_sub_hw, [],
            port_f, nf2ff_f, pp_sim_path)


def run_postproc(port_f, nf2ff_f, run_dir, pp_sim_path, graphs_path, vtk_path,
                 opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log):
    """Run full post-processing; return the PostProcessor (carries results)."""
    from src.postproc import PostProcessor
    pp = PostProcessor(
        port=port_f,
        nf2ff_box=nf2ff_f,
        run_dir=run_dir,
        sim_path=pp_sim_path,
        graphs_path=graphs_path,
        vtk_path=vtk_path,
        opt_W=opt_W,
        opt_delta=opt_delta,
        opt_y_inset=opt_y_inset,
        opt_sub_hw=opt_sub_hw,
        opt_log=opt_log,
        post_proc_only=post_proc_only,
        export_vtk_surf=export_vtk_surf,
    )
    pp.run()
    return pp


def export_outputs(pp, run_dir):
    """Generate patch_antenna.kicad_pcb from the post-processed results."""
    if not export_kicad:
        return
    import config
    from src.kicad_export import write_kicad_pcb
    kicad_out = os.path.join(run_dir, 'patch_antenna.kicad_pcb')
    write_kicad_pcb(
        W=pp.results['W_mm'],
        delta=pp.results['delta_mm'],
        y_inset=pp.results['y_inset_mm'],
        substrate_h=config.substrate_thickness,
        output_path=kicad_out,
        sub_hw_mm=pp.results['sub_hw_mm'],
    )


def main():
    setup_console_and_backend()

    run_dir, sim_path, graphs_path, vtk_path = setup_run_dirs()
    log_file = setup_logging(run_dir)

    print(f'Run directory  : {run_dir}')
    print(f'Sim data       : {sim_path}')
    print(f'Graphs         : {graphs_path}')
    print(f'VTK            : {vtk_path}')
    print(f'Session started: {_dt.datetime.now():%Y-%m-%d %H:%M:%S}')

    (W_cp, delta_init, y_inset_init, sub_hw_init,
     ws, reuse_run_dir) = resolve_dimensions()
    dims = (W_cp, delta_init, y_inset_init, sub_hw_init)

    # ── Geometry preview ──────────────────────────────────────────────
    if not post_proc_only:
        if maybe_preview(run_dir, delta_init, y_inset_init, W_cp, sub_hw_init):
            print('preview_only=True — exiting.', flush=True)
            sys.exit(0)

    # ── Simulation dispatch ───────────────────────────────────────────
    if single_sim_only:
        (opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log,
         port_f, nf2ff_f) = run_single_sim(sim_path, dims)
        pp_sim_path = sim_path
    elif not post_proc_only:
        (opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log,
         port_f, nf2ff_f) = run_optimize(sim_path, W_cp, ws, sub_hw_init)
        pp_sim_path = sim_path
    else:
        (opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log,
         port_f, nf2ff_f, pp_sim_path) = setup_post_proc_only(dims, reuse_run_dir)

    # ── Post-processing ───────────────────────────────────────────────
    pp = run_postproc(port_f, nf2ff_f, run_dir, pp_sim_path, graphs_path, vtk_path,
                      opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log)

    # ── KiCad export ──────────────────────────────────────────────────
    export_outputs(pp, run_dir)

    # ── Flush log and show plots ──────────────────────────────────────
    log_file.flush()
    import matplotlib.pyplot as plt
    plt.show()


if __name__ == '__main__':
    main()

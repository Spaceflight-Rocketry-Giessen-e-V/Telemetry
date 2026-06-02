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


if __name__ == '__main__':
    import atexit
    import datetime as _dt
    import os
    import subprocess
    import sys

    # ── UTF-8 output on Windows ───────────────────────────────────────
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    # ── matplotlib backend (must be set before any other plt import) ──
    import matplotlib
    try:
        matplotlib.use('TkAgg')
    except Exception:
        try:
            matplotlib.use('Qt5Agg')
        except Exception:
            pass

    # ── imports ───────────────────────────────────────────────────────
    import config
    from src.model     import build_sim, _Tee
    from src.optimizer import Optimizer, _find_latest_results_json, _load_results_json
    from src.postproc  import PostProcessor
    from src.kicad_export import write_kicad_pcb

    # ── Output directory layout ───────────────────────────────────────
    timestamp   = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir     = os.path.join(os.getcwd(), f'RHCP_Patch_{timestamp}')
    sim_path    = os.path.join(run_dir, 'sim_data')
    graphs_path = os.path.join(run_dir, 'graphs')
    vtk_path    = os.path.join(run_dir, 'vtk')

    os.makedirs(graphs_path, exist_ok=True)
    os.makedirs(vtk_path,    exist_ok=True)
    # sim_path must NOT be pre-created — openEMS.Run() requires it absent

    # ── Log tee (stdout → console + simulation.log) ───────────────────
    _log_file = open(os.path.join(run_dir, 'simulation.log'),
                     'w', encoding='utf-8', errors='replace')
    atexit.register(_log_file.close)
    sys.stdout = _Tee(sys.stdout, _log_file)

    print(f'Run directory  : {run_dir}')
    print(f'Sim data       : {sim_path}')
    print(f'Graphs         : {graphs_path}')
    print(f'VTK            : {vtk_path}')
    print(f'Session started: {_dt.datetime.now():%Y-%m-%d %H:%M:%S}')

    # ── Analytical initial dimensions ─────────────────────────────────
    W_cp         = config.W_cp
    delta_init   = W_cp * config._delta_frac
    y_inset_init = W_cp * config._y_inset_frac
    sub_hw_init  = config.SUB_HW_DEFAULT

    # ── Apply warm_start / reuse_best ─────────────────────────────────
    _ws = warm_start  # local copy so we can override from reuse_best
    _reuse_run_dir = None  # set below when reuse_best loads a results.json

    if reuse_best:
        _rj = reuse_results_dir
        if _rj is None:
            _rj = _find_latest_results_json()
        elif os.path.isdir(_rj):
            _cand = os.path.join(_rj, 'results.json')
            _old  = os.path.join(_rj, 'images', 'results.json')
            _rj   = _cand if os.path.exists(_cand) else (_old if os.path.exists(_old) else None)
        if not _rj or not os.path.exists(str(_rj)):
            print('\nERROR: reuse_best=True but no results.json found.')
            print('  Set reuse_results_dir to a previous RHCP_Patch_* folder, or leave None.')
            sys.exit(1)
        try:
            _rW, _rd, _ryi, _rsh = _load_results_json(_rj)
        except Exception as e:
            print(f'\nERROR reading results.json: {e}')
            sys.exit(1)
        _ws = {'W_mm': _rW, 'delta_mm': _rd, 'y_inset_mm': _ryi, 'sub_hw_mm': _rsh}
        _reuse_run_dir = os.path.dirname(os.path.abspath(str(_rj)))
        print(f'\nreuse_best: loaded {_rj}')
        print(f'  → using as warm_start  (W={_rW:.4f}  Δ={_rd:.4f}  '
              f'yi={_ryi:.4f}  sub_hw={_rsh:.2f} mm)')

    if _ws is not None:
        W_cp         = float(_ws['W_mm'])
        delta_init   = float(_ws['delta_mm'])
        y_inset_init = float(_ws['y_inset_mm'])
        sub_hw_init  = float(_ws.get('sub_hw_mm', config.SUB_HW_DEFAULT))
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

    # ── Geometry preview ──────────────────────────────────────────────
    if not post_proc_only:
        print('\n--- Writing initial geometry for preview ---', flush=True)
        FDTD_prev, CSX_prev, _, _ = build_sim(delta_init, y_inset_init, W_cp, NrTS=1,
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

        if preview_only:
            print('preview_only=True — exiting.', flush=True)
            sys.exit(0)

    # ── Simulation dispatch ───────────────────────────────────────────
    if single_sim_only:
        print(f'\n{"="*60}')
        print(f'single_sim_only=True — one high-fidelity sim  (NrTS = {config.NrTS_final})')
        print(f'  W = {W_cp:.2f} mm   Δ = {delta_init:.2f} mm   '
              f'y_inset = {y_inset_init:.2f} mm   sub_hw = {sub_hw_init:.2f} mm')
        print(f'{"="*60}')
        opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log = (
            W_cp, delta_init, y_inset_init, sub_hw_init, [])
        FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
            opt_delta, opt_y_inset, opt_W, config.NrTS_final,
            sub_hw_mm=opt_sub_hw, vtk_dump=export_vtk_surf)
        FDTD_f.Run(sim_path, verbose=1, cleanup=True)

    elif not post_proc_only:
        _par  = min(config.num_workers or os.cpu_count() or 1, 9)
        _n_opt = 10 + 8 + 5 + 9 + 7 + 5 + int(config.SUB_HW_N)
        _secs = (_n_opt / _par * config.NrTS_opt / 40000 * 90
                 + config.NrTS_final / 40000 * 90)
        _eta  = _dt.datetime.now() + _dt.timedelta(seconds=_secs)
        print(f'\n{"="*60}')
        print(f'Starting optimisation  ({_n_opt} FDTD runs  NrTS = {config.NrTS_opt})')
        print(f'  Phases: 0=width(10)  1=coarse-Δ(8)  0b=W-corr(5)'
              f'  2=inset(9)  3=fine-Δ(7)  3b=W-corr(5)  4=GP({config.SUB_HW_N})')
        print(f'  Workers: {_par}  |  Rough wall-clock estimate: ~{int(_secs/60)} min'
              f'  (ETA ~{_eta.strftime("%H:%M")})')
        print(f'{"="*60}')
        opt = Optimizer(W_cp, warm_start=_ws, sub_hw_init=sub_hw_init)
        opt_W, opt_delta, opt_y_inset, opt_sub_hw, opt_log = opt.run()

        print('\n--- Final high-fidelity simulation (with VTK field dumps) ---')
        print(f'  W = {opt_W:.2f} mm   Δ = {opt_delta:.2f} mm   '
              f'y_inset = {opt_y_inset:.2f} mm   sub_hw = {opt_sub_hw:.2f} mm   '
              f'NrTS = {config.NrTS_final}')
        FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
            opt_delta, opt_y_inset, opt_W, config.NrTS_final,
            sub_hw_mm=opt_sub_hw, vtk_dump=export_vtk_surf)
        FDTD_f.Run(sim_path, verbose=1, cleanup=True)

    else:
        # post_proc_only: rebuild model so CalcPort / CalcNF2FF work on existing sim_data
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
        opt_log = []
        FDTD_f, _CSX_f, port_f, nf2ff_f = build_sim(
            opt_delta, opt_y_inset, opt_W, config.NrTS_final,
            sub_hw_mm=opt_sub_hw)

    # ── Post-processing ───────────────────────────────────────────────
    # When re-running post-proc on an existing run the FDTD port data lives
    # in the source run's sim_data, not the newly created (empty) one.
    if post_proc_only and _reuse_run_dir is not None:
        pp_sim_path = os.path.join(_reuse_run_dir, 'sim_data')
        print(f'post_proc_only: reading sim_data from {pp_sim_path}')
    else:
        pp_sim_path = sim_path

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

    # ── KiCad export ──────────────────────────────────────────────────
    if export_kicad:
        kicad_out = os.path.join(run_dir, 'patch_antenna.kicad_pcb')
        write_kicad_pcb(
            W=pp.results['W_mm'],
            delta=pp.results['delta_mm'],
            y_inset=pp.results['y_inset_mm'],
            substrate_h=config.substrate_thickness,
            output_path=kicad_out,
            sub_hw_mm=pp.results['sub_hw_mm'],
        )

    # ── Flush log and show plots ──────────────────────────────────────
    _log_file.flush()
    import matplotlib.pyplot as plt
    plt.show()

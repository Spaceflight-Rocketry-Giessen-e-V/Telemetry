# -*- coding: utf-8 -*-
"""
RHCP Patch Antenna — Ground Station for Sounding Rocket
========================================================
Central entry point.  Edit the switches below and run:

    python run.py

Flat dual-feed (branch-line coupler) RHCP patch: a square patch fed in quadrature
by an etched 90° hybrid coupler driving two orthogonal inset feeds, one edge-launch
SMA input, one SMD 50 Ω resistor on the isolated port.  The whole geometry is a
``PatchParams`` object (src/params.py); all physical constants live in config.py.
"""

# ═══════════════════════ USER SWITCHES ════════════════════════════
# ── Run mode (pick at most one) ───────────────────────────────────
preview_only    = False  # write XML + open AppCSXCAD, then exit
show_geometry   = False  # open AppCSXCAD to inspect geometry before simulating (BLOCKS until
                         # the window is closed). Leave False for unattended/background runs —
                         # the geometry XML is still written either way.
single_sim_only = True   # ON: design FROZEN at the accepted NP-140F dims — W=72.5 / arm=40 on the
                         # 160 mm board (εr 4.15). Validated at full 150k fidelity: f_res 869.5,
                         # S11 −11.0, AR 1.70 dB, AR≤3 beam 52°, RHCP (tests/board_sweep.py 160 mm point).
                         # A run now does ONE confirmation sim + writes the final KiCad board.
                         # Flip False to re-optimise (W grid re-anchors via config.GRID_W_FRAC).
post_proc_only  = False  # skip FDTD entirely, re-run post-processing on existing sim_data

# ── Warm-start / dimension source ────────────────────────────────
# Set warm_start to seed the optimisation (or single sim) from known-good dims.
# Keys are PatchParams fields (any subset; missing fields take config.py seeds):
#   W_mm, cpl_arm_mm, cpl_w50_mm, cpl_w35_mm,
#   inset_x_mm, inset_y_mm, sub_hw_mm
# Leave as None for a cold start from the config.py synthesis seeds.
warm_start = {
    # Re-baselined by UNIFORM SCALING of the only valid clean-CP anchor (W=87.14/arm=48/
    # inset=16 -> AR 0.51 dB at 714 MHz, on geometry with NO inset collision). Scaling the
    # whole resonant structure by 714/869.52 = 0.821 moves resonance AND the coupler
    # quadrature onto the target together: W 87.14->71.5, arm 48->40, inset 16->~13 (the
    # geometry cap at this W lands it at 12.6 == the scaled value). The earlier W=75/arm=40
    # seed came from a diagnosis run on a MALFORMED patch (insets collided) and is retracted.
    'W_mm':       72.5,   # Re-anchored for NP-140F (εr 4.3→4.15). The εr=4.3 optimum was W=71.5
                          #   (AR 1.61 dB @869.52, 44° beam, S11 −12.3, dip at 864.5). Lower εr grows
                          #   the resonant length ~+1.8 % → ~72.5 mm; the ±2 % W grid (config.GRID_W_FRAC)
                          #   brackets the new basin. The optimiser re-centres W/arm; re-tighten after a scout.
    'inset_x_mm': 16.0,   # 50 Ω match; auto-caps to ~12.6 at this W (== scaled depth)
    'inset_y_mm': 16.0,   #   (symmetric square: inset_x == inset_y)
    'cpl_arm_mm': 40.0,   # 0.821 * 48 -> coupler quadrature band centred on 869.52 (gives 44° beam;
                          #   arm=38 breaks CP to beam 0° — do NOT reduce further)
#    'sub_hw_mm':  85.0,   # half-edge of board; layout grows it to fit coupler+feeds
}

# reuse_best: load dims from the most-recent results.json and use them as
# warm_start (overrides the dict above).  Combined with single_sim_only=True
# this reproduces "run one final sim at previous best dims".  Combined with
# single_sim_only=False it re-runs the full optimisation from those dims.
reuse_best        = False
reuse_results_dir = None  # folder to load results.json from; None = auto-find latest

# ── Output options ────────────────────────────────────────────────
export_kicad    = True   # generate patch_antenna.kicad_pcb after final sim
export_vtk_surf = False  # copy J surface-current .vtr files into vtk/ subfolders
                         # (set False to skip files and save disk space)

# ── Post-processing overrides (only used when post_proc_only=True) ─
# Copy the "Final geometry for PCB" values from a previous run's log.
# Leave as None to fall back to warm_start / config seeds.
pp_dims = None
# pp_dims = {'W_mm': 83.5, 'inset_x_mm': 18.0, 'inset_y_mm': 18.0, 'cpl_arm_mm': 47.0}
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

# This project targets CPython 3.14: the openEMS/CSXCAD bindings are installed
# as cp314-ABI wheels, so a different minor version cannot load them (see
# SETUP.md and .python-version).
REQUIRED_PY = (3, 14)


def preflight_check():
    """Fail fast with an actionable message when the openEMS bindings are missing.

    CSXCAD/openEMS are NOT on PyPI or conda, so `pip install -r requirements.txt`
    cannot provide them -- they are installed out-of-band alongside a native
    openEMS (see SETUP.md).  Without this check the first heavy import dies with a
    deep `ModuleNotFoundError: No module named 'CSXCAD'` traceback (it actually
    surfaces via `import config` -> openEMS/__init__.py, not src.model).

    Runs only from main(), and imports only the two bindings -- so `import run`
    stays lightweight and openEMS-free, per the module-scope note above.  Message
    is kept ASCII so it prints correctly before the UTF-8 console is configured.
    """
    # Self-healing DLL discovery: the bindings' CSXCAD/__init__.py registers
    # os.environ['OPENEMS_INSTALL_PATH'] as a Windows DLL search dir.  If unset,
    # point it at a standard install so the import can still find CSXCAD.dll /
    # openEMS.dll without relying on a machine-global environment variable.
    if os.name == 'nt' and not os.environ.get('OPENEMS_INSTALL_PATH'):
        for _cand in (r'C:\Program Files\openEMS',
                      r'C:\opt\openEMS',
                      os.path.join(os.environ.get('LOCALAPPDATA', ''), 'openEMS')):
            if _cand and os.path.exists(os.path.join(_cand, 'CSXCAD.dll')):
                os.environ['OPENEMS_INSTALL_PATH'] = _cand
                break

    try:
        import CSXCAD   # noqa: F401  -- import also sets up the Windows DLL path
        import openEMS  # noqa: F401
        return
    except Exception as exc:  # ImportError, or DLL-load error on Windows
        cp       = f'cp{REQUIRED_PY[0]}{REQUIRED_PY[1]}'
        py       = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        ver_note = ('' if sys.version_info[:2] == REQUIRED_PY
                    else f'   <-- mismatch: {cp} wheels will not install/load here')
        bar = '=' * 72
        lines = [
            '', bar,
            ' openEMS Python bindings unavailable -- cannot run the simulation.',
            bar,
            f'   {type(exc).__name__}: {exc}',
            '',
            ' CSXCAD / openEMS are NOT on PyPI or conda, so installing',
            ' requirements.txt does not provide them. They ship as version-specific',
            ' wheels alongside a native openEMS install.  Full steps: SETUP.md',
            '',
            ' Quick fix:',
            '   1. Install native openEMS (provides CSXCAD.dll / openEMS.dll) and',
            '      set OPENEMS_INSTALL_PATH to that folder.',
            '   2. Install the matching bindings into THIS interpreter:',
            f'        "{sys.executable}" -m pip install '
            f'"<openEMS>\\python\\csxcad-*-{cp}-*.whl" '
            f'"<openEMS>\\python\\openems-*-{cp}-*.whl"',
            '',
            f' This project targets Python {REQUIRED_PY[0]}.{REQUIRED_PY[1]}; '
            f'you are on {py}{ver_note}',
        ]
        if os.name == 'nt' and not os.environ.get('OPENEMS_INSTALL_PATH'):
            lines += [
                '',
                ' OPENEMS_INSTALL_PATH is unset and no openEMS install was found at',
                ' C:\\Program Files\\openEMS -- the bindings cannot locate their DLLs.',
            ]
        lines += [bar, '']
        print('\n'.join(lines))
        sys.exit(1)


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
    """Resolve the starting geometry into a PatchParams.

    Precedence: config.py synthesis seeds (default_params) → warm_start dict →
    reuse_best (loads the latest results.json, overrides warm_start).

    Returns (p_init, ws, reuse_run_dir) where p_init is a PatchParams, ws is the
    effective warm-start dict (or None) and reuse_run_dir is the source run folder
    when reuse_best loaded a results.json (else None).
    """
    from src.params import PatchParams, default_params
    from src.optimizer import _find_latest_results_json, _load_results_json

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
            p_loaded = _load_results_json(rj)
        except Exception as e:
            print(f'\nERROR reading results.json: {e}')
            sys.exit(1)
        ws            = p_loaded.to_dict()
        reuse_run_dir = os.path.dirname(os.path.abspath(str(rj)))
        print(f'\nreuse_best: loaded {rj}')

    # Standalone post-proc source (without reuse_best): post_proc_only needs an
    # existing run's sim_data, and the error message advertises reuse_results_dir as
    # a usable option on its own. Locate that run here and — crucially — load its
    # results.json dims so the rebuilt model MATCHES the sim_data it reads; using
    # warm_start/config seeds that differ from the source geometry would silently
    # desync the MSL-port probes (wrong S11 / Zin / f_res, no error). pp_dims can
    # still override below for advanced use.
    if reuse_run_dir is None and (post_proc_only or reuse_results_dir is not None):
        rj2 = None
        if reuse_results_dir is not None and os.path.isdir(reuse_results_dir):
            cand = os.path.join(reuse_results_dir, 'results.json')
            old  = os.path.join(reuse_results_dir, 'images', 'results.json')
            rj2  = cand if os.path.exists(cand) else (old if os.path.exists(old) else None)
        elif reuse_results_dir is None:
            rj2 = _find_latest_results_json()
        if rj2 and os.path.exists(str(rj2)):
            try:
                ws = _load_results_json(rj2).to_dict()
            except Exception as e:
                print(f'\nWARNING: could not read {rj2}: {e}')
            reuse_run_dir = os.path.dirname(os.path.abspath(str(rj2)))
            print(f'\npost-proc source run: {reuse_run_dir}')
        elif reuse_results_dir is not None and os.path.isdir(reuse_results_dir) \
                and os.path.isdir(os.path.join(reuse_results_dir, 'sim_data')):
            reuse_run_dir = os.path.abspath(reuse_results_dir)
            print(f'\npost-proc source run (no results.json): {reuse_run_dir}')

    p_init = PatchParams.from_dict(ws) if ws else default_params()

    if ws is not None:
        print('\nWarm-start dims:')
    else:
        print('\nConfig synthesis seeds:')
    print(f'  W = {p_init.W_mm:.3f} mm   cpl_arm = {p_init.cpl_arm_mm:.2f} mm   '
          f'inset x/y = {p_init.inset_x_mm:.2f}/{p_init.inset_y_mm:.2f} mm   '
          f'sub_hw = {p_init.sub_hw_mm:.1f} mm')
    if ws is not None and not reuse_best:
        print('  Optimiser sweep windows are tightened around these values.')

    return p_init, ws, reuse_run_dir


def maybe_preview(run_dir, p_init):
    """Write the initial-geometry XML and open AppCSXCAD.

    Returns True when the caller should exit now (preview_only).
    """
    from src.model import build_full_sim

    print('\n--- Writing initial geometry for preview ---', flush=True)
    _FDTD_prev, CSX_prev, _, _ = build_full_sim(p_init, NrTS=1)
    csx_file = os.path.join(run_dir, 'rhcp_patch_init.xml')
    CSX_prev.Write2XML(csx_file)
    print(f'XML written: {csx_file}', flush=True)

    # Only OPEN the (blocking) AppCSXCAD viewer when explicitly requested. The
    # subprocess.call below waits until the GUI window is closed, so launching it
    # unconditionally would wedge every unattended/background run (incl. the long
    # optimisation) at startup. The XML above is always written for later inspection.
    if preview_only or show_geometry:
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
    else:
        print(f'Skipping AppCSXCAD (show_geometry=False). Inspect later: {csx_file}', flush=True)

    return preview_only


def run_single_sim(sim_path, p_init):
    """single_sim_only: one high-fidelity sim at the resolved dims. Returns params.

    Only builds + runs the FDTD here (writing sim_data); post-processing happens in
    a SEPARATE process (run_postproc_isolated) — see its docstring for why.
    """
    import config
    from src.model import build_full_sim

    print(f'\n{"="*60}')
    print(f'single_sim_only=True — one high-fidelity sim  (NrTS = {config.NrTS_final})')
    print(f'  W = {p_init.W_mm:.2f} mm   cpl_arm = {p_init.cpl_arm_mm:.2f} mm   '
          f'inset x/y = {p_init.inset_x_mm:.2f}/{p_init.inset_y_mm:.2f} mm')
    print(f'{"="*60}')
    FDTD_f, _CSX_f, _port_f, _nf2ff_f = build_full_sim(
        p_init, config.NrTS_final, vtk_dump=export_vtk_surf)
    # Runs alone in the main process — claim all cores (numThreads=0 → max),
    # independent of any ambient OMP_NUM_THREADS the user may have set.
    FDTD_f.Run(sim_path, verbose=1, cleanup=True, numThreads=(os.cpu_count() or 0))
    return p_init


def run_optimize(sim_path, p_init):
    """Full coverage optimisation followed by a final high-fidelity sim.

    Returns (p_opt, opt_log). The final sim only writes sim_data here; the heavy
    post-processing runs in a separate process (run_postproc_isolated).
    """
    import config
    from src.model import build_full_sim
    from src.optimizer import (Optimizer, estimate_seconds, n_opt, phases_label,
                               resolve_workers)

    par   = resolve_workers()
    n_run = n_opt()
    secs  = estimate_seconds(par)  # honest: sums ceil(n_phase/par) waves, incl. final sim
    eta   = _dt.datetime.now() + _dt.timedelta(seconds=secs)
    print(f'\n{"="*60}')
    print(f'Starting optimisation  ({n_run} FDTD runs, two-tier fidelity)')
    print(f'  Search: {phases_label()}')
    print(f'  Workers: {par}  |  Rough wall-clock estimate: ~{int(secs/60)} min'
          f'  (ETA ~{eta.strftime("%H:%M")})')
    print(f'{"="*60}')
    opt = Optimizer(p_init)
    p_opt, opt_log = opt.run()

    print('\n--- Final high-fidelity simulation (with VTK field dumps) ---')
    print(f'  W = {p_opt.W_mm:.2f} mm   cpl_arm = {p_opt.cpl_arm_mm:.2f} mm   '
          f'inset x/y = {p_opt.inset_x_mm:.2f}/{p_opt.inset_y_mm:.2f} mm   '
          f'sub_hw = {p_opt.sub_hw_mm:.1f} mm   NrTS = {config.NrTS_final}')
    FDTD_f, _CSX_f, _port_f, _nf2ff_f = build_full_sim(
        p_opt, config.NrTS_final, vtk_dump=export_vtk_surf)
    # Runs alone in the main process — claim all cores (numThreads=0 → max),
    # independent of any ambient OMP_NUM_THREADS the user may have set.
    FDTD_f.Run(sim_path, verbose=1, cleanup=True, numThreads=(os.cpu_count() or 0))
    return p_opt, opt_log


def setup_post_proc_only(p_init, reuse_run_dir):
    """post_proc_only: resolve the params + source sim_data (no model build here).

    The model is (re)built inside the post-processing child process; this only
    validates that an existing, populated sim_data is available to read.
    Returns (p_post, opt_log, pp_sim_path).
    """
    from src.params import PatchParams

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
        p_post = PatchParams.from_dict(pp_dims)
        print(f'post_proc_only: pp_dims OVERRIDE — W={p_post.W_mm} mm  '
              f'cpl_arm={p_post.cpl_arm_mm} mm  inset x/y={p_post.inset_x_mm}/{p_post.inset_y_mm} mm')
        print('  ! pp_dims MUST match the geometry that produced the source sim_data; a'
              ' mismatch silently desyncs the MSL-port probes (wrong S11/Zin/f_res).')
    else:
        # p_init now carries the source run's results.json dims (resolve_dimensions
        # loads them for the post-proc source), so the rebuilt model matches sim_data.
        p_post = p_init
        print('post_proc_only: using source-run dims (results.json) — matches sim_data.')

    return p_post, [], pp_sim_path


def _postproc_worker(kw):
    """Post-process + KiCad-export in a FRESH (spawned) process.

    The heavy NF2FF post-processing crashes the openEMS bindings (native access
    violation) when run in the SAME process right after a long FDTD.Run() at high
    NrTS — the post-run engine/native state does not survive the Run→heavy-NF2FF
    transition / interpreter teardown. Doing it in a spawned child (a clean
    interpreter that rebuilds the model only to READ the already-saved sim_data)
    sidesteps that entirely. Top-level + a single picklable dict arg so it works
    with the 'spawn' start method on Windows.
    """
    import os as _os
    import sys as _sys
    # Windows DLL discovery (mirror preflight_check) — the spawned child has a
    # clean environment and must locate CSXCAD.dll / openEMS.dll itself.
    if _os.name == 'nt' and not _os.environ.get('OPENEMS_INSTALL_PATH'):
        for _c in (r'C:\Program Files\openEMS', r'C:\opt\openEMS',
                   _os.path.join(_os.environ.get('LOCALAPPDATA', ''), 'openEMS')):
            if _c and _os.path.exists(_os.path.join(_c, 'CSXCAD.dll')):
                _os.environ['OPENEMS_INSTALL_PATH'] = _c
                break
    if hasattr(_sys.stdout, 'reconfigure'):
        _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    # Tee the child's output into the run's simulation.log so nothing is lost.
    logf = None
    if kw.get('log_path'):
        try:
            from src.model import _Tee
            logf = open(kw['log_path'], 'a', encoding='utf-8', errors='replace')
            _sys.stdout = _Tee(_sys.stdout, logf)
        except Exception:
            logf = None
    # Headless backend — set BEFORE importing postproc (which imports pyplot).
    import matplotlib
    try:
        matplotlib.use('Agg')
    except Exception:
        pass

    import config
    from src.model import build_full_sim
    from src.postproc import PostProcessor

    p = kw['params']
    _F, _C, port, nf2ff = build_full_sim(p, 1)   # fresh model: only to read sim_data
    pp = PostProcessor(
        port=port, nf2ff_box=nf2ff, run_dir=kw['run_dir'], sim_path=kw['sim_path'],
        graphs_path=kw['graphs_path'], vtk_path=kw['vtk_path'], params=p,
        opt_log=kw['opt_log'], post_proc_only=kw['post_proc_only'],
        export_vtk_surf=kw['export_vtk_surf'])
    pp.run()
    if kw['export_kicad']:
        from src.kicad_export import write_kicad_pcb
        write_kicad_pcb(p, substrate_h=config.substrate_thickness,
                        output_path=_os.path.join(kw['run_dir'], 'patch_antenna.kicad_pcb'))
    if logf:
        try:
            logf.flush(); logf.close()
        except Exception:
            pass


def run_postproc_isolated(run_dir, pp_sim_path, graphs_path, vtk_path,
                          p_final, opt_log, log_path=None):
    """Post-process (+ KiCad export) in a spawned child process; True on success.

    Isolating post-processing from the parent — which still holds openEMS engine
    state from FDTD.Run() — avoids a native segfault on the Run→heavy-NF2FF
    transition at high NrTS. The child rebuilds the model only to read the saved
    sim_data, so the simulation is never repeated.
    """
    import multiprocessing as mp
    kw = dict(run_dir=run_dir, sim_path=pp_sim_path, graphs_path=graphs_path,
              vtk_path=vtk_path, params=p_final, opt_log=opt_log,
              post_proc_only=post_proc_only, export_vtk_surf=export_vtk_surf,
              export_kicad=export_kicad, log_path=log_path)
    sys.stdout.flush()
    proc = mp.get_context('spawn').Process(target=_postproc_worker, args=(kw,))
    proc.start()
    proc.join()
    if proc.exitcode != 0:
        print(f'\n{"!"*64}')
        print(f'! Post-processing subprocess exited abnormally (code {proc.exitcode}).')
        print(f'! The SIMULATION DATA is intact:')
        print(f'!   {pp_sim_path}')
        print(f'! Recover graphs / results.json / KiCad board WITHOUT re-simulating:')
        print(f'!   set post_proc_only=True and reuse_results_dir="{run_dir}"')
        print(f'!   (or reuse_best=True) in run.py, then re-run.')
        print(f'{"!"*64}', flush=True)
        return False
    return True


def main():
    preflight_check()      # fail fast (actionable message) if openEMS is missing
    setup_console_and_backend()

    run_dir, sim_path, graphs_path, vtk_path = setup_run_dirs()
    log_file = setup_logging(run_dir)
    log_path = os.path.join(run_dir, 'simulation.log')

    print(f'Run directory  : {run_dir}')
    print(f'Sim data       : {sim_path}')
    print(f'Graphs         : {graphs_path}')
    print(f'VTK            : {vtk_path}')
    print(f'Session started: {_dt.datetime.now():%Y-%m-%d %H:%M:%S}')

    p_init, ws, reuse_run_dir = resolve_dimensions()

    # ── Geometry preview ──────────────────────────────────────────────
    if not post_proc_only:
        if maybe_preview(run_dir, p_init):
            print('preview_only=True — exiting.', flush=True)
            sys.exit(0)

    # ── Simulation dispatch (writes sim_data; no in-process post-proc) ─
    if single_sim_only:
        p_final, opt_log, pp_sim_path = run_single_sim(sim_path, p_init), [], sim_path
    elif not post_proc_only:
        p_final, opt_log = run_optimize(sim_path, p_init)
        pp_sim_path = sim_path
    else:
        p_final, opt_log, pp_sim_path = setup_post_proc_only(p_init, reuse_run_dir)

    # ── Post-processing + KiCad export in an ISOLATED child process ────
    # (avoids the native segfault on the in-process Run→heavy-NF2FF transition;
    # the child reads the saved sim_data, so the simulation is never repeated.)
    ok = run_postproc_isolated(run_dir, pp_sim_path, graphs_path, vtk_path,
                               p_final, opt_log, log_path=log_path)
    if ok:
        print(f'\nDone. Graphs + results.json + KiCad board in:\n  {run_dir}', flush=True)

    # ── Hard exit ─────────────────────────────────────────────────────
    # The parent still holds openEMS engine/native state from FDTD.Run(), whose
    # interpreter teardown can itself segfault on Windows after a high-NrTS run.
    # The child has already written every output, so flush and bypass teardown
    # with os._exit() to return a clean, reliable status.
    try:
        log_file.flush(); log_file.close()
    except Exception:
        pass
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(0 if ok else 1)


if __name__ == '__main__':
    main()

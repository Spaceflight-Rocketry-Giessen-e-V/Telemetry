# -*- coding: utf-8 -*-
"""Six-phase RHCP patch antenna optimizer (parallel FDTD sweeps)."""

import atexit
import datetime as _dt
import glob
import json
import math
import multiprocessing as _mp
import os
import shutil
import tempfile
import time
from concurrent.futures import (ProcessPoolExecutor, TimeoutError as _FuturesTimeout,
                                as_completed)

import numpy as np

import config
from src.metrics import failure_result


# ── Phase schedule: the single source of truth for sweep sizes and labels ──
# (phase_id, n_candidates, short_label). The Phase-4 ground-plane sweep uses
# config.SUB_HW_N candidates and is accounted for separately in n_opt().
#
# Candidate counts are aligned to the default worker count (config.MAX_WORKERS=9)
# so every phase is a single FULL wave — no straggler wave, no idle cores — while
# also giving finer W/Δ grids than the old (10,8,5,9,7,5) counts. On a machine
# with fewer cores the pool simply wave-rounds (still correct). Edit freely, but
# keeping each count == the worker count maximises utilisation.
PHASES = [
    ('0',   9, 'width(9)'),
    ('1',   9, 'coarse-Δ(9)'),
    ('0b',  9, 'W-corr(9)'),
    ('2',   9, 'inset(9)'),
    ('3',   9, 'fine-Δ(9)'),
    ('3b',  9, 'W-corr(9)'),
]
PHASE_N = {pid: n for pid, n, _ in PHASES}


def n_opt() -> int:
    """Total number of FDTD runs across all phases, including the GP sweep."""
    return sum(n for _, n, _ in PHASES) + int(config.SUB_HW_N)


def phases_label() -> str:
    """One-line 'Phases: 0=width(10) 1=coarse-Δ(8) ...' header (run.py banner)."""
    parts = '  '.join(f'{pid}={lbl}' for pid, _, lbl in PHASES)
    return f'{parts}  4=GP({int(config.SUB_HW_N)})'


def resolve_workers(num_workers: int | None = None) -> int:
    """Resolve the parallel-worker count, capped by config.MAX_WORKERS.

    num_workers=None falls back to config.num_workers, then os.cpu_count().
    The optimiser pool and the run.py ETA both call this, so they can never
    disagree about how many openEMS subprocesses run concurrently.
    """
    nw = num_workers if num_workers is not None else config.num_workers
    nw = nw if nw and nw > 0 else (os.cpu_count() or 1)
    return min(nw, config.MAX_WORKERS)


def _sim_seconds(n_timesteps: int) -> float:
    """Rough wall-clock for one FDTD run: ~90 s per 40 000 time steps."""
    return n_timesteps / 40000 * 90


def estimate_seconds(num_workers: int | None = None) -> float:
    """Wall-clock estimate for a full optimisation + final high-fidelity sim.

    Single source of truth shared with the run.py banner so the two can never
    disagree (mirrors resolve_workers). Sums ceil(n_phase / par) WAVES per phase
    — honest about the per-phase barrier — rather than the old n_run/par formula,
    which assumed perfect packing and so under-estimated. The dynamic-thread
    speed-up on under-filled waves is ignored here (kept conservative).
    """
    par   = resolve_workers(num_workers)
    waves = sum(math.ceil(n / par) for _, n, _ in PHASES)
    waves += math.ceil(int(config.SUB_HW_N) / par)
    return waves * _sim_seconds(config.NrTS_opt) + _sim_seconds(config.NrTS_final)


def _sweep_stale_temp_dirs():
    """Delete leftover rhcp_* sim dirs (from killed workers / crashed runs).

    Registered with atexit in the MAIN process ONLY — a spawned pool worker must
    never run this or it would delete its siblings' live sim directories.
    """
    for d in glob.glob(os.path.join(tempfile.gettempdir(), 'rhcp_*')):
        shutil.rmtree(d, ignore_errors=True)


if _mp.parent_process() is None:        # true in the main process, not in workers
    atexit.register(_sweep_stale_temp_dirs)


def _cost(r) -> float:
    """Weighted combined cost — lower is better. Used by every optimizer phase.

    Each term is normalized to be O(1) at the boundary of the "good" region.
    Penalties (max(0, ...)) push frequency / S11 / AR toward their thresholds
    and go silent once met.  Gain is a *tiebreaker only among feasible designs*:
    a candidate earns gain credit only when it already meets the CP + match
    spec (right-handed, AR ≤ AR_MAX, S11 ≤ −10 dB), and the credit is clamped
    to [0, GAIN_CAP].  So a high-gain but poorly-circular design earns nothing
    and can never out-score a properly circular one — fixing the old behaviour
    where the optimiser traded away axial ratio for raw directivity.

    AR is the true axial ratio (≥0, smaller = better); a wrong-handed result
    (LHCP dominant when we want RHCP) takes a flat penalty on top.  Here AR is
    the WORST value over f_target ± AR_MARGIN_MHZ, so the optimiser selects for
    CP that survives a resonance drift rather than a fragile single-frequency null.

    A board-area penalty (W_AREA · (sub_hw/SUB_HW_DEFAULT)²) is added so the
    Phase-4 ground-plane sweep prefers the smallest board that still meets spec.
    """
    pen_freq = config.W_FREQ  * abs(r['f_res'] - config.f_target) / config.fc
    pen_s11  = config.W_MATCH * max(0.0, r['s11_dB'] + 10.0)
    pen_ar   = config.W_CP    * max(0.0, r['ar_dB'] - config.AR_MAX_DB) / config.AR_MAX_DB
    if not r.get('rhcp', True):
        pen_ar += config.W_CP * config.WRONG_HAND_PENALTY

    # Ground-plane area penalty ∝ board area (sub_hw²): drives the optimiser to
    # the smallest feasible board, since beyond ~0.5–0.6 λ a bigger GP buys
    # negligible gain. A raw worker result has no 'sub_hw' (it is added later by
    # _record), so fall back to the default — _cost must never KeyError.
    sub_hw   = r.get('sub_hw', config.SUB_HW_DEFAULT)
    pen_area = config.W_AREA * (sub_hw / config.SUB_HW_DEFAULT) ** 2

    # r['ar_dB'] is the WORST axial ratio over f_target ± AR_MARGIN_MHZ (set in
    # the worker), so feasibility/gain credit require CP that holds across the
    # band, not just at the centre frequency.
    feasible = (r.get('rhcp', True)
                and r['ar_dB'] <= config.AR_MAX_DB
                and r['s11_dB'] <= -10.0)
    rew_gain = (config.W_GAIN * max(0.0, min(r['Dmax'] - 5.0, config.GAIN_CAP))
                if feasible else 0.0)
    return pen_freq + pen_s11 + pen_ar + pen_area - rew_gain


def _run_sim_worker(kw: dict) -> dict:
    """Top-level worker: build and run one FDTD sim in a child process.

    Must be a module-level function (not a method) so multiprocessing can
    pickle it on Windows (spawn start method).  Heavy dependencies are imported
    inside the function so they load once per spawned child.
    """
    import os as _os
    n_threads = int(kw.get('num_threads', 1))
    # Hard set (NOT setdefault): on Windows spawn the child inherits the parent
    # env, so setdefault would be a no-op when OMP_NUM_THREADS is already set,
    # silently oversubscribing cores. The authoritative control is numThreads
    # passed to FDTD.Run below; this just keeps any incidental BLAS in step.
    _os.environ['OMP_NUM_THREADS'] = str(n_threads)
    import shutil as _shutil
    import tempfile as _tempfile
    import numpy as _np
    import config as _cfg
    from src.model import build_sim as _build
    from src.metrics import (axial_ratio_db as _ar, cp_center_freq as _cf,
                             failure_result as _fail, freq_eval_grid as _grid,
                             s11_db as _s11db)

    # Unique temp dir per sim: mkdtemp can never collide, even if two candidates
    # round to the same readable suffix (the old gettempdir()/rhcp_<suffix> could,
    # and one worker's cleanup=True could then wipe the other's data mid-read).
    sp = _tempfile.mkdtemp(prefix=f'rhcp_{kw["sim_suffix"]}_')
    try:
        FDTD, _CSX, port, nf2ff_box = _build(
            kw['delta_mm'], kw['y_inset_mm'], kw['W_patch'], kw['NrTS'],
            sub_hw_mm=kw.get('sub_hw_mm', _cfg.SUB_HW_DEFAULT))
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=n_threads)

        f_eval = _grid()
        port.CalcPort(sp, f_eval)
        s11_dB_all = _s11db(port.uf_ref, port.uf_inc)
        s11_dB     = float(s11_dB_all[0])
        zin        = port.uf_tot[0] / port.if_tot[0]
        # f_res: weighted centroid over the swept band ONLY. Index 0 of the grid
        # is f_target (a deliberate duplicate, so s11_dB[0] reads S11 at the
        # design frequency); excluding it keeps f_target from being double-
        # counted in the matched-bandwidth centroid.
        f_res      = _cf(f_eval[1:], s11_dB_all[1:])

        # NF2FF grid: θ=0 (boresight) for Dmax, plus the 1°/2°/3° ring used for
        # the AR estimate — the SAME near-boresight cone postproc reports, so
        # the optimiser selects on the metric the final run will confirm.
        # NF2FF at f_target AND f_target ± AR_MARGIN: select on the WORST axial
        # ratio across the band, so a razor-thin AR null that a resonance drift
        # would fall off cannot win. The transform re-uses the recorded near
        # fields, so the extra frequencies are nearly free. Index 1 is f_target —
        # read Dmax and handedness there.
        dAR    = _cfg.AR_MARGIN_MHZ * 1e6
        f_band = [_cfg.f_target - dAR, _cfg.f_target, _cfg.f_target + dAR]
        res = nf2ff_box.CalcNF2FF(sp, f_band,
                                   theta=[0.0, 1.0, 2.0, 3.0, 5.0, 10.0],
                                   phi=[0., 90., 180., 270.],
                                   center=[0, 0, 1e-3])
        # True axial ratio from the θ∈{1,2,3}° ring (rows 1:4) at each frequency;
        # skip θ=0 where the E_cprh/E_cplh split is degenerate on-axis.
        ar_band  = [_ar(res.E_cprh[n][1:4], res.E_cplh[n][1:4]) for n in range(3)]
        ar_worst = max(a for a, _ in ar_band)        # worst across the band
        _, is_rhcp = ar_band[1]                       # handedness at f_target
        Dmax  = float(res.Dmax[1])
        return {'s11_dB': s11_dB, 'f_res': f_res, 'ar_dB': ar_worst, 'Dmax': Dmax,
                'rhcp': is_rhcp,
                'zin_re': float(_np.real(zin)), 'zin_im': float(_np.imag(zin)),
                'ok': True}
    except Exception as exc:
        return {**_fail(), '_exc': str(exc)}
    finally:
        if _os.path.exists(sp):
            _shutil.rmtree(sp, ignore_errors=True)


def _find_latest_results_json() -> str | None:
    """Return path of most-recently-modified results.json under cwd.

    Checks the new layout (RHCP_Patch_*/results.json) first, then falls back
    to the old layout (RHCP_Patch_*/images/results.json) for backward compat.
    """
    cwd = os.getcwd()
    new = glob.glob(os.path.join(cwd, 'RHCP_Patch_*', 'results.json'))
    old = glob.glob(os.path.join(cwd, 'RHCP_Patch_*', 'images', 'results.json'))
    candidates = new + old
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def _load_results_json(rjson_path: str) -> tuple:
    """Load and validate a results.json.

    Returns (W_mm, delta_mm, y_inset_mm, sub_hw_mm).
    sub_hw_mm defaults to config.SUB_HW_DEFAULT for results.json files
    written before the Phase 4 GP sweep was added.
    """
    with open(rjson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key in ('W_mm', 'delta_mm', 'y_inset_mm'):
        if key not in data:
            raise KeyError(f'results.json is missing required key "{key}"')
    return (float(data['W_mm']), float(data['delta_mm']),
            float(data['y_inset_mm']),
            float(data.get('sub_hw_mm', config.SUB_HW_DEFAULT)))


class Optimizer:
    """Six-phase optimizer: width → coarse Δ → W-correct → inset → fine Δ → W-correct → GP.

    Phase 0:  Sweep patch side W to align resonance with f_target.
    Phase 1:  Fix W, sweep truncation ratio Δ/W for best RHCP purity.
    Phase 0b: Re-tune W at the actual Phase-1 Δ (resonance shifts with Δ).
    Phase 2:  Fix W and Δ, sweep y_inset for best impedance match.
    Phase 3:  Fine-grid Δ/W search around Phase-1 best with correct inset.
    Phase 3b: Re-tune W after Phase-3 Δ adjustment (resonance drifts again).
    Phase 4:  Sweep ground-plane half-width for boresight gain.
    """

    def __init__(self, W_patch_init: float, warm_start: dict | None = None,
                 num_workers: int | None = None,
                 sub_hw_init: float | None = None):
        self._W_init      = W_patch_init
        self._ws          = warm_start
        self._log: list   = []
        self._n_done      = 0
        self._t_start     = None
        self._num_workers = resolve_workers(num_workers)
        self._pool        = None  # one persistent pool, created lazily in _run_batch
        # Phases 0–3b all use one fixed GP size; Phase 4 sweeps it. Clamp a
        # warm-started value (e.g. a stale 375 mm board from an old results.json)
        # into the current [SUB_HW_MIN, SUB_HW_MAX] window so the tuning phases
        # never run at a board size the final design can't use.
        _sh = float(sub_hw_init) if sub_hw_init is not None else config.SUB_HW_DEFAULT
        self._sub_hw = min(max(_sh, config.SUB_HW_MIN), config.SUB_HW_MAX)
        self.N_OPT   = n_opt()

        # Starting fractions — overridden by warm-start if provided
        self._delta_frac   = config._delta_frac
        self._y_inset_frac = config._y_inset_frac
        if warm_start is not None:
            self._delta_frac   = float(warm_start['delta_mm'])   / float(warm_start['W_mm'])
            self._y_inset_frac = float(warm_start['y_inset_mm']) / float(warm_start['W_mm'])

    def run(self) -> tuple:
        """Run all phases. Returns (opt_W, opt_delta, opt_y_inset, opt_sub_hw, log).

        Thin wrapper around _run_all_phases so the shared worker pool is always
        shut down — even if a phase raises.
        """
        self._t_start = time.monotonic()
        try:
            return self._run_all_phases()
        finally:
            self._shutdown_pool()

    def _run_all_phases(self) -> tuple:
        opt_W   = self._phase0()
        best_dr = self._phase1(opt_W)
        opt_W   = self._phase0b(opt_W, best_dr)
        best_yi = self._phase2(opt_W, best_dr)
        best_dr3, opt_yi = self._phase3(opt_W, best_dr, best_yi)
        opt_W   = self._phase3b(opt_W, best_dr3, opt_yi)
        opt_sub_hw = self._phase4(opt_W, best_dr3, opt_yi)

        opt_d = best_dr3 * opt_W

        total = time.monotonic() - self._t_start
        print(f'\n  {"="*78}')
        print(f'  OPTIMISATION COMPLETE — {self._fmt_dur(total)}'
              f'  ({total/self.N_OPT:.0f}s/sim avg)')
        print(f'  {"="*78}')
        print(f'  {"Phase":<6}  {"W mm":>6}  {"Δ mm":>6}  {"Δ/W":>5}  {"yi mm":>6}'
              f'  {"gp mm":>6}  {"S11 dB":>7}  {"AR dB":>6}  {"G dBi":>6}  {"cost":>6}')
        print(f'  {"-"*78}')
        phase_labels = [
            ('0',  'width sweep best'),
            ('1',  'coarse Δ best'),
            ('0b', 'W correction best'),
            ('2',  'inset best'),
            ('3',  'fine Δ best'),
            ('3b', 'W correction best'),
            ('4',  'GP sweep best  ← FINAL'),
        ]
        for ph, label in phase_labels:
            pts = [x for x in self._log if x['phase'] == ph]
            if not pts:
                continue
            bst = min(pts, key=_cost)
            print(f'  {ph:<6}  {bst["W"]:>6.2f}  {bst["dr"]*bst["W"]:>6.2f}'
                  f'  {bst["dr"]:>5.3f}  {bst["yi"]:>6.2f}'
                  f'  {bst["sub_hw"]*2:>6.1f}'
                  f'  {bst["s11_dB"]:>7.1f}  {bst["ar_dB"]:>6.1f}'
                  f'  {bst["Dmax"]:>6.1f}  {_cost(bst):>6.2f}   Phase {ph} {label}')
        print(f'  {"="*78}')
        print(f'  Final geometry for PCB:')
        print(f'    Patch side W   = {opt_W:.2f} mm')
        print(f'    Corner cut Δ   = {opt_d:.2f} mm  (Δ/W = {opt_d/opt_W:.3f})')
        print(f'    Feed inset     = {opt_yi:.2f} mm')
        print(f'    Ground plane   = {opt_sub_hw*2:.1f} × {opt_sub_hw*2:.1f} mm')

        return opt_W, opt_d, opt_yi, opt_sub_hw, self._log

    # ── phases ────────────────────────────────────────────────────────

    def _phase0(self) -> float:
        print('\n=== Phase 0: Patch width sweep (frequency tuning) ===')
        if self._ws is not None:
            W_cands = self._W_init * np.linspace(0.96, 1.04, PHASE_N['0'])
            print(f'  (warm-start: ±4 % around W = {self._W_init:.4f} mm)')
        else:
            W_cands = self._W_init * np.linspace(0.90, 1.05, PHASE_N['0'])
        jobs = [(W, self._delta_frac, W * self._y_inset_frac,
                 self._mk_kw(W, self._delta_frac, W * self._y_inset_frac, f'p0_W{W:.1f}'))
                for W in W_cands]
        self._run_batch('0', jobs)

        p0      = [x for x in self._log if x['phase'] == '0']
        best    = min(p0, key=_cost)
        opt_W   = best['W']
        print(f'  → Best W = {opt_W:.2f} mm  '
              f'(f_res = {best["f_res"]/1e6:.2f} MHz  '
              f'offset = {(best["f_res"]-config.f_target)/1e6:+.2f} MHz  '
              f'G = {best["Dmax"]:.1f} dBi)')
        return opt_W

    def _phase1(self, opt_W: float) -> float:
        print(f'\n=== Phase 1: Coarse truncation sweep (W = {opt_W:.2f} mm) ===')
        yi_init = opt_W * self._y_inset_frac
        if self._ws is not None:
            dr0   = float(self._ws['delta_mm']) / float(self._ws['W_mm'])
            drs_1 = np.clip(np.linspace(dr0 - 0.06, dr0 + 0.06, PHASE_N['1']), 0.02, 0.30)
            print(f'  (warm-start: Δ/W = {dr0:.4f} ± 0.06)')
        else:
            drs_1 = np.linspace(0.04, 0.28, PHASE_N['1'])
        self._drs_1 = drs_1  # stored for Phase 3 coarse_step
        jobs = [(opt_W, dr, yi_init,
                 self._mk_kw(opt_W, dr, yi_init, f'p1_{dr:.3f}'))
                for dr in drs_1]
        self._run_batch('1', jobs)

        p1      = [x for x in self._log if x['phase'] == '1']
        best    = min(p1, key=_cost)
        best_dr = best['dr']
        print(f'  → Best Δ/W = {best_dr:.3f}  (Δ = {best_dr * opt_W:.2f} mm)'
              f'  AR = {best["ar_dB"]:.1f} dB  G = {best["Dmax"]:.1f} dBi')
        return best_dr

    def _phase0b(self, opt_W: float, best_dr: float) -> float:
        print(f'\n=== Phase 0b: W correction at Δ/W = {best_dr:.3f} ===')
        jobs = [(W, best_dr, self._y_inset_frac * W,
                 self._mk_kw(W, best_dr, self._y_inset_frac * W, f'p0b_W{W:.1f}'))
                for W in opt_W * np.linspace(0.96, 1.04, PHASE_N['0b'])]
        self._run_batch('0b', jobs)

        p0b   = [x for x in self._log if x['phase'] == '0b']
        best  = min(p0b, key=_cost)
        opt_W = best['W']
        print(f'  → Corrected W = {opt_W:.2f} mm  '
              f'(f_res = {best["f_res"]/1e6:.2f} MHz  '
              f'offset = {(best["f_res"]-config.f_target)/1e6:+.2f} MHz  '
              f'G = {best["Dmax"]:.1f} dBi)')
        return opt_W

    def _phase2(self, opt_W: float, best_dr: float) -> float:
        print(f'\n=== Phase 2: Feed inset sweep (Δ/W = {best_dr:.3f}  W = {opt_W:.2f} mm) ===')
        if self._ws is not None:
            yi0   = float(self._ws['y_inset_mm'])
            yis_2 = np.clip(
                np.linspace(yi0 - 0.04 * opt_W, yi0 + 0.04 * opt_W, PHASE_N['2']),
                0.01 * opt_W, 0.22 * opt_W)
            print(f'  (warm-start: yi = {yi0:.4f} mm ± {0.04*opt_W:.2f} mm)')
        else:
            yis_2 = np.linspace(0.01 * opt_W, 0.22 * opt_W, PHASE_N['2'])
        jobs = [(opt_W, best_dr, yi,
                 self._mk_kw(opt_W, best_dr, yi, f'p2_yi{yi:.1f}'))
                for yi in yis_2]
        self._run_batch('2', jobs)

        p2      = [x for x in self._log if x['phase'] == '2']
        best    = min(p2, key=_cost)
        best_yi = best['yi']
        print(f'  → Best y_inset = {best_yi:.2f} mm  '
              f'S11 = {best["s11_dB"]:.1f} dB  G = {best["Dmax"]:.1f} dBi')
        return best_yi

    def _phase3(self, opt_W: float, best_dr: float, best_yi: float) -> tuple:
        print(f'\n=== Phase 3: Fine truncation sweep (yi = {best_yi:.2f} mm) ===')
        coarse_step = (self._drs_1[1] - self._drs_1[0]) / 2
        drs_3 = np.clip(
            np.linspace(best_dr - 2 * coarse_step, best_dr + 2 * coarse_step, PHASE_N['3']),
            0.02, 0.30)
        jobs = [(opt_W, dr, best_yi,
                 self._mk_kw(opt_W, dr, best_yi, f'p3_{dr:.4f}'))
                for dr in drs_3]
        self._run_batch('3', jobs)

        p3   = [x for x in self._log if x['phase'] == '3']
        best = min(p3, key=_cost)
        return best['dr'], best['yi']

    def _phase3b(self, opt_W: float, best_dr3: float, opt_yi: float) -> float:
        print(f'\n=== Phase 3b: W correction at Δ/W = {best_dr3:.3f} ===')
        jobs = [(W, best_dr3, opt_yi,
                 self._mk_kw(W, best_dr3, opt_yi, f'p3b_W{W:.1f}'))
                for W in opt_W * np.linspace(0.96, 1.04, PHASE_N['3b'])]
        self._run_batch('3b', jobs)

        p3b   = [x for x in self._log if x['phase'] == '3b']
        best  = min(p3b, key=_cost)
        opt_W = best['W']
        print(f'  → Corrected W = {opt_W:.2f} mm  '
              f'(f_res = {best["f_res"]/1e6:.2f} MHz  '
              f'offset = {(best["f_res"]-config.f_target)/1e6:+.2f} MHz  '
              f'G = {best["Dmax"]:.1f} dBi)')
        return opt_W

    def _phase4(self, opt_W: float, best_dr3: float, opt_yi: float) -> float:
        """Sweep ground-plane half-width at the locked-in patch dimensions.

        GP affects boresight gain (and slightly back-lobe) but only weakly
        perturbs the patch's resonance/match, so it runs last. Selects on the
        same _cost metric: because a bigger GP barely adds gain in this small
        range while the W_AREA area penalty grows with board size, this now
        picks the SMALLEST board that still meets the match / AR / frequency spec.
        """
        sub_hws = np.linspace(config.SUB_HW_MIN, config.SUB_HW_MAX, config.SUB_HW_N)
        print(f'\n=== Phase 4: Ground-plane sweep '
              f'(GP edge {2*config.SUB_HW_MIN:.0f}–{2*config.SUB_HW_MAX:.0f} mm) ===')
        jobs = [(opt_W, best_dr3, opt_yi,
                 self._mk_kw(opt_W, best_dr3, opt_yi, f'p4_gp{sh:.0f}', sub_hw=sh))
                for sh in sub_hws]
        self._run_batch('4', jobs)

        p4   = [x for x in self._log if x['phase'] == '4']
        best = min(p4, key=_cost)
        print(f'  → Best GP edge = {best["sub_hw"]*2:.1f} mm  '
              f'G = {best["Dmax"]:.1f} dBi  S11 = {best["s11_dB"]:.1f} dB  '
              f'AR = {best["ar_dB"]:.1f} dB')
        return float(best['sub_hw'])

    # ── helpers ───────────────────────────────────────────────────────

    def _mk_kw(self, W, dr, yi, suffix, sub_hw=None):
        """Per-sim kwargs dict handed to the worker (identical shape every phase).

        num_threads is a placeholder of 1; _run_batch sets the real value once the
        wave width for the phase is known (dynamic idle-core reclamation).
        """
        return {'delta_mm': dr * W, 'y_inset_mm': yi, 'W_patch': W,
                'sub_hw_mm': self._sub_hw if sub_hw is None else sub_hw,
                'NrTS': config.NrTS_opt, 'sim_suffix': suffix,
                'num_threads': 1}

    # ── worker-pool lifecycle ──────────────────────────────────────────
    def _ensure_pool(self) -> ProcessPoolExecutor:
        """Return the persistent pool, creating it on first use."""
        if self._pool is None:
            self._pool = ProcessPoolExecutor(max_workers=self._num_workers)
        return self._pool

    def _rebuild_pool(self):
        """Tear down the pool (cancelling queued work) and start a fresh one.

        Used after a phase timeout so a wedged openEMS child can't poison later
        phases; the running phase already recorded its stragglers as failures.
        """
        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
        self._pool = ProcessPoolExecutor(max_workers=self._num_workers)

    def _shutdown_pool(self):
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None

    def _run_batch(self, phase, jobs: list):
        """Submit a phase's simulations in parallel and record results as they arrive.

        jobs: list of (W, dr, yi, kw_dict) where kw_dict is passed to _run_sim_worker.

        Reuses ONE persistent pool across phases (workers import openEMS once, not
        once per phase). When a wave under-fills the pool, its otherwise-idle cores
        are handed to the running sims as extra openEMS threads. A wedged sim can't
        freeze the run: as_completed has a per-phase timeout, after which any
        stragglers are recorded as failures and the pool is rebuilt.
        """
        # Dynamic threads-per-sim: >1 only when this wave under-fills the pool.
        cores      = os.cpu_count() or self._num_workers
        concurrent = min(len(jobs), self._num_workers)
        n_threads  = max(1, cores // concurrent)
        for _, _, _, kw in jobs:
            kw['num_threads'] = n_threads

        waves    = math.ceil(len(jobs) / self._num_workers)
        t_phase  = waves * _sim_seconds(config.NrTS_opt)
        eta      = _dt.datetime.now() + _dt.timedelta(seconds=t_phase)
        suffixes = '  '.join(kw['sim_suffix'] for _, _, _, kw in jobs)
        print(f'  Phase {phase}: {len(jobs)} sims, {self._num_workers} workers, '
              f'{n_threads} thread(s)/sim  →  ~{self._fmt_dur(t_phase)} '
              f'(phase ETA {eta.strftime("%H:%M")})', flush=True)
        print(f'  Queued: {suffixes}', flush=True)

        pool    = self._ensure_pool()
        fut_map = {pool.submit(_run_sim_worker, kw): (W, dr, yi,
                                                      kw.get('sub_hw_mm', self._sub_hw),
                                                      kw['sim_suffix'])
                   for W, dr, yi, kw in jobs}
        pending = set(fut_map)
        try:
            for fut in as_completed(fut_map, timeout=config.PHASE_TIMEOUT_S):
                pending.discard(fut)
                W, dr, yi, sub_hw, suffix = fut_map[fut]
                try:
                    r = fut.result()
                    if not r.get('ok', True) and '_exc' in r:
                        print(f'  !! Sim {suffix} failed: {r["_exc"]}')
                except Exception as exc:
                    print(f'  !! Sim {suffix} raised: {exc}')
                    r = failure_result()
                self._record(phase, W, dr, yi, r, sub_hw=sub_hw)
        except _FuturesTimeout:
            # One or more sims hung past the phase deadline. Record the missing
            # candidates as failures (they can never win _cost) and rebuild the
            # pool so the wedged child can't poison later phases.
            for fut in pending:
                W, dr, yi, sub_hw, suffix = fut_map[fut]
                print(f'  !! Sim {suffix} timed out after {config.PHASE_TIMEOUT_S}s'
                      f' — recorded as failure', flush=True)
                self._record(phase, W, dr, yi, failure_result(), sub_hw=sub_hw)
            self._rebuild_pool()

    def _record(self, phase, W, dr, yi, r, sub_hw=None):
        self._n_done += 1
        if sub_hw is None:
            sub_hw = self._sub_hw
        entry = {'phase': phase, 'W': W, 'dr': dr, 'yi': yi, 'sub_hw': sub_hw, **r}
        self._log.append(entry)
        status  = 'RHCP' if r.get('rhcp', True) else 'LHCP'
        elapsed = time.monotonic() - self._t_start
        rem     = (self.N_OPT - self._n_done) * elapsed / max(self._n_done, 1)
        eta     = _dt.datetime.now() + _dt.timedelta(seconds=rem)
        df      = (r['f_res'] - config.f_target) / 1e6
        print(
            f'  [{self._n_done:2d}/{self.N_OPT}  P{phase}]'
            f'  W={W:5.1f}mm  Δ={dr*W:5.2f}mm(Δ/W={dr:.3f})  yi={yi:5.2f}mm'
            f'  gp={sub_hw*2:5.1f}mm'
            f'  →  S11={r["s11_dB"]:+5.1f}dB  f_res={r["f_res"]/1e6:.2f}MHz({df:+.1f})'
            f'  AR={r["ar_dB"]:4.1f}dB {status}  G={r["Dmax"]:+4.1f}dBi'
            f'  cost={_cost(entry):+5.2f}'
            f'  [+{self._fmt_dur(elapsed)}  ETA {eta.strftime("%H:%M")}]',
            flush=True)

    @staticmethod
    def _fmt_dur(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f'{m}m {s:02d}s'

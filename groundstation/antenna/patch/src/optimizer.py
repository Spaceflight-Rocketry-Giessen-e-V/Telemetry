# -*- coding: utf-8 -*-
"""Six-phase RHCP patch antenna optimizer and single-simulation runner."""

import datetime as _dt
import glob
import json
import os
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

import config
from src.model import build_sim


def _cp_center_freq(f_arr, s11_dB_arr, threshold_dB=-10.0):
    """CP operating frequency as the -S11-weighted centroid of the matched bandwidth.

    Works for both single-mode patches (centroid ≈ argmin) and split-mode CP
    patches (centroid ≈ midpoint of the two modes).  Robust at coarse frequency
    grids where individual mode minima may not resolve as distinct local minima.
    Falls back to argmin when nothing is below threshold.
    """
    mask = s11_dB_arr < threshold_dB
    if not mask.any():
        return float(f_arr[np.argmin(s11_dB_arr)])
    weights = -s11_dB_arr[mask]  # positive; deeper S11 → higher weight
    return float(np.average(f_arr[mask], weights=weights))


def _axial_ratio_db(E_rhcp, E_lhcp):
    """True axial ratio [dB, ≥0] and handedness from circular field components.

    E_rhcp / E_lhcp: complex RHCP / LHCP field samples over a small boresight
    cone (openEMS res.E_cprh / res.E_cplh).  Reduced to scalar magnitudes by
    averaging, then combined with the rigorous polarisation-ellipse formula

        AR = (R + L) / |R − L|        (linear, ≥1)
        AR_dB = 20·log10(AR)          (0 dB = perfect circular)

    This is NOT the same as 20·log10(L/R) (the cross-pol ratio): an AR of 3 dB
    corresponds to a cross-pol ratio of only ≈ −15 dB, so optimising the ratio
    with a −3 dB threshold accepts essentially linear polarisation.

    Returns (ar_dB, is_rhcp) where is_rhcp is True when RHCP dominates.
    """
    R = float(np.mean(np.abs(E_rhcp)))
    L = float(np.mean(np.abs(E_lhcp)))
    ar = (R + L) / (abs(R - L) + 1e-30)
    return 20.0 * np.log10(ar), (R >= L)


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
    (LHCP dominant when we want RHCP) takes a flat penalty on top.
    """
    pen_freq = config.W_FREQ  * abs(r['f_res'] - config.f_target) / config.fc
    pen_s11  = config.W_MATCH * max(0.0, r['s11_dB'] + 10.0)
    pen_ar   = config.W_CP    * max(0.0, r['ar_dB'] - config.AR_MAX_DB) / config.AR_MAX_DB
    if not r.get('rhcp', True):
        pen_ar += config.W_CP * config.WRONG_HAND_PENALTY

    feasible = (r.get('rhcp', True)
                and r['ar_dB'] <= config.AR_MAX_DB
                and r['s11_dB'] <= -10.0)
    rew_gain = (config.W_GAIN * max(0.0, min(r['Dmax'] - 5.0, config.GAIN_CAP))
                if feasible else 0.0)
    return pen_freq + pen_s11 + pen_ar - rew_gain


def _run_sim_worker(kw: dict) -> dict:
    """Top-level worker: build and run one FDTD sim in a child process.

    Must be a module-level function (not a method) so multiprocessing can
    pickle it on Windows (spawn start method).
    """
    import os as _os
    _os.environ.setdefault('OMP_NUM_THREADS', '1')
    import shutil as _shutil
    import tempfile as _tempfile
    import numpy as _np
    import config as _cfg
    from src.model import build_sim as _build

    sp = _os.path.join(_tempfile.gettempdir(), f'rhcp_{kw["sim_suffix"]}')
    try:
        FDTD, _CSX, port, nf2ff_box = _build(
            kw['delta_mm'], kw['y_inset_mm'], kw['W_patch'], kw['NrTS'],
            sub_hw_mm=kw.get('sub_hw_mm', _cfg.SUB_HW_DEFAULT))
        _os.makedirs(sp, exist_ok=True)
        FDTD.Run(sp, verbose=0, cleanup=True)

        f_eval = _np.concatenate([
            [_cfg.f_target],
            _np.linspace(_cfg.f_target * 0.85, _cfg.f_target * 1.15, 25)
        ])
        port.CalcPort(sp, f_eval)
        s11_all    = port.uf_ref / port.uf_inc
        s11_dB_all = 20.0 * _np.log10(_np.abs(s11_all) + 1e-30)
        s11_dB     = float(s11_dB_all[0])
        zin        = port.uf_tot[0] / port.if_tot[0]
        f_res      = _cp_center_freq(f_eval, s11_dB_all)

        # NF2FF grid: θ=0 (boresight) for Dmax, plus the 1°/2°/3° ring used for
        # the AR estimate — the SAME near-boresight cone postproc reports, so
        # the optimiser selects on the metric the final run will confirm.
        res = nf2ff_box.CalcNF2FF(sp, [_cfg.f_target],
                                   theta=[0.0, 1.0, 2.0, 3.0, 5.0, 10.0],
                                   phi=[0., 90., 180., 270.],
                                   center=[0, 0, 1e-3])
        # True axial ratio from the θ∈{1,2,3}° ring (rows 1:4); skip θ=0 where
        # the E_cprh/E_cplh split is degenerate on-axis.
        ar_dB, is_rhcp = _axial_ratio_db(res.E_cprh[0][1:4], res.E_cplh[0][1:4])
        Dmax  = float(res.Dmax[0])
        return {'s11_dB': s11_dB, 'f_res': f_res, 'ar_dB': ar_dB, 'Dmax': Dmax,
                'rhcp': is_rhcp,
                'zin_re': float(_np.real(zin)), 'zin_im': float(_np.imag(zin)),
                'ok': True}
    except Exception as exc:
        return {'s11_dB': 0.0, 'f_res': config.f_target, 'ar_dB': 99.0,
                'Dmax': -99.0, 'rhcp': True,
                'zin_re': 0.0, 'zin_im': 0.0, 'ok': False, '_exc': str(exc)}
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
    """Six-phase optimizer: width → coarse Δ → W-correct → inset → fine Δ → W-correct.

    Phase 0:  Sweep patch side W to align resonance with f_target.
    Phase 1:  Fix W, sweep truncation ratio Δ/W for best RHCP purity.
    Phase 0b: Re-tune W at the actual Phase-1 Δ (resonance shifts with Δ).
    Phase 2:  Fix W and Δ, sweep y_inset for best impedance match.
    Phase 3:  Fine-grid Δ/W search around Phase-1 best with correct inset.
    Phase 3b: Re-tune W after Phase-3 Δ adjustment (resonance drifts again).
    """

    N_OPT = 10 + 8 + 5 + 9 + 7 + 5 + 0  # phase counts; +SUB_HW_N added at runtime

    def __init__(self, W_patch_init: float, warm_start: dict | None = None,
                 num_workers: int | None = None,
                 sub_hw_init: float | None = None):
        self._W_init     = W_patch_init
        self._ws         = warm_start
        self._log: list  = []
        self._n_done     = 0
        self._t_start    = None
        nw = num_workers if num_workers is not None else config.num_workers
        self._num_workers = nw if nw > 0 else os.cpu_count()
        # Phases 0–3b all use the default GP size; Phase 4 sweeps it.
        self._sub_hw = float(sub_hw_init) if sub_hw_init is not None else config.SUB_HW_DEFAULT
        # Recompute N_OPT to include Phase 4.
        self.N_OPT = 10 + 8 + 5 + 9 + 7 + 5 + int(config.SUB_HW_N)

        # Starting fractions — overridden by warm-start if provided
        self._delta_frac   = config._delta_frac
        self._y_inset_frac = config._y_inset_frac
        if warm_start is not None:
            self._delta_frac   = float(warm_start['delta_mm'])   / float(warm_start['W_mm'])
            self._y_inset_frac = float(warm_start['y_inset_mm']) / float(warm_start['W_mm'])

    def run(self) -> tuple:
        """Run all phases. Returns (opt_W, opt_delta, opt_y_inset, opt_sub_hw, log)."""
        self._t_start = time.monotonic()

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
            W_cands = self._W_init * np.linspace(0.96, 1.04, 10)
            print(f'  (warm-start: ±4 % around W = {self._W_init:.4f} mm)')
        else:
            W_cands = self._W_init * np.linspace(0.90, 1.05, 10)
        jobs = [(W, self._delta_frac, W * self._y_inset_frac,
                 {'delta_mm': W * self._delta_frac, 'y_inset_mm': W * self._y_inset_frac,
                  'W_patch': W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p0_W{W:.1f}'})
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
            drs_1 = np.clip(np.linspace(dr0 - 0.06, dr0 + 0.06, 8), 0.02, 0.30)
            print(f'  (warm-start: Δ/W = {dr0:.4f} ± 0.06)')
        else:
            drs_1 = np.linspace(0.04, 0.28, 8)
        self._drs_1 = drs_1  # stored for Phase 3 coarse_step
        jobs = [(opt_W, dr, yi_init,
                 {'delta_mm': dr * opt_W, 'y_inset_mm': yi_init,
                  'W_patch': opt_W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p1_{dr:.3f}'})
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
                 {'delta_mm': best_dr * W, 'y_inset_mm': self._y_inset_frac * W,
                  'W_patch': W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p0b_W{W:.1f}'})
                for W in opt_W * np.linspace(0.96, 1.04, 5)]
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
                np.linspace(yi0 - 0.04 * opt_W, yi0 + 0.04 * opt_W, 9),
                0.01 * opt_W, 0.22 * opt_W)
            print(f'  (warm-start: yi = {yi0:.4f} mm ± {0.04*opt_W:.2f} mm)')
        else:
            yis_2 = np.linspace(0.01 * opt_W, 0.22 * opt_W, 9)
        jobs = [(opt_W, best_dr, yi,
                 {'delta_mm': best_dr * opt_W, 'y_inset_mm': yi,
                  'W_patch': opt_W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p2_yi{yi:.1f}'})
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
            np.linspace(best_dr - 2 * coarse_step, best_dr + 2 * coarse_step, 7),
            0.02, 0.30)
        jobs = [(opt_W, dr, best_yi,
                 {'delta_mm': dr * opt_W, 'y_inset_mm': best_yi,
                  'W_patch': opt_W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p3_{dr:.4f}'})
                for dr in drs_3]
        self._run_batch('3', jobs)

        p3   = [x for x in self._log if x['phase'] == '3']
        best = min(p3, key=_cost)
        return best['dr'], best['yi']

    def _phase3b(self, opt_W: float, best_dr3: float, opt_yi: float) -> float:
        print(f'\n=== Phase 3b: W correction at Δ/W = {best_dr3:.3f} ===')
        jobs = [(W, best_dr3, opt_yi,
                 {'delta_mm': best_dr3 * W, 'y_inset_mm': opt_yi,
                  'W_patch': W, 'sub_hw_mm': self._sub_hw,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p3b_W{W:.1f}'})
                for W in opt_W * np.linspace(0.96, 1.04, 5)]
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
        perturbs the patch's resonance/match, so it runs last. Selects on
        the same _cost metric — gain reward typically dominates here since
        S11/AR/freq are already in their good regions.
        """
        sub_hws = np.linspace(config.SUB_HW_MIN, config.SUB_HW_MAX, config.SUB_HW_N)
        print(f'\n=== Phase 4: Ground-plane sweep '
              f'(GP edge {2*config.SUB_HW_MIN:.0f}–{2*config.SUB_HW_MAX:.0f} mm) ===')
        jobs = [(opt_W, best_dr3, opt_yi,
                 {'delta_mm': best_dr3 * opt_W, 'y_inset_mm': opt_yi,
                  'W_patch': opt_W, 'sub_hw_mm': sh,
                  'NrTS': config.NrTS_opt, 'sim_suffix': f'p4_gp{sh:.0f}'})
                for sh in sub_hws]
        self._run_batch('4', jobs)

        p4   = [x for x in self._log if x['phase'] == '4']
        best = min(p4, key=_cost)
        print(f'  → Best GP edge = {best["sub_hw"]*2:.1f} mm  '
              f'G = {best["Dmax"]:.1f} dBi  S11 = {best["s11_dB"]:.1f} dB  '
              f'AR = {best["ar_dB"]:.1f} dB')
        return float(best['sub_hw'])

    # ── helpers ───────────────────────────────────────────────────────

    def _run_batch(self, phase, jobs: list):
        """Submit a phase's simulations in parallel and record results as they arrive.

        jobs: list of (W, dr, yi, kw_dict) where kw_dict is passed to _run_sim_worker.
        """
        suffixes = '  '.join(kw['sim_suffix'] for _, _, _, kw in jobs)
        print(f'  Queued ({len(jobs)} sims, {self._num_workers} workers): {suffixes}',
              flush=True)
        with ProcessPoolExecutor(max_workers=self._num_workers) as ex:
            fut_map = {ex.submit(_run_sim_worker, kw): (W, dr, yi,
                                                         kw.get('sub_hw_mm', self._sub_hw),
                                                         kw['sim_suffix'])
                       for W, dr, yi, kw in jobs}
            for fut in as_completed(fut_map):
                W, dr, yi, sub_hw, suffix = fut_map[fut]
                try:
                    r = fut.result()
                    if not r.get('ok', True) and '_exc' in r:
                        print(f'  !! Sim {suffix} failed: {r["_exc"]}')
                except Exception as exc:
                    print(f'  !! Sim {suffix} raised: {exc}')
                    r = {'s11_dB': 0.0, 'f_res': config.f_target, 'ar_dB': 99.0,
                         'Dmax': -99.0, 'rhcp': True,
                         'zin_re': 0.0, 'zin_im': 0.0, 'ok': False}
                self._record(phase, W, dr, yi, r, sub_hw=sub_hw)

    def _run_single(self, delta_mm: float, y_inset_mm: float,
                    W_patch: float, sim_suffix: str,
                    sub_hw_mm: float | None = None,
                    NrTS: int | None = None, cleanup: bool = True,
                    verbose: int = 0) -> dict:
        """Build, run, and post-process one FDTD simulation."""
        if NrTS is None:
            NrTS = config.NrTS_opt
        if sub_hw_mm is None:
            sub_hw_mm = config.SUB_HW_DEFAULT
        print(f'  → [{sim_suffix}]  W={W_patch:.2f}mm  Δ={delta_mm:.2f}mm'
              f'  yi={y_inset_mm:.2f}mm  sub_hw={sub_hw_mm:.1f}mm  NrTS={NrTS}',
              flush=True)
        sp = os.path.join(tempfile.gettempdir(), f'rhcp_{sim_suffix}')
        try:
            FDTD, _CSX, port, nf2ff_box = build_sim(delta_mm, y_inset_mm,
                                                     W_patch, NrTS,
                                                     sub_hw_mm=sub_hw_mm)
            if not os.path.exists(sp):
                os.makedirs(sp)
            FDTD.Run(sp, verbose=verbose, cleanup=True)

            f_eval = np.concatenate([
                [config.f_target],
                np.linspace(config.f_target * 0.85, config.f_target * 1.15, 25)
            ])
            port.CalcPort(sp, f_eval)

            s11_all    = port.uf_ref / port.uf_inc
            s11_dB_all = 20.0 * np.log10(np.abs(s11_all) + 1e-30)
            s11_dB     = float(s11_dB_all[0])
            zin        = port.uf_tot[0] / port.if_tot[0]
            f_res      = _cp_center_freq(f_eval, s11_dB_all)

            res = nf2ff_box.CalcNF2FF(sp, [config.f_target],
                                       theta=[0.0, 1.0, 2.0, 3.0, 5.0, 10.0],
                                       phi=[0., 90., 180., 270.],
                                       center=[0, 0, 1e-3])
            ar_dB, is_rhcp = _axial_ratio_db(res.E_cprh[0][1:4],
                                             res.E_cplh[0][1:4])
            Dmax  = float(res.Dmax[0])

            return {'s11_dB': s11_dB, 'f_res': f_res, 'ar_dB': ar_dB,
                    'Dmax': Dmax, 'rhcp': is_rhcp,
                    'zin_re': float(np.real(zin)),
                    'zin_im': float(np.imag(zin)), 'ok': True}

        except Exception as exc:
            print(f'  !! Sim {sim_suffix} failed: {exc}')
            return {'s11_dB': 0.0, 'f_res': config.f_target, 'ar_dB': 99.0,
                    'Dmax': -99.0, 'rhcp': True,
                    'zin_re': 0.0, 'zin_im': 0.0, 'ok': False}

        finally:
            if cleanup and os.path.exists(sp):
                shutil.rmtree(sp, ignore_errors=True)

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
            f'  cost={_cost(r):+5.2f}'
            f'  [+{self._fmt_dur(elapsed)}  ETA {eta.strftime("%H:%M")}]',
            flush=True)

    @staticmethod
    def _fmt_dur(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f'{m}m {s:02d}s'

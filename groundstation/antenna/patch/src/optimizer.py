# -*- coding: utf-8 -*-
"""Coverage optimizer for the single-feed corner-truncated RHCP patch.

Selects on WIDE-BEAM COVERAGE, not boresight gain: it rewards a large AR<=3 dB
elevation beamwidth, penalises the worst axial ratio over the 0-COVER_CONE cone,
holds a floor on gain across the cone, rewards radiation efficiency, and drives
resonance/match/handedness to spec. Sweeps a 2-D grid of the two coupled levers —
patch side W (resonance) × corner truncation (CP / AR) — at a coarse screen NrTS,
then confirms the best W-per-truncation at full fidelity. Reuses the parallel-pool
machinery (one persistent ProcessPoolExecutor, dynamic idle-core threads, timeout).
"""

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

import config
from src.metrics import failure_result
from src.params import PatchParams, default_params


# ── Search schedule (grid screen + two-tier confirm) ──────────────────────────
# The optimiser explores the two COUPLED resonance/AR levers — patch side W and the
# corner truncation — on ONE independent 2-D grid at a cheap SCREENING fidelity
# (config.NrTS_screen), then re-runs the best-W-per-truncation winners at full fidelity
# (config.NrTS_opt == NrTS_final). The 2-D grid (vs a sequential coordinate descent)
# navigates the W/truncation coupling: W sets resonance, truncation sets the CP mode-
# split, and the AR null is only centred on f_target when BOTH are right together. The
# single inset (match) and the board (locked for wide-beam coverage) stay at the seed.
# AR does NOT converge at the screen NrTS, so it is judged only at confirm. See config.GRID_*.


def _grid_dims() -> tuple:
    """(n_grid, n_confirm) — coarse-screen count and full-fidelity confirm count."""
    n_grid = len(config.GRID_W_FRAC) * len(config.GRID_TRUNC_MM)
    return n_grid, int(config.N_CONFIRM)


def n_opt() -> int:
    """Total optimisation FDTD runs (coarse grid + fine confirm)."""
    n_grid, n_conf = _grid_dims()
    return n_grid + n_conf


def phases_label() -> str:
    n_grid, n_conf = _grid_dims()
    return (f'GRID {len(config.GRID_W_FRAC)}W×{len(config.GRID_TRUNC_MM)}trunc={n_grid}'
            f'@{config.NrTS_screen // 1000}k  ->  CONFIRM {n_conf}@{config.NrTS_opt // 1000}k')


def resolve_workers(num_workers: int | None = None) -> int:
    """Resolve the parallel-worker count, capped by config.MAX_WORKERS."""
    nw = num_workers if num_workers is not None else config.num_workers
    nw = nw if nw and nw > 0 else (os.cpu_count() or 1)
    return min(nw, config.MAX_WORKERS)


def _sim_seconds(n_timesteps: int) -> float:
    """Rough wall-clock for one FDTD run on THIS host (~0.04 s/timestep).

    Calibrated to the optimiser's concurrent 4-thread sims (the host runs ~0.011
    s/step solo at 20 threads and slower when 5 sims share the machine). The old
    90 s / 40 000 steps (~0.00225 s/step) assumed a ~5-18x faster machine and made
    the ETA — and the PHASE_TIMEOUT comment — wildly optimistic. Display-only; the
    correctness-critical guard is config.PHASE_TIMEOUT_S.
    """
    return n_timesteps / 40000 * 1600


def estimate_seconds(num_workers: int | None = None) -> float:
    """Wall-clock estimate: coarse grid + fine confirm + the final high-fidelity sim."""
    par = resolve_workers(num_workers)
    n_grid, n_conf = _grid_dims()
    grid_waves = math.ceil(n_grid / par)
    conf_waves = math.ceil(n_conf / par)
    return (grid_waves * _sim_seconds(config.NrTS_screen)
            + conf_waves * _sim_seconds(config.NrTS_opt)
            + _sim_seconds(config.NrTS_final))


def _sweep_stale_temp_dirs():
    for d in glob.glob(os.path.join(tempfile.gettempdir(), 'rhcp_*')):
        shutil.rmtree(d, ignore_errors=True)


if _mp.parent_process() is None:
    atexit.register(_sweep_stale_temp_dirs)


def _cost(r) -> float:
    """Coverage cost — lower is better. Rewards AR<=3 dB beamwidth; penalises the
    worst AR over the cone, an under-floor gain, S11, resonance offset and a
    wrong-handed (LHCP) result. Replaces the old boresight-gain cost.

    A raw worker result already carries the coverage metrics (ar_bw_deg,
    ar_cone_dB, gain_cone_dBic, boresight ar_dB, rhcp, Dmax); failure_result()
    supplies safe sentinels so _cost never KeyErrors.
    """
    # Resonance penalty: a deadband (no penalty within ±F_RES_DEADBAND_MHZ — fab /
    # channel tolerance) then a strong linear ramp on a few-MHz scale. The OLD form
    # divided |Δf| by fc (250 MHz), so even a 16 MHz miss cost only ~0.06 and the
    # optimiser effectively ignored resonance — run 20260606_052114 kept a +16 MHz
    # design and DISCARDED an on-resonance arm=48.9 mm candidate by a 0.03 cost
    # margin. The FINAL selection uses the GENTLE F_RES_*_FINAL shaping (a tiebreaker,
    # not a driver) so on-target CP coverage decides — see config.F_RES_*_FINAL re: run #3,
    # where the sharp screen penalty wrongly crowned a beam-0° on-dip design. (The SCREEN
    # cost below keeps the sharp F_RES_* to shortlist on-resonance grid candidates.)
    df_MHz   = abs(r['f_res'] - config.f_target) / 1e6
    pen_freq = config.W_FREQ * max(0.0, df_MHz - config.F_RES_DEADBAND_FINAL_MHZ) \
        / config.F_RES_SCALE_FINAL_MHZ
    pen_s11  = config.W_MATCH * max(0.0, r['s11_dB'] + 10.0)
    # worst AR over the cone above AR_MAX_DB
    pen_ar   = config.W_AR_CONE * max(0.0, r.get('ar_cone_dB', 99.0) - config.AR_MAX_DB) \
        / config.AR_MAX_DB
    if not r.get('rhcp', True):
        # Hard gate: a wrong-handed (LHCP) candidate must NEVER win, even over a
        # badly off-spec RHCP. The soft W_CP·WRONG_HAND_PENALTY term alone is finite
        # (~3), so a clean LHCP (AR≈0, full beamwidth) could otherwise undercut an
        # unmatched RHCP whose pen_s11/pen_freq exceed 3. Add a dominating constant.
        pen_ar += config.W_CP * config.WRONG_HAND_PENALTY + 100.0
    # gain floor over the cone (penalise dropping below GAIN_FLOOR_DBIC)
    pen_gain = config.W_GAIN_FLOOR * max(
        0.0, config.GAIN_FLOOR_DBIC - r.get('gain_cone_dBic', -99.0)) / config.GAIN_FLOOR_DBIC
    # reward AR<=3 dB beamwidth, normalised to AR_BW_REF and capped at 1.0
    rew_bw = config.W_AR_BW * min(r.get('ar_bw_deg', 0.0) / config.AR_BW_REF, 1.0)
    # reward radiation efficiency (drive power INTO the patch, not the iso resistor);
    # saturates at ETA_RAD_REF so a good radiator isn't over-rewarded vs CP coverage.
    rew_eff = config.W_EFF * min(max(r.get('eta_rad', 0.0), 0.0) / config.ETA_RAD_REF, 1.0)
    return pen_freq + pen_s11 + pen_ar + pen_gain - rew_bw - rew_eff


def _screen_cost(r) -> float:
    """Cheap-fidelity ranking for the coarse grid: resonance + match (+ soft
    wrong-hand). The razor AR/beamwidth is NOT reliable at config.NrTS_screen, so it
    is EXCLUDED here and judged only at the full-fidelity confirm stage (by _cost).
    """
    df_MHz   = abs(r['f_res'] - config.f_target) / 1e6
    pen_freq = config.W_FREQ * max(0.0, df_MHz - config.F_RES_DEADBAND_MHZ) \
        / config.F_RES_SCALE_MHZ
    pen_s11  = config.W_MATCH * max(0.0, r['s11_dB'] + 10.0)
    pen_hand = 0.0 if r.get('rhcp', True) else 1.0   # soft: handedness noisy at coarse NrTS
    # radiation efficiency (Prad/P_acc) converges with the match at screen NrTS, and is
    # the dominant re-tune objective, so shortlist on it too (drive power into the patch).
    rew_eff  = config.W_EFF * min(max(r.get('eta_rad', 0.0), 0.0) / config.ETA_RAD_REF, 1.0)
    return pen_freq + pen_s11 + pen_hand - rew_eff


def _run_sim_worker(kw: dict) -> dict:
    """Top-level worker: build + run one single-feed CP FDTD sim in a child process.

    Returns the COVERAGE metrics the cost selects on (all at f_target): S11,
    f_res, boresight AR + handedness, AR<=3 beamwidth, worst AR over the cone,
    min gain over the cone, Dmax.
    """
    import os as _os
    n_threads = int(kw.get('num_threads', 1))
    _os.environ['OMP_NUM_THREADS'] = str(n_threads)
    import shutil as _shutil
    import tempfile as _tempfile
    import numpy as _np
    import config as _cfg
    from src.model import build_patch_sim as _build
    from src.metrics import (axial_ratio_db as _ar, cp_center_freq as _cf,
                             failure_result as _fail, s11_db as _s11db,
                             ar_beamwidth_deg as _bw, worst_ar_over_cone as _wc,
                             min_gain_over_cone as _mg, directivity_dbi as _ddbi,
                             radiation_efficiency as _eff)

    sp = _tempfile.mkdtemp(prefix=f'rhcp_{kw["sim_suffix"]}_')
    try:
        p = kw['p']
        FDTD, _CSX, port, nf2ff = _build(p, kw['NrTS'])
        FDTD.Run(sp, verbose=0, cleanup=True, numThreads=n_threads)

        # ── S11 / resonance at the MSL input ──
        f_eval = _np.concatenate([[_cfg.f_target],
                                  _np.linspace(max(100e6, _cfg.f_target - _cfg.fc),
                                               _cfg.f_target + _cfg.fc, 25)])
        port.CalcPort(sp, f_eval)
        s11_all = _s11db(port.uf_ref, port.uf_inc)
        s11_dB  = float(s11_all[0])
        f_res   = _cf(f_eval[1:], s11_all[1:])

        # ── coverage NF2FF over an elevation cone, AR sampled band-robust ──
        # AR is evaluated at f_target AND f_target ± AR_MARGIN_MHZ and selected on the
        # WORST value over that band, so a razor-thin AR null that drifts off f_target
        # (fab / εr spread / coarse→final convergence) cannot be selected — the defence
        # config.AR_MARGIN_MHZ documents. f_target is the FIRST frequency, so index 0 is
        # the operating point used for handedness / gain / Dmax. The θ grid is 2° to
        # match postproc, so the selected AR≤3 dB beamwidth equals the reported one.
        th = _np.arange(0.0, _cfg.COVER_CONE_DEG + 15.1, 2.0)   # 0..60 deg, 2° step
        ph = [0.0, 45.0, 90.0, 135.0]
        d_ar  = _cfg.AR_MARGIN_MHZ * 1e6
        f_ar  = [_cfg.f_target, _cfg.f_target - d_ar, _cfg.f_target + d_ar]
        res   = nf2ff.CalcNF2FF(sp, f_ar, theta=th, phi=ph, center=[0, 0, 1e-3])
        nf    = len(f_ar)

        # Peak directivity (dBi) + radiation efficiency from a coarse FULL-SPHERE call:
        # Dmax/Prad need the whole sphere (the cone call above only integrates 0..60°, so
        # its Prad — hence Dmax — is biased). openEMS Dmax is the LINEAR ratio → dBi via
        # _ddbi. η_rad = Prad / P_acc is dipole-validated; it rewards designs that actually
        # radiate (penalising dielectric / mismatch loss a good S11 alone can hide).
        res_f = nf2ff.CalcNF2FF(sp, [_cfg.f_target],
                                theta=_np.arange(0.0, 180.1, 6.0),
                                phi=_np.arange(0.0, 360.0, 30.0), center=[0, 0, 1e-3])
        Dmax  = float(_ddbi(res_f.Dmax[0]))              # at f_target, dBi
        P_acc = float(_np.real(port.P_acc[0]))          # f_eval[0] == f_target
        eta_rad = float(_eff(res_f.Prad[0], P_acc))

        # handedness at f_target; boresight AR = worst over the band (θ=2° near-axis ring)
        _, is_rhcp = _ar(res.E_cprh[0][1, :], res.E_cplh[0][1, :])
        ar0 = max(_ar(res.E_cprh[fi][1, :], res.E_cplh[fi][1, :])[0] for fi in range(nf))

        # AR per θ = worst over φ AND over the band. Gain per θ = worst (min) RHCP
        # partial directivity over φ at f_target, built from the RHCP component
        # |E_cprh| (NOT the total field E_norm) so the optimiser scores the SAME gain
        # the final run reports (postproc._coverage_cuts uses |E_cprh| likewise).
        E_rh = res.E_cprh[0]                             # RHCP component at f_target
        Emax = float(_np.max(res.E_norm[0]))            # total-field peak (broadside)
        ar_th, g_th = [], []
        for i in range(len(th)):
            j0 = 1 if i == 0 else i           # avoid degenerate on-axis CP split at θ=0
            ar_th.append(max(_ar(_np.array([res.E_cprh[fi][j0, k]]),
                                 _np.array([res.E_cplh[fi][j0, k]]))[0]
                             for fi in range(nf) for k in range(len(ph))))
            g_th.append(Dmax + 20.0 * _np.log10(
                min(abs(E_rh[i, k]) for k in range(len(ph))) / Emax + 1e-12))
        ar_th = _np.array(ar_th); g_th = _np.array(g_th)

        return {'s11_dB': s11_dB, 'f_res': f_res, 'ar_dB': float(ar0),
                'ar_bw_deg': float(_bw(th, ar_th)),
                'ar_cone_dB': float(_wc(th, ar_th, _cfg.COVER_CONE_DEG)),
                'gain_cone_dBic': float(_mg(th, g_th, _cfg.COVER_CONE_DEG)),
                'Dmax': Dmax, 'eta_rad': eta_rad, 'rhcp': bool(is_rhcp), 'ok': True}
    except Exception as exc:
        return {**_fail(), 'ar_bw_deg': 0.0, 'ar_cone_dB': 99.0,
                'gain_cone_dBic': -99.0, 'eta_rad': 0.0, '_exc': str(exc)}
    finally:
        if _os.path.exists(sp):
            _shutil.rmtree(sp, ignore_errors=True)


def _find_latest_results_json() -> str | None:
    cwd = os.getcwd()
    cands = glob.glob(os.path.join(cwd, 'RHCP_Patch_*', 'results.json'))
    return max(cands, key=os.path.getmtime) if cands else None


def _load_results_json(rjson_path: str) -> PatchParams:
    """Load a results.json into a PatchParams (missing fields take config seeds)."""
    with open(rjson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return PatchParams.from_dict(data)


class Optimizer:
    """Coverage optimizer — 2-D (W × truncation) grid screen + full-fidelity confirm.

    Stage GRID : a cheap-fidelity (config.NrTS_screen) 2-D grid over patch side W and
                 corner truncation — the two COUPLED levers that set resonance AND axial
                 ratio. Ranked by _screen_cost (resonance + match + efficiency; the razor
                 AR is not trustworthy this coarse). inset and board are fixed at the seed.
    Stage CONF : the best W per truncation (up to config.N_CONFIRM diverse candidates)
                 re-run at full fidelity (config.NrTS_opt); the best by the full coverage
                 _cost (incl. AR/beamwidth/efficiency) wins.
    """

    def __init__(self, p_init: PatchParams | None = None,
                 num_workers: int | None = None):
        self._p0          = p_init or default_params()
        self._log: list   = []
        self._n_done      = 0
        self._t_start     = None
        self._num_workers = resolve_workers(num_workers)
        self._pool        = None
        self.N_OPT        = n_opt()
        # fix the board at the seed (clamped); it is locked for wide-beam coverage
        # (config.SUB_HW_*), so sub_hw is not swept by the optimiser.
        self._p0 = self._p0.with_(
            sub_hw_mm=min(max(self._p0.sub_hw_mm, config.SUB_HW_MIN), config.SUB_HW_MAX))

    def run(self) -> tuple:
        """Run the grid screen + confirm. Returns (best PatchParams, log)."""
        self._t_start = time.monotonic()
        try:
            return self._run_search()
        finally:
            self._shutdown_pool()

    def _grid_jobs(self, p0, NrTS):
        """Build the 2-D (W × corner-truncation) grid jobs at the given fidelity."""
        jobs = []
        for wf in config.GRID_W_FRAC:
            for tr in config.GRID_TRUNC_MM:
                pp = p0.with_(W_mm=p0.W_mm * wf, trunc_mm=tr)
                jobs.append((pp, self._mk_kw(pp, NrTS, f'G_W{pp.W_mm:.1f}_T{tr:.1f}')))
        return jobs

    def _run_search(self) -> tuple:
        p0 = self._p0
        # ── Stage GRID: coarse 2-D (W × truncation) screen ───────────────────
        print(f'\n=== Stage GRID: {len(config.GRID_W_FRAC)}×{len(config.GRID_TRUNC_MM)}'
              f' (W × truncation) screen @ NrTS={config.NrTS_screen} ===')
        self._run_batch('GRID', self._grid_jobs(p0, config.NrTS_screen), config.NrTS_screen)
        grid = [x for x in self._log if x['phase'] == 'GRID' and x.get('ok', True)]

        # best W per truncation by SCREEN cost (resonance + match + efficiency) → a
        # truncation-diverse confirm set (AR is judged only at the full-fidelity confirm)
        per_tr = []
        for tr in config.GRID_TRUNC_MM:
            col = [x for x in grid if abs(x['p'].trunc_mm - tr) < 1e-6]
            if col:
                per_tr.append(min(col, key=_screen_cost))
        per_tr.sort(key=_screen_cost)
        confirm = per_tr[:int(config.N_CONFIRM)]
        confirm_ps = [e['p'] for e in confirm] or [p0]   # fall back to seed if grid all failed
        self.N_OPT = self._n_done + len(confirm_ps)      # actual total (grid recorded + confirms)
        if not confirm:
            print('  ! GRID produced no usable candidate — confirming the seed dims.')
        else:
            print('  GRID winners (best W per truncation, by resonance+match+η):')
            for e in confirm:
                print(f'    W={e["p"].W_mm:.2f}  trunc={e["p"].trunc_mm:.2f}  '
                      f'f_res {e["f_res"]/1e6:.1f} MHz  S11 {e["s11_dB"]:.1f} dB  '
                      f'screen {_screen_cost(e):.2f}')

        # ── Stage CONFIRM: full-fidelity re-run; full coverage _cost decides ──
        print(f'\n=== Stage CONFIRM: {len(confirm_ps)} candidate(s) @ NrTS={config.NrTS_opt} ===')
        cjobs = [(pp, self._mk_kw(pp, config.NrTS_opt, f'C_W{pp.W_mm:.1f}_T{pp.trunc_mm:.1f}'))
                 for pp in confirm_ps]
        self._run_batch('CONF', cjobs, config.NrTS_opt)
        conf = [x for x in self._log if x['phase'] == 'CONF']
        ok_conf = [x for x in conf if x.get('ok', True)]   # prefer successful confirms
        best = min(ok_conf or conf, key=_cost) if conf else {'p': p0}
        p = best['p']

        total = time.monotonic() - self._t_start
        print(f'\n  {"="*70}')
        print(f'  OPTIMISATION COMPLETE — {self._fmt_dur(total)}'
              f'  ({total/max(self._n_done,1):.0f}s/sim avg, {self._n_done} sims)')
        print(f'  Best: W={p.W_mm:.2f}  trunc={p.trunc_mm:.2f}  '
              f'inset={p.inset_y_mm:.2f}  GP={p.sub_hw_mm*2:.1f} mm')
        if conf:
            print(f'        f_res {best["f_res"]/1e6:.2f} MHz  S11 {best["s11_dB"]:.1f} dB  '
                  f'AR {best["ar_dB"]:.1f} dB  AR≤3 BW {best.get("ar_bw_deg", 0):.0f}°  '
                  f'cost {_cost(best):+.2f}')
        print(f'  {"="*70}')
        return p, self._log

    # ── helpers ───────────────────────────────────────────────────────
    def _mk_kw(self, p, NrTS, suffix):
        return {'p': p, 'NrTS': int(NrTS), 'sim_suffix': suffix, 'num_threads': 1}

    def _ensure_pool(self):
        if self._pool is None:
            self._pool = ProcessPoolExecutor(max_workers=self._num_workers)
        return self._pool

    def _rebuild_pool(self):
        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
        self._pool = ProcessPoolExecutor(max_workers=self._num_workers)

    def _shutdown_pool(self):
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None

    def _run_batch(self, phase, jobs: list, NrTS: int):
        """Submit a batch of sims in parallel; record results as they arrive.

        jobs: list of (PatchParams, kw_dict). Reuses one persistent pool; idle
        cores on under-filled waves become extra openEMS threads; a per-batch
        timeout records stragglers as failures and rebuilds the pool. NrTS is the
        batch fidelity (display/ETA only; each job already carries its own NrTS).
        """
        cores      = os.cpu_count() or self._num_workers
        concurrent = min(len(jobs), self._num_workers)
        n_threads  = max(1, cores // concurrent)
        for _, kw in jobs:
            kw['num_threads'] = n_threads

        waves   = math.ceil(len(jobs) / self._num_workers)
        t_phase = waves * _sim_seconds(NrTS)
        eta     = _dt.datetime.now() + _dt.timedelta(seconds=t_phase)
        print(f'  Phase {phase}: {len(jobs)} sims, {self._num_workers} workers, '
              f'{n_threads} thread(s)/sim  ->  ~{self._fmt_dur(t_phase)} '
              f'(ETA {eta.strftime("%H:%M")})', flush=True)

        pool    = self._ensure_pool()
        fut_map = {pool.submit(_run_sim_worker, kw): (p, kw['sim_suffix'])
                   for p, kw in jobs}
        pending = set(fut_map)
        try:
            for fut in as_completed(fut_map, timeout=config.PHASE_TIMEOUT_S):
                pending.discard(fut)
                p, suffix = fut_map[fut]
                try:
                    r = fut.result()
                    if not r.get('ok', True) and '_exc' in r:
                        print(f'  !! Sim {suffix} failed: {r["_exc"]}')
                except Exception as exc:
                    print(f'  !! Sim {suffix} raised: {exc}')
                    r = {**failure_result(), 'ar_bw_deg': 0.0, 'ar_cone_dB': 99.0,
                         'gain_cone_dBic': -99.0}
                self._record(phase, p, r)
        except _FuturesTimeout:
            for fut in pending:
                p, suffix = fut_map[fut]
                print(f'  !! Sim {suffix} timed out after {config.PHASE_TIMEOUT_S}s'
                      f' — recorded as failure', flush=True)
                self._record(phase, p, {**failure_result(), 'ar_bw_deg': 0.0,
                                        'ar_cone_dB': 99.0, 'gain_cone_dBic': -99.0})
            self._rebuild_pool()

    def _record(self, phase, p, r):
        self._n_done += 1
        entry = {'phase': phase, 'p': p, **r}
        self._log.append(entry)
        status  = 'RHCP' if r.get('rhcp', True) else 'LHCP'
        elapsed = time.monotonic() - self._t_start
        rem     = (self.N_OPT - self._n_done) * elapsed / max(self._n_done, 1)
        eta     = _dt.datetime.now() + _dt.timedelta(seconds=rem)
        df      = (r['f_res'] - config.f_target) / 1e6
        print(
            f'  [{self._n_done:2d}/{self.N_OPT}  P{phase}]'
            f'  W={p.W_mm:5.1f}  trunc={p.trunc_mm:4.1f}  ins={p.inset_y_mm:4.1f}'
            f'  gp={p.sub_hw_mm*2:5.1f}'
            f'  ->  S11={r["s11_dB"]:+5.1f}  f={r["f_res"]/1e6:.1f}({df:+.0f})'
            f'  AR={r["ar_dB"]:4.1f} {status}  BW={r.get("ar_bw_deg",0):3.0f}'
            f'  D={r["Dmax"]:+4.1f}dBi  η={r.get("eta_rad",0)*100:4.1f}%  cost={_cost(entry):+5.2f}'
            f'  [+{self._fmt_dur(elapsed)} ETA {eta.strftime("%H:%M")}]',
            flush=True)

    @staticmethod
    def _fmt_dur(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f'{m}m {s:02d}s'

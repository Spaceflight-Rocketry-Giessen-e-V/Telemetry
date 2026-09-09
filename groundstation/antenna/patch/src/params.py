# -*- coding: utf-8 -*-
"""Geometry parameter object for the single-feed corner-truncated RHCP patch.

A single frozen dataclass carries the whole design so it can be threaded through
``build_patch_sim`` / the optimiser / post-processing without long positional
signatures, and pickled cleanly into ``ProcessPoolExecutor`` workers (a frozen
dataclass of plain floats pickles trivially across the spawn start method).

RHCP comes from truncating two diagonally-opposite corners of a near-square patch
(the chamfer splits the two degenerate modes 90° apart at f_target), fed by ONE
inset microstrip — no branch-line coupler, no isolated-port resistor (which dumped
~64 % of accepted power).
"""

from __future__ import annotations

from dataclasses import dataclass, replace, asdict, fields

import config


@dataclass(frozen=True)
class PatchParams:
    """Full geometry of the single-feed corner-truncated RHCP patch (lengths in mm)."""

    # ── near-square patch ─────────────────────────────────────────────
    W_mm:        float                  # patch side length

    # ── CP perturbation ───────────────────────────────────────────────
    trunc_mm:    float                  # corner truncation (chamfer leg) on two
                                        # diagonally-opposite corners — sets the CP

    # ── single inset feed (bottom −y edge centre) ─────────────────────
    inset_y_mm:  float                  # inset depth of the feed notch

    # ── board ─────────────────────────────────────────────────────────
    sub_hw_mm:   float                  # ground/substrate half-width (smaller → broader beam)

    # ── constructors / helpers ────────────────────────────────────────
    @classmethod
    def from_dict(cls, d: dict) -> "PatchParams":
        """Build from a (possibly partial) dict; missing fields take config seeds."""
        seed = default_params()
        known = {f.name for f in fields(cls)}
        overrides = {k: float(v) for k, v in d.items() if k in known}
        return replace(seed, **overrides)

    def with_(self, **changes) -> "PatchParams":
        """Return a copy with the given fields replaced (one-field sweeps)."""
        return replace(self, **{k: float(v) for k, v in changes.items()})

    def to_dict(self) -> dict:
        return asdict(self)


def default_params() -> PatchParams:
    """Seed geometry from the analytical / synthesis values in config.py."""
    return PatchParams(
        W_mm        = config.W_CP_INIT,
        trunc_mm    = config.TRUNC_INIT,
        inset_y_mm  = config.INSET_Y,
        sub_hw_mm   = config.SUB_HW_DEFAULT,
    )

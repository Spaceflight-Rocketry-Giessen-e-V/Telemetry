# -*- coding: utf-8 -*-
"""Geometry parameter object for the flat dual-feed (branch-line coupler) RHCP patch.

A single frozen dataclass carries the whole design so it can be threaded through
``build_full_sim`` / the optimiser / post-processing without long positional
signatures, and pickled cleanly into ``ProcessPoolExecutor`` workers (a frozen
dataclass of plain floats pickles trivially across the spawn start method).

Replaces the old ``(delta_mm, y_inset_mm, W_patch, sub_hw_mm)`` positional tuple
of the truncated-corner single-feed design.  See docs/migration-plan.md §0.
"""

from __future__ import annotations

from dataclasses import dataclass, replace, asdict, fields

import config


@dataclass(frozen=True)
class PatchParams:
    """Full geometry of the flat dual-feed RHCP patch (all lengths in mm)."""

    # ── square patch ──────────────────────────────────────────────────
    W_mm:        float                  # square patch side length

    # ── branch-line (90° hybrid) coupler ──────────────────────────────
    cpl_arm_mm:  float                  # arm length (≈ λg/4)
    cpl_w50_mm:  float                  # 50 Ω line width   (shunt arms + I/O)
    cpl_w35_mm:  float                  # 35.36 Ω line width (Z0/√2 through arms)

    # ── feed routing (coupler outputs → patch) ────────────────────────
    inset_x_mm:  float                  # inset depth of the x-edge feed
    inset_y_mm:  float                  # inset depth of the y-edge feed

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
        W_mm        = config.W_SQ_INIT,
        cpl_arm_mm  = config.CPL_ARM,
        cpl_w50_mm  = config.CPL_W50,
        cpl_w35_mm  = config.CPL_W35,
        inset_x_mm  = config.INSET_X,
        inset_y_mm  = config.INSET_Y,
        sub_hw_mm   = config.SUB_HW_DEFAULT,
    )

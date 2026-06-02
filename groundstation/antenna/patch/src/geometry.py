# -*- coding: utf-8 -*-
"""Patch antenna geometry: vertex calculations shared by the FDTD model and KiCad export."""

import numpy as np

SUBSTRATE_MM = 150.0  # ground plane / substrate edge length [mm]


def patch_vertices_sim(W: float, delta: float) -> list:
    """Six CCW vertices of the truncated-corner patch in sim coordinates.

    Sim coordinate origin is at the patch centre; Y is up.
    Removes the TR (+h,+h) and BL (-h,-h) corners with 45° cuts of leg delta.
    """
    h, d = W / 2, delta
    return [
        (-h,    -h + d),   # left edge at BL cut
        (-h + d, -h),      # bottom edge at BL cut
        ( h,    -h),       # BR corner (intact)
        ( h,     h - d),   # right edge at TR cut
        ( h - d,  h),      # top edge at TR cut
        (-h,     h),       # TL corner (intact)
    ]


def patch_vertices_array(W: float, delta: float) -> np.ndarray:
    """Return shape (2, 6) array (x-row, y-row) for openEMS AddPolygon."""
    return np.array(patch_vertices_sim(W, delta)).T


def to_kicad(x_sim: float, y_sim: float,
             substrate_mm: float = SUBSTRATE_MM) -> tuple:
    """Sim coords (patch-centre origin, Y-up) → KiCad coords (Y-down, (0,0) = board TL)."""
    cx = cy = substrate_mm / 2
    return cx + x_sim, cy - y_sim

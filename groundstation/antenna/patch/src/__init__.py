# -*- coding: utf-8 -*-
"""RHCP patch-antenna toolchain: FDTD model, optimizer, post-processing, exports.

Kept side-effect-free (no heavy imports) so `python -m src.kicad_export` and
the pure-numeric helpers load without pulling in openEMS / matplotlib.
"""

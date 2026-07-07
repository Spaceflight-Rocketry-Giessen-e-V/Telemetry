"""
ui.layout
---------
Rendering / placement layer for the modular dashboard.

:mod:`ui.layout.grid_math` is pure geometry (no DearPyGui). :class:`ui.layout.grid_engine.GridLayoutEngine`
turns a dashboard document (see :mod:`ui.layout.layout_store`) into mounted
widgets at computed pixel positions. The engine is deliberately thin and
config-driven: dashboards are defined in JSON and loaded at startup — there is
no runtime drag/resize editor in this version.
"""

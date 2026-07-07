"""
ui.core
-------
Framework-agnostic domain layer for the modular Ground Station GUI.

Nothing in this package touches layout or rendering — it holds the telemetry
bus, the main-thread pump, the mission clock, the widget base class, the widget
registry, and the service bundle handed to every widget. Everything that *does*
render lives in :mod:`ui.layout` and :mod:`ui.windows`.
"""

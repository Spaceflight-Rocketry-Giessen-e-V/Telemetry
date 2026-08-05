"""
acceleration_window.py
----------------------
Live acceleration chart with per-session statistics (min, max, current, per-sample
delta, median delta).

Modular widget: per-instance data and stats (no class-level singleton), namespaced
tags, subscribes to ``tele/acceleration`` and the shared plot-control topics. The
time axis uses each sample's mission-elapsed time. As in the original, a frozen
plot skips updates entirely (the sample is dropped, not buffered).
"""

import logging
import math
import statistics

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.windows.plot_base import PlotWidgetBase

log = logging.getLogger(__name__)


class AccelerationWindow(PlotWidgetBase):
    """Live acceleration chart with statistics strip."""

    TYPE_ID = "acceleration"
    DISPLAY_NAME = "Acceleration Plot"
    DEFAULT_CELLS = (6, 5)
    MIN_CELLS = (4, 4)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self.time_data: list[float] = []
        self.accel_data: list[float] = []
        self.delta_data: list[float] = []
        self.accel_min = self.accel_max = self.accel_current = None

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Acceleration"), color=(255, 255, 0))

        with dpg.plot(label="Acceleration vs Time", height=-104, width=-1, zoom_mod=1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=self.tag("xaxis"))
            with dpg.plot_axis(dpg.mvYAxis, label="Acceleration (g)", tag=self.tag("yaxis")):
                dpg.add_line_series([], [], tag=self.tag("series"), label="Acceleration", parent=self.tag("yaxis"))

        with dpg.group(horizontal=True):
            with dpg.group(horizontal=False):
                self._build_plot_controls()
            dpg.add_spacer(width=10)
            with dpg.group(horizontal=False):
                dpg.add_text("Min: 0 g", tag=self.tag("min"))
                dpg.add_text("Max: 0 g", tag=self.tag("max"))
            dpg.add_spacer(width=10)
            dpg.add_text("Current: 0 g", tag=self.tag("current"))
            with dpg.group(horizontal=False):
                dpg.add_text("Δ: 0 g", tag=self.tag("delta"))
                dpg.add_text("Median Δ: 0 g", tag=self.tag("median_delta"))

        self.subscribe(topics.tele("acceleration"), self._on_accel)
        self._subscribe_plot_control()

    def _on_accel(self, sample) -> None:
        if not self.active:
            return
        value = float(sample.value)
        if math.isnan(value) or math.isinf(value):
            log.warning("AccelerationWindow[%s]: dropping non-finite acceleration %r", self.iid, value)
            return

        self.time_data.append(sample.mission_t)
        self.accel_data.append(value)
        self.accel_current = value
        self.accel_min = value if self.accel_min is None else min(self.accel_min, value)
        self.accel_max = value if self.accel_max is None else max(self.accel_max, value)

        if len(self.accel_data) > 1:
            delta = value - self.accel_data[-2]
            self.delta_data.append(delta)
        else:
            delta = 0.0
        median_delta = statistics.median(self.delta_data) if self.delta_data else 0.0

        dpg.set_value(self.tag("series"), [self.time_data, self.accel_data])
        dpg.fit_axis_data(self.tag("xaxis"))
        dpg.fit_axis_data(self.tag("yaxis"))

        dpg.set_value(self.tag("min"), f"Min: {self.accel_min:.2f} g")
        dpg.set_value(self.tag("max"), f"Max: {self.accel_max:.2f} g")
        dpg.set_value(self.tag("current"), f"Current: {self.accel_current:.2f} g")
        dpg.set_value(self.tag("delta"), f"Δ: {delta:.2f} g")
        dpg.set_value(self.tag("median_delta"), f"Median Δ: {median_delta:.2f} g")

    def _clear(self) -> None:
        self.time_data.clear()
        self.accel_data.clear()
        self.delta_data.clear()
        self.accel_min = self.accel_max = self.accel_current = None
        dpg.set_value(self.tag("series"), [[], []])
        dpg.set_value(self.tag("min"), "Min: 0 g")
        dpg.set_value(self.tag("max"), "Max: 0 g")
        dpg.set_value(self.tag("current"), "Current: 0 g")
        dpg.set_value(self.tag("delta"), "Δ: 0 g")
        dpg.set_value(self.tag("median_delta"), "Median Δ: 0 g")

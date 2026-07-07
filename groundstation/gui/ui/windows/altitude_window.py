"""
altitude_window.py
------------------
Live dual-source altitude chart with per-session statistics.

Two independent series — barometric (pressure) and GNSS altitude — each with its
own min/max/current strip. Modular widget: all data and stats are per-instance
(no more class-level singleton state), tags are namespaced, and it subscribes to
``tele/height_pressure`` / ``tele/height_gnss`` plus the shared plot-control
topics. The time axis uses each sample's mission-elapsed time.
"""

import logging
import math

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.windows.plot_base import PlotWidgetBase

log = logging.getLogger(__name__)


class AltitudeWindow(PlotWidgetBase):
    """Live dual-source altitude chart with statistics strips."""

    TYPE_ID = "altitude"
    DISPLAY_NAME = "Altitude Plot"
    DEFAULT_CELLS = (6, 5)
    MIN_CELLS = (4, 4)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self.t_pressure: list[float] = []
        self.t_gnss: list[float] = []
        self.alt_pressure: list[float] = []
        self.alt_gnss: list[float] = []
        self.p_min = self.p_max = self.p_cur = None
        self.g_min = self.g_max = self.g_cur = None

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Altitude"), color=(255, 255, 0))

        with dpg.plot(label="Altitude vs Time", height=-80, width=-1, zoom_mod=1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=self.tag("xaxis"))
            with dpg.plot_axis(dpg.mvYAxis, label="Altitude (m)", tag=self.tag("yaxis")):
                dpg.add_line_series([], [], tag=self.tag("series_p"), label="Pressure Alt", parent=self.tag("yaxis"))
                dpg.add_line_series([], [], tag=self.tag("series_g"), label="GNSS Alt", parent=self.tag("yaxis"))

        with dpg.group(horizontal=True):
            with dpg.group(horizontal=False):
                self._build_plot_controls()
            dpg.add_spacer(width=10)
            with dpg.group(horizontal=False):
                dpg.add_text("Pressure", color=(180, 200, 255))
                dpg.add_text("Min: 0 m", tag=self.tag("p_min"))
                dpg.add_text("Max: 0 m", tag=self.tag("p_max"))
                dpg.add_text("Cur: 0 m", tag=self.tag("p_cur"))
            dpg.add_spacer(width=10)
            with dpg.group(horizontal=False):
                dpg.add_text("GNSS", color=(180, 255, 180))
                dpg.add_text("Min: 0 m", tag=self.tag("g_min"))
                dpg.add_text("Max: 0 m", tag=self.tag("g_max"))
                dpg.add_text("Cur: 0 m", tag=self.tag("g_cur"))

        self.subscribe(topics.tele("height_pressure"), lambda s: self._update("pressure", s))
        self.subscribe(topics.tele("height_gnss"), lambda s: self._update("gnss", s))
        self._subscribe_plot_control()

    def _update(self, source: str, sample) -> None:
        if not self.active:
            return
        value = float(sample.value)
        if math.isnan(value) or math.isinf(value):
            log.warning("AltitudeWindow[%s]: dropping non-finite %s altitude %r", self.iid, source, value)
            return
        t = sample.mission_t

        if source == "pressure":
            self.t_pressure.append(t)
            self.alt_pressure.append(value)
            self.p_cur = value
            self.p_min = value if self.p_min is None else min(self.p_min, value)
            self.p_max = value if self.p_max is None else max(self.p_max, value)
            dpg.set_value(self.tag("series_p"), [self.t_pressure, self.alt_pressure])
            dpg.set_value(self.tag("p_min"), f"Min: {self.p_min:.1f} m")
            dpg.set_value(self.tag("p_max"), f"Max: {self.p_max:.1f} m")
            dpg.set_value(self.tag("p_cur"), f"Cur: {self.p_cur:.1f} m")
        else:
            self.t_gnss.append(t)
            self.alt_gnss.append(value)
            self.g_cur = value
            self.g_min = value if self.g_min is None else min(self.g_min, value)
            self.g_max = value if self.g_max is None else max(self.g_max, value)
            dpg.set_value(self.tag("series_g"), [self.t_gnss, self.alt_gnss])
            dpg.set_value(self.tag("g_min"), f"Min: {self.g_min:.1f} m")
            dpg.set_value(self.tag("g_max"), f"Max: {self.g_max:.1f} m")
            dpg.set_value(self.tag("g_cur"), f"Cur: {self.g_cur:.1f} m")

        dpg.fit_axis_data(self.tag("xaxis"))
        dpg.fit_axis_data(self.tag("yaxis"))

    def _clear(self) -> None:
        self.t_pressure.clear(); self.t_gnss.clear()
        self.alt_pressure.clear(); self.alt_gnss.clear()
        self.p_min = self.p_max = self.p_cur = None
        self.g_min = self.g_max = self.g_cur = None
        dpg.set_value(self.tag("series_p"), [[], []])
        dpg.set_value(self.tag("series_g"), [[], []])
        for suffix in ("p_min", "g_min"):
            dpg.set_value(self.tag(suffix), "Min: 0 m")
        for suffix in ("p_max", "g_max"):
            dpg.set_value(self.tag(suffix), "Max: 0 m")
        for suffix in ("p_cur", "g_cur"):
            dpg.set_value(self.tag(suffix), "Cur: 0 m")

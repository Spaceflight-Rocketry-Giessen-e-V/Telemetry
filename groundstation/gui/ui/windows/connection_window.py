"""
connection_window.py
--------------------
Connection-quality (RSSI) progress bar with a weak-signal warning and a
time-since-last-packet readout.

Modular widget: subscribes to ``tele/rssi`` and ``tele/time_since_last_packet``,
and to ``settings/connection/changed`` for live threshold refresh. Its bar
colour theme is created per-instance and deleted on teardown.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class ConnectionWindow(Widget):
    """Connection-quality widget driven by the telemetry bus."""

    TYPE_ID = "connection"
    DISPLAY_NAME = "Connection Quality"
    DEFAULT_CELLS = (3, 3)
    MIN_CELLS = (2, 2)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self._read_thresholds()
        self._bar_theme: int | None = None
        self._bar_color: int | None = None

    def _read_thresholds(self) -> None:
        conn = self.ctx.settings.data.get("connection", {})
        self.rssi_min = int(self.config.get("rssi_min", conn.get("rssi_min", -110)))
        self.rssi_max = int(self.config.get("rssi_max", conn.get("rssi_max", -30)))
        self.rssi_warn = int(self.config.get("rssi_warn", conn.get("rssi_warn", -90)))

    def build(self, width: int, height: int) -> None:
        rssi_start = (self.rssi_min + self.rssi_max) // 2
        fraction = self._fraction(rssi_start)

        dpg.add_text(self.config.get("title", "Connection Quality"), color=(255, 255, 0))
        dpg.add_progress_bar(default_value=fraction, width=-1, height=30, tag=self.tag("bar"))

        with dpg.group(horizontal=True):
            dpg.add_text(f"{rssi_start} dBm", tag=self.tag("label"))
            dpg.add_text("⚠ WEAK SIGNAL", tag=self.tag("warning"), color=(255, 0, 0, 255))

        dpg.add_spacer(height=10)
        with dpg.group(horizontal=False):
            dpg.add_text(f"Min:  {self.rssi_min} dBm", tag=self.tag("min"))
            dpg.add_text(f"Warn: {self.rssi_warn} dBm", tag=self.tag("warn"))
            dpg.add_text(f"Max:  {self.rssi_max} dBm", tag=self.tag("max"))

        dpg.add_spacer(height=6)
        dpg.add_separator()
        dpg.add_text("Time since last packet: 0 ms", tag=self.tag("delay"))

        with dpg.theme() as self._bar_theme:
            with dpg.theme_component(dpg.mvProgressBar):
                self._bar_color = dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (0, 255, 0, 255))
        dpg.bind_item_theme(self.tag("bar"), self._bar_theme)

        dpg.hide_item(self.tag("warning"))

        self.subscribe(topics.tele("rssi"), self._on_rssi)
        self.subscribe(topics.tele("time_since_last_packet"), self._on_delay)
        self.subscribe(topics.settings_changed("connection"), lambda _=None: self.on_config_changed(self.config))

    def _on_rssi(self, sample) -> None:
        rssi = int(sample.value)
        clamped = max(self.rssi_min, min(rssi, self.rssi_max))
        fraction = self._fraction(clamped)

        dpg.set_value(self.tag("bar"), fraction)
        dpg.set_value(self.tag("label"), f"{clamped} dBm")
        self._update_bar_color(fraction)

        if clamped <= self.rssi_warn:
            dpg.show_item(self.tag("warning"))
        else:
            dpg.hide_item(self.tag("warning"))

    def _on_delay(self, sample) -> None:
        if dpg.does_item_exist(self.tag("delay")):
            dpg.set_value(self.tag("delay"), f"Time since last packet: {sample.value} ms")

    def _fraction(self, rssi: int) -> float:
        span = self.rssi_max - self.rssi_min
        return (rssi - self.rssi_min) / span if span else 0.0

    def _update_bar_color(self, fraction: float) -> None:
        if fraction < 0.5:
            r, g = 255, int(510 * fraction)
        else:
            r, g = int(255 - (fraction - 0.5) * 510), 255
        if self._bar_color is not None:
            dpg.set_value(self._bar_color, (r, g, 0, 255))

    def on_config_changed(self, config: dict) -> None:
        super().on_config_changed(config)
        self._read_thresholds()
        if dpg.does_item_exist(self.tag("min")):
            dpg.set_value(self.tag("min"), f"Min:  {self.rssi_min} dBm")
            dpg.set_value(self.tag("warn"), f"Warn: {self.rssi_warn} dBm")
            dpg.set_value(self.tag("max"), f"Max:  {self.rssi_max} dBm")

    def destroy(self) -> None:
        # The bar theme lives outside the root child_window, so delete it explicitly.
        if self._bar_theme is not None and dpg.does_item_exist(self._bar_theme):
            dpg.delete_item(self._bar_theme)
        self._bar_theme = None
        super().destroy()

"""
battery_window.py
-----------------
Battery voltage progress bar with a critical-voltage warning indicator.

Modular widget: subscribes to ``tele/battery_voltage`` for live values and to
``settings/battery/changed`` for live threshold refresh. All DPG tags are
per-instance (via :py:meth:`Widget.tag`), so any number of battery widgets can
coexist — e.g. one per battery pack.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class BatteryWindow(Widget):
    """Battery-status widget driven by the telemetry bus."""

    TYPE_ID = "battery"
    DISPLAY_NAME = "Battery Voltage"
    DEFAULT_CELLS = (3, 3)
    MIN_CELLS = (2, 2)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self._read_thresholds()

    def _read_thresholds(self) -> None:
        bat = self.ctx.settings.data.get("battery", {})
        self.v_min = float(self.config.get("voltage_min", bat.get("voltage_min", 5.4)))
        self.v_max = float(self.config.get("voltage_max", bat.get("voltage_max", 8.4)))
        self.v_crit = float(self.config.get("voltage_critical", bat.get("voltage_critical", 5.6)))

    def build(self, width: int, height: int) -> None:
        title = self.config.get("title", "Battery Status")
        dpg.add_text(title, color=(255, 255, 0))
        dpg.add_progress_bar(default_value=1.0, width=-1, height=30, tag=self.tag("bar"))

        with dpg.group(horizontal=True):
            dpg.add_text(f"{self.v_max:.2f} V", tag=self.tag("label"))
            dpg.add_text("⚠ UNDERVOLTAGE", tag=self.tag("warning"), color=(255, 0, 0, 255))

        dpg.add_spacer(height=10)
        with dpg.group(horizontal=False):
            dpg.add_text(f"Min:      {self.v_min:.2f} V", tag=self.tag("min"))
            dpg.add_text(f"Critical: {self.v_crit:.2f} V", tag=self.tag("crit"))
            dpg.add_text(f"Max:      {self.v_max:.2f} V", tag=self.tag("max"))

        dpg.hide_item(self.tag("warning"))

        self.subscribe(topics.tele("battery_voltage"), self._on_voltage)
        self.subscribe(topics.settings_changed("battery"), lambda _=None: self.on_config_changed(self.config))

    def _on_voltage(self, sample) -> None:
        voltage = float(sample.value)
        clamped = max(self.v_min, min(voltage, self.v_max))
        span = self.v_max - self.v_min
        fraction = (clamped - self.v_min) / span if span else 0.0

        dpg.set_value(self.tag("bar"), fraction)
        dpg.set_value(self.tag("label"), f"{clamped:.2f} V")

        if clamped <= self.v_crit:
            dpg.show_item(self.tag("warning"))
            log.warning("BatteryWindow[%s]: undervoltage — %.2f V (crit %.2f V)", self.iid, clamped, self.v_crit)
        else:
            dpg.hide_item(self.tag("warning"))

    def on_config_changed(self, config: dict) -> None:
        super().on_config_changed(config)
        self._read_thresholds()
        if dpg.does_item_exist(self.tag("min")):
            dpg.set_value(self.tag("min"), f"Min:      {self.v_min:.2f} V")
            dpg.set_value(self.tag("crit"), f"Critical: {self.v_crit:.2f} V")
            dpg.set_value(self.tag("max"), f"Max:      {self.v_max:.2f} V")

"""
battery_window.py
-----------------
Battery voltage progress bar with a critical-voltage warning indicator.

Thresholds are read from SettingsManager once at draw time and stored as
instance attributes. They do not update at runtime unless the UI is rebuilt.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.settings_manager import settings

log = logging.getLogger(__name__)


class BatteryWindow:
    """Renders a battery-status widget and handles voltage updates."""

    def __init__(self):
        bat = settings.data.get("battery", {})
        self.v_min = float(bat.get("voltage_min", 5.4))
        self.v_max = float(bat.get("voltage_max", 8.4))
        self.v_crit = float(bat.get("voltage_critical", 5.6))

        self._tag_bar = "battery_bar"
        self._tag_label = "battery_label"
        self._tag_warning = "battery_warning"
        self._tag_min = "battery_min"
        self._tag_crit = "battery_critical"
        self._tag_max = "battery_max"

        log.debug("BatteryWindow: thresholds min=%.2f crit=%.2f max=%.2f",
                  self.v_min, self.v_crit, self.v_max)

    def draw_ui(self, window_width: int = 300, window_height: int = 200) -> None:
        """Create the battery child-window. Call once during UI construction."""
        log.debug("BatteryWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(label="Battery", width=window_width, height=window_height):
            dpg.add_text("Battery Status")
            dpg.add_progress_bar(default_value=1.0, width=-1, height=30, tag=self._tag_bar)

            with dpg.group(horizontal=True):
                dpg.add_text(f"{self.v_max:.2f} V", tag=self._tag_label)
                dpg.add_text("UNDERVOLTAGE", tag=self._tag_warning, color=(255, 0, 0, 255))

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=False):
                dpg.add_text(f"Min:      {self.v_min:.2f} V", tag=self._tag_min)
                dpg.add_text(f"Critical: {self.v_crit:.2f} V", tag=self._tag_crit)
                dpg.add_text(f"Max:      {self.v_max:.2f} V", tag=self._tag_max)

        dpg.hide_item(self._tag_warning)

    def update_voltage(self, voltage: float) -> None:
        """
        Update the progress bar and warning indicator for a new voltage reading.

        The voltage is clamped to [v_min, v_max] before display. The
        UNDERVOLTAGE warning is shown when the value falls at or below v_crit.
        """
        clamped = max(self.v_min, min(voltage, self.v_max))
        span = self.v_max - self.v_min
        fraction = (clamped - self.v_min) / span if span else 0.0

        dpg.set_value(self._tag_bar, fraction)
        dpg.set_value(self._tag_label, f"{clamped:.2f} V")

        if clamped <= self.v_crit:
            dpg.show_item(self._tag_warning)
            log.warning("BatteryWindow: undervoltage — %.2f V (critical: %.2f V)", clamped, self.v_crit)
        else:
            dpg.hide_item(self._tag_warning)

    def reload(self) -> None:
        """Re-read thresholds from settings and refresh the static labels (post-save)."""
        bat = settings.data.get("battery", {})
        self.v_min = float(bat.get("voltage_min", 5.4))
        self.v_max = float(bat.get("voltage_max", 8.4))
        self.v_crit = float(bat.get("voltage_critical", 5.6))
        if dpg.does_item_exist(self._tag_min):
            dpg.set_value(self._tag_min, f"Min:      {self.v_min:.2f} V")
            dpg.set_value(self._tag_crit, f"Critical: {self.v_crit:.2f} V")
            dpg.set_value(self._tag_max, f"Max:      {self.v_max:.2f} V")
        log.debug("BatteryWindow: thresholds reloaded min=%.2f crit=%.2f max=%.2f",
                  self.v_min, self.v_crit, self.v_max)

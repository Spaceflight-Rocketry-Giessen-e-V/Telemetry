"""
connection_window.py
--------------------
Connection-quality (RSSI) progress bar with a weak-signal warning indicator.

Thresholds are read from SettingsManager once at draw time and stored as
instance attributes. They do not update at runtime unless the UI is rebuilt.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.settings_manager import settings

log = logging.getLogger(__name__)


class ConnectionWindow:
    """Renders a connection-quality widget and handles RSSI updates."""

    def __init__(self):
        conn = settings.data.get("connection", {})
        self.rssi_min = int(conn.get("rssi_min", -110))
        self.rssi_max = int(conn.get("rssi_max", -30))
        self.rssi_warn = int(conn.get("rssi_warn", -90))

        self._tag_bar = "rssi_bar"
        self._tag_label = "rssi_label"
        self._tag_warning = "rssi_warning"
        self._tag_min = "rssi_threshold_min"
        self._tag_warn = "rssi_threshold_warn"
        self._tag_max = "rssi_threshold_max"

        # Persistent progress-bar colour theme (created in draw_ui). Reused on
        # every update so we don't leak a theme item per packet.
        self._bar_theme: int | None = None
        self._bar_color: int | None = None

        log.debug("ConnectionWindow: thresholds min=%d warn=%d max=%d",
                  self.rssi_min, self.rssi_warn, self.rssi_max)

    def draw_ui(self, window_width: int = 200, window_height: int = 200) -> None:
        """Create the connection child-window. Call once during UI construction."""
        log.debug("ConnectionWindow: drawing UI (%dx%d)", window_width, window_height)

        rssi_start = (self.rssi_min + self.rssi_max) // 2
        fraction = self._fraction(rssi_start)

        with dpg.child_window(label="Connection", width=window_width, height=window_height):
            dpg.add_text("Connection Quality")
            dpg.add_progress_bar(default_value=fraction, width=-1, height=30, tag=self._tag_bar)

            with dpg.group(horizontal=True):
                dpg.add_text(f"{rssi_start} dBm", tag=self._tag_label)
                dpg.add_text("WEAK SIGNAL", tag=self._tag_warning, color=(255, 0, 0, 255))

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=False):
                dpg.add_text(f"Min:  {self.rssi_min} dBm", tag=self._tag_min)
                dpg.add_text(f"Warn: {self.rssi_warn} dBm", tag=self._tag_warn)
                dpg.add_text(f"Max:  {self.rssi_max} dBm", tag=self._tag_max)

        # One reusable theme for the bar colour; _update_bar_color mutates it.
        with dpg.theme() as self._bar_theme:
            with dpg.theme_component(dpg.mvProgressBar):
                self._bar_color = dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (0, 255, 0, 255))
        dpg.bind_item_theme(self._tag_bar, self._bar_theme)

        dpg.hide_item(self._tag_warning)

    def update_rssi(self, rssi: int) -> None:
        """
        Refresh the progress bar and warning indicator for a new RSSI reading.

        The value is clamped to [rssi_min, rssi_max]. The WEAK SIGNAL warning
        is shown when the value falls at or below rssi_warn.
        """
        clamped = max(self.rssi_min, min(rssi, self.rssi_max))
        fraction = self._fraction(clamped)

        dpg.set_value(self._tag_bar, fraction)
        dpg.set_value(self._tag_label, f"{clamped} dBm")
        self._update_bar_color(fraction)

        if clamped <= self.rssi_warn:
            dpg.show_item(self._tag_warning)
            log.warning("ConnectionWindow: weak signal — %d dBm (warn: %d dBm)", clamped, self.rssi_warn)
        else:
            dpg.hide_item(self._tag_warning)

    def _fraction(self, rssi: int) -> float:
        """Return the normalised position of *rssi* within [rssi_min, rssi_max]."""
        span = self.rssi_max - self.rssi_min
        return (rssi - self.rssi_min) / span if span else 0.0

    def _update_bar_color(self, fraction: float) -> None:
        """Apply a smooth red → yellow → green gradient to the progress bar."""
        if fraction < 0.5:
            r, g = 255, int(510 * fraction)
        else:
            r, g = int(255 - (fraction - 0.5) * 510), 255

        # Mutate the reusable theme colour instead of creating a new theme.
        if self._bar_color is not None:
            dpg.set_value(self._bar_color, (r, g, 0, 255))

    def reload(self) -> None:
        """Re-read thresholds from settings and refresh the static labels (post-save)."""
        conn = settings.data.get("connection", {})
        self.rssi_min = int(conn.get("rssi_min", -110))
        self.rssi_max = int(conn.get("rssi_max", -30))
        self.rssi_warn = int(conn.get("rssi_warn", -90))
        if dpg.does_item_exist(self._tag_min):
            dpg.set_value(self._tag_min, f"Min:  {self.rssi_min} dBm")
            dpg.set_value(self._tag_warn, f"Warn: {self.rssi_warn} dBm")
            dpg.set_value(self._tag_max, f"Max:  {self.rssi_max} dBm")
        log.debug("ConnectionWindow: thresholds reloaded min=%d warn=%d max=%d",
                  self.rssi_min, self.rssi_warn, self.rssi_max)

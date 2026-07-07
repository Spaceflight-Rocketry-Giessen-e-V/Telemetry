"""
location_window.py
------------------
GPS coordinate display in both decimal-degree and DMS notation.

Modular widget: subscribes to ``gps/fix`` (payload ``(lat, lon)``, published only
when both are present). Per-instance tags mean it can appear both standalone and
alongside a map with no collision.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class LocationWindow(Widget):
    """GPS coordinate table driven by the ``gps/fix`` bus topic."""

    TYPE_ID = "location"
    DISPLAY_NAME = "GPS Coordinates"
    DEFAULT_CELLS = (4, 2)
    MIN_CELLS = (3, 2)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self.lat = 0.0
        self.lon = 0.0

    @staticmethod
    def decimal_to_dms(decimal: float) -> tuple[int, int, float]:
        """Convert a decimal-degree coordinate to (deg, min, sec) magnitude (sign applied by caller)."""
        total_seconds = round(abs(decimal) * 3600, 2)
        degrees, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return int(degrees), int(minutes), seconds

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "GPS Coordinates"), color=(255, 255, 0))
        dpg.add_separator()

        with dpg.table(
                header_row=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
                row_background=True,
        ):
            dpg.add_table_column(label="Decimal")
            dpg.add_table_column(label="DMS")

            with dpg.table_row():
                dpg.add_text(f"Lat: {self.lat:.6f}", tag=self.tag("lat"))
                dpg.add_text('0°0\'0"', tag=self.tag("lat_dms"))
            with dpg.table_row():
                dpg.add_text(f"Lon: {self.lon:.6f}", tag=self.tag("lon"))
                dpg.add_text('0°0\'0"', tag=self.tag("lon_dms"))

        self.subscribe(topics.GPS_FIX, self._on_fix)

    def _on_fix(self, fix) -> None:
        lat, lon = fix
        self.lat, self.lon = lat, lon
        dpg.set_value(self.tag("lat"), f"Lat: {lat:.6f}")
        dpg.set_value(self.tag("lon"), f"Lon: {lon:.6f}")

        lat_d, lat_m, lat_s = self.decimal_to_dms(lat)
        lon_d, lon_m, lon_s = self.decimal_to_dms(lon)
        lat_h = "S" if lat < 0 else "N"
        lon_h = "W" if lon < 0 else "E"
        dpg.set_value(self.tag("lat_dms"), f"{lat_d}°{lat_m}'{lat_s:.2f}\" {lat_h}")
        dpg.set_value(self.tag("lon_dms"), f"{lon_d}°{lon_m}'{lon_s:.2f}\" {lon_h}")

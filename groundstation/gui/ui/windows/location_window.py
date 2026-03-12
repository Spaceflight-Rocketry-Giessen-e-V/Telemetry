"""
location_window.py
------------------
GPS coordinate display in both decimal-degree and DMS notation.

Multiple instances can coexist in the same DearPyGui context (e.g. one in
the Flight Data tab and one in the Map View tab) because every DPG item tag
is scoped to a per-instance unique ID.
"""

import itertools
import logging

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class LocationWindow:
    """Renders a GPS coordinate table and keeps it updated."""

    _id_counter = itertools.count()

    def __init__(self, instance_id: str | None = None):
        uid = instance_id if instance_id is not None else str(next(self._id_counter))

        self.lat = 0.0
        self.lon = 0.0

        self.lat_value_tag = f"loc_lat_value_{uid}"
        self.lon_value_tag = f"loc_lon_value_{uid}"
        self.lat_dms_value_tag = f"loc_lat_dms_{uid}"
        self.lon_dms_value_tag = f"loc_lon_dms_{uid}"

        log.debug("LocationWindow[%s]: initialised", uid)

    @staticmethod
    def decimal_to_dms(decimal: float) -> tuple[int, int, float]:
        """
        Convert a decimal-degree coordinate to ``(degrees, minutes, seconds)``.

        Works for both latitude and longitude. The caller is responsible for
        appending N/S or E/W suffixes as appropriate.
        """
        degrees = int(decimal)
        minutes_full = abs((decimal - degrees) * 60)
        minutes = int(minutes_full)
        seconds = (minutes_full - minutes) * 60
        return degrees, minutes, seconds

    def draw_ui(self, window_width: int = 300, window_height: int = 200) -> None:
        """
        Create the GPS coordinate child-window.

        Call once during UI construction. Subsequent updates go through
        :py:meth:`update_gps`.
        """
        log.debug("LocationWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(label="GPS", width=window_width, height=window_height):
            dpg.add_text("GPS Coordinates", color=(255, 255, 0))
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
                    dpg.add_text(f"Lat: {self.lat:.6f}", tag=self.lat_value_tag)
                    dpg.add_text('0°0\'0"', tag=self.lat_dms_value_tag)

                with dpg.table_row():
                    dpg.add_text(f"Lon: {self.lon:.6f}", tag=self.lon_value_tag)
                    dpg.add_text('0°0\'0"', tag=self.lon_dms_value_tag)

    def update_gps(self, lat: float, lon: float) -> None:
        """
        Refresh the coordinate display with a new GPS fix.

        Parameters
        ----------
        lat:
            Latitude in decimal degrees (negative = south).
        lon:
            Longitude in decimal degrees (negative = west).
        """
        self.lat, self.lon = lat, lon
        log.debug("LocationWindow: GPS updated — lat=%.6f, lon=%.6f", lat, lon)

        dpg.set_value(self.lat_value_tag, f"Lat: {lat:.6f}")
        dpg.set_value(self.lon_value_tag, f"Lon: {lon:.6f}")

        lat_d, lat_m, lat_s = self.decimal_to_dms(lat)
        lon_d, lon_m, lon_s = self.decimal_to_dms(lon)
        dpg.set_value(self.lat_dms_value_tag, f"{lat_d}°{lat_m}'{lat_s:.2f}\"")
        dpg.set_value(self.lon_dms_value_tag, f"{lon_d}°{lon_m}'{lon_s:.2f}\"")

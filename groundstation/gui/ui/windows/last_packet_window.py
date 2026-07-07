"""
last_packet_window.py
---------------------
Read-only system-status table showing the most recent value for every telemetry
field.

Modular widget: subscribes to ``packet/raw`` and formats each field itself (the
formatting that used to live in ``UIManager.update_*``). Per-instance tags mean
several of these can coexist. Rows with no value in a packet are left unchanged.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


def _fmt_onoff(v) -> str:
    return "ON" if v else "OFF"


class LastPacketWindow(Widget):
    """System-status table driven by the raw-packet bus topic."""

    TYPE_ID = "last_packet"
    DISPLAY_NAME = "System Status"
    DEFAULT_CELLS = (3, 6)
    MIN_CELLS = (3, 4)

    # (row label, packet field, tag suffix, formatter)
    ROWS: list[tuple] = [
        ("Acceleration", "acceleration", "accel", lambda v: f"{float(v):.2f} g"),
        ("Temperature", "temperature", "temperature", lambda v: f"{float(v):.1f} °C"),
        ("Subsystem", "subsystem_status", "subsystem", lambda v: format(int(v), "03b")),
        ("Flight Mode", "flight_mode", "flight_mode", _fmt_onoff),
        ("Low Power", "low_power_mode", "low_power", _fmt_onoff),
        ("Status Events", "status_events", "status_events", lambda v: str(v)),
        ("RSSI", "rssi", "rssi", lambda v: f"{v} dBm"),
        ("Packet Delay", "time_since_last_packet", "packet_delay", lambda v: f"{v} ms"),
        ("GNSS Height", "height_gnss", "gnss_height", lambda v: f"{v}"),
        ("Pressure Height", "height_pressure", "pressure_height", lambda v: f"{v}"),
        ("Latitude", "lat_gnss", "lat", lambda v: f"{v}"),
        ("Longitude", "lon_gnss", "lon", lambda v: f"{v}"),
        ("Battery Voltage", "battery_voltage", "battery_voltage", lambda v: f"{v} V"),
    ]

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "System Status"), color=(255, 255, 0))
        dpg.add_separator()

        with dpg.table(
                header_row=False,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
                row_background=True, resizable=True,
        ):
            dpg.add_table_column(label="Parameter", width_fixed=True)
            dpg.add_table_column(label="Value")

            defaults = {"accel": "0.00 g", "temperature": "0.0 °C", "subsystem": "000",
                        "flight_mode": "OFF", "low_power": "OFF", "status_events": "0",
                        "rssi": "0 dBm", "packet_delay": "0 ms", "gnss_height": "0 m",
                        "pressure_height": "0 m", "lat": "0.0", "lon": "0.0",
                        "battery_voltage": "0.0 V"}
            for label, _field, suffix, _fmt in self.ROWS:
                with dpg.table_row():
                    dpg.add_text(label)
                    dpg.add_text(defaults.get(suffix, "-"), tag=self.tag(suffix))

        self.subscribe(topics.PACKET_RAW, self._on_packet)

    def _on_packet(self, packet: dict) -> None:
        for _label, field, suffix, fmt in self.ROWS:
            if field in packet and packet[field] is not None:
                try:
                    dpg.set_value(self.tag(suffix), fmt(packet[field]))
                except (ValueError, TypeError):
                    dpg.set_value(self.tag(suffix), str(packet[field]))

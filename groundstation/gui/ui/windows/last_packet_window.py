"""
last_packet_window.py
---------------------
Read-only system-status table showing the most recent value for every
telemetry field.

Each field is a labelled row; values are updated in-place via the DPG item
tags stored in :attr:`system_status_tags`. UIManager calls these tags
directly via ``dpg.set_value`` on each incoming packet.
"""

import logging

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class LastPacketWindow:
    """Renders and manages the last-packet system-status table."""

    # Maps logical field name → unique DPG item tag.
    # UIManager uses these tags to push updated values.
    system_status_tags: dict[str, str] = {
        "accel": "accel_current_raw",
        "temperature": "temperature_value_raw",
        "subsystem": "subsystem_status_value_raw",
        "flight_mode": "flight_mode_value_raw",
        "low_power": "low_power_mode_value_raw",
        "status_events": "status_events_value_raw",
        "rssi": "rssi_value_raw",
        "packet_delay": "packet_delay_value_raw",
        "gnss_height": "gnss_height_value_raw",
        "pressure_height": "pressure_height_value_raw",
        "lat": "lat_value_raw",
        "lon": "lon_value_raw",
        "batteryVoltage": "battery_voltage_value_raw",
    }

    def __init__(self):
        log.debug("%s: initialised", self.__class__.__name__)

    def draw_ui(self, window_width: int = 300, window_height: int = 750) -> None:
        """
        Create the system-status child-window.

        Call once during UI construction. Values are subsequently updated
        through the tags in :attr:`system_status_tags`.
        """
        log.debug("LastPacketWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("System Status", color=(255, 255, 0))
            dpg.add_separator()

            with dpg.table(
                    header_row=False,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    row_background=True,
                    resizable=True,
            ):
                dpg.add_table_column(label="Parameter", width_fixed=True)
                dpg.add_table_column(label="Value")

                def row(label: str, tag: str, default: str) -> None:
                    with dpg.table_row():
                        dpg.add_text(label)
                        dpg.add_text(default, tag=tag)

                row("Acceleration", self.system_status_tags["accel"], "0.00 g")
                row("Temperature", self.system_status_tags["temperature"], "0.0 °C")
                row("Subsystem", self.system_status_tags["subsystem"], "000")
                row("Flight Mode", self.system_status_tags["flight_mode"], "OFF")
                row("Low Power", self.system_status_tags["low_power"], "OFF")
                row("Status Events", self.system_status_tags["status_events"], "0")
                row("RSSI", self.system_status_tags["rssi"], "0 dBm")
                row("Packet Delay", self.system_status_tags["packet_delay"], "0 ms")
                row("GNSS Height", self.system_status_tags["gnss_height"], "0 m")
                row("Pressure Height", self.system_status_tags["pressure_height"], "0 m")
                row("Latitude", self.system_status_tags["lat"], "0.0")
                row("Longitude", self.system_status_tags["lon"], "0.0")
                row("Battery Voltage", self.system_status_tags["batteryVoltage"], "0.0 V")

        log.debug("LastPacketWindow: %d rows rendered", len(self.system_status_tags))

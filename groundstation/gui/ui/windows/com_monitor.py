"""
com_monitor.py
--------------
Scrollable table that displays every received telemetry packet in full.

Each call to :py:meth:`add_row` appends one row to the DearPyGui table.
Numeric fields are formatted with precision appropriate to their meaning:
  - acceleration  → 4 decimal places
  - lat / lon     → 7 decimal places (~1 cm resolution)
  - all others    → 1 decimal place
"""

import logging

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class ComMonitor:
    """Renders the communication-monitor table and handles row insertion."""

    TABLE_TAG = "COM Monitor Table"

    # Column definitions: (display_label, data_dict_key)
    COLUMNS: list[tuple[str, str]] = [
        ("temperature > 80 C", "temperature"),
        ("subsystem_status", "subsystem_status"),
        ("flight_mode", "flight_mode"),
        ("low_power_mode", "low_power_mode"),
        ("status_events", "status_events"),
        ("acceleration", "acceleration"),
        ("height_pressure", "height_pressure"),
        ("height_gnss", "height_gnss"),
        ("lat_gnss", "lat_gnss"),
        ("lon_gnss", "lon_gnss"),
        ("battery_voltage", "battery_voltage"),
        ("rssi", "rssi"),
        ("time_since_last_pkt", "time_since_last_packet"),
    ]

    def __init__(self):
        self._row_count = 0
        log.debug("%s: initialised with %d columns", self.__class__.__name__, len(self.COLUMNS))

    def draw_ui(self) -> None:
        """
        Create the monitor child-window and its scrollable table.

        Call once during UI construction.
        """
        log.debug("ComMonitor: drawing UI")

        with dpg.child_window(label="Communication Monitor"):
            with dpg.table(
                    header_row=True,
                    tag=self.TABLE_TAG,
                    clipper=True,  # only renders visible rows — important for long sessions
                    scrollY=True,
            ):
                for label, _ in self.COLUMNS:
                    dpg.add_table_column(label=label)

        log.debug("ComMonitor: table created")

    def add_row(self, data: dict) -> None:
        """
        Append one telemetry packet as a new row in the monitor table.

        Missing keys are rendered as an empty string.
        """
        with dpg.table_row(parent=self.TABLE_TAG):
            for _, key in self.COLUMNS:
                value = data.get(key, "")

                if isinstance(value, float):
                    if key == "acceleration":
                        value = f"{value:.4f}"
                    elif key in ("lat_gnss", "lon_gnss"):
                        value = f"{value:.7f}"
                    else:
                        value = f"{value:.1f}"

                dpg.add_text(str(value))

        self._row_count += 1
        log.debug("ComMonitor: row %d appended", self._row_count)

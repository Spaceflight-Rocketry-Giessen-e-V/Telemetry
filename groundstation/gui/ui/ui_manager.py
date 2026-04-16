"""
ui_manager.py
-------------
Top-level UI orchestrator for the Ground Station GUI.

Responsibilities:
  - Bootstrap DearPyGui (context, viewport, main window).
  - Instantiate and lay out all sub-windows.
  - Receive decoded telemetry packets and fan them out to the appropriate
    sub-window update methods.
  - Provide a clean :py:meth:`shutdown` path.

Logging is configured once at import time via ``_configure_logging``. Any
module that calls ``logging.getLogger(__name__)`` will automatically write to
both the console and a rotating log file under ``logs/ground_station.log``.
"""

import logging
import logging.handlers
import os
import sys
import time
from typing import Any, Callable

import dearpygui.dearpygui as dpg

from ui.windows.location_window import LocationWindow
from ui.windows.altitude_window import AltitudeWindow
from ui.windows.battery_window import BatteryWindow
from ui.windows.map_view_window import MapViewWindow
from ui.windows.com_monitor import ComMonitor
from ui.windows.last_packet_window import LastPacketWindow
from ui.windows.com_monitor_controller import ComMonitorController
from ui.windows.flight_events_window import FlightEventWindow
from ui.windows.acceleration_window import AccelerationWindow
from ui.windows.commands_window import CommandsWindow
from ui.windows.connection_window import ConnectionWindow
from ui.windows.settings_window import SettingsWindow
from ui.windows.time_window import TimeWindow


def _configure_logging(
        log_dir: str = "logs",
        log_file: str = "ground_station.log",
        max_bytes: int = 5 * 1024 * 1024,
        backups: int = 5,
        level: int = logging.DEBUG,
) -> None:
    """
    Configure the root logger with two handlers:

    - **StreamHandler** (stdout) at INFO — human-readable progress during a flight.
    - **RotatingFileHandler** at DEBUG — full trace for post-flight analysis.
      Files rotate at *max_bytes*; *backups* older archives are kept.

    Call this once before any other module creates a logger.
    """
    os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=max_bytes,
        backupCount=backups,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    root.addHandler(console_handler)
    root.addHandler(file_handler)


_configure_logging()
log = logging.getLogger(__name__)

# Mission-elapsed-time reference point (seconds since process start).
_START_TIME = time.time()


def get_screen_resolution() -> tuple[int, int]:
    """
    Return the primary monitor's resolution as ``(width, height)`` in pixels.

    Uses the Win32 API on Windows and falls back to Tkinter on Linux/macOS.
    """
    if sys.platform.startswith("win"):
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h


class UIManager:
    """
    Owns all sub-window instances and wires them together.

    Telemetry data enters through :py:meth:`update_all`, which fans each
    field out to the relevant sub-window via focused ``update_*`` methods.
    Those methods can also be called individually for testing.
    """

    def __init__(self):
        log.info("UIManager: initialising sub-windows")

        # Two MapView and Location instances are created: one for the Flight
        # Data tab and a second for the dedicated Map View tab.
        self.map_view_window = MapViewWindow(instance_id="main")
        self.map_view_tab = MapViewWindow(instance_id="tab")
        self.location_window = LocationWindow(instance_id="main")
        self.location_tab = LocationWindow(instance_id="tab")

        self.altitude_window = AltitudeWindow()
        self.battery_window = BatteryWindow()
        self.com_monitor = ComMonitor()
        self.com_monitor_controller = ComMonitorController(self)
        self.last_packet_window = LastPacketWindow()
        self.flight_events_window = FlightEventWindow()
        self.accelerometer_window = AccelerationWindow()
        self.commands_window = CommandsWindow(receiver=self.com_monitor_controller)
        self.connection_window = ConnectionWindow()
        self.settings_window = SettingsWindow()
        self.time_window = TimeWindow()

        log.info("UIManager: all sub-windows initialised")

    def shutdown(self) -> None:
        """Tear down the DearPyGui context and exit cleanly."""
        log.info("UIManager: shutdown requested — destroying DPG context")
        dpg.destroy_context()

    def _draw_flight_data_ui(self) -> None:
        """
        Build the Flight Data tab layout.

        Four vertical columns:
          1. COM controller + commands + last-packet summary
          2. Flight events + battery + connection quality
          3. Altitude plot + acceleration plot
          4. Time clock + map + GPS coordinates
        """
        with dpg.group(horizontal=True):
            with dpg.group(horizontal=False):
                self.com_monitor_controller.draw_ui(300, 155)
                self.commands_window.draw_ui(300, 500)
                self.last_packet_window.draw_ui(300, 350)

            with dpg.group(horizontal=False):
                self.flight_events_window.draw_ui(400, 400)
                self.battery_window.draw_ui(400, 200)
                self.connection_window.draw_ui(400, 200)

            with dpg.group(horizontal=False):
                self.altitude_window.draw_ui(500, 400)
                self.accelerometer_window.draw_ui(500, 400)

            with dpg.group(horizontal=False):
                self.time_window.draw_ui(600, 125)
                self.map_view_window.draw_ui(600, 600)
                self.location_window.draw_ui(600, 125)

            with dpg.group(horizontal=False):
                pass

    def _draw_com_monitor_ui(self) -> None:
        """Build the COM Monitor tab layout (full-width scrollable table)."""
        self.com_monitor.draw_ui()

    def _draw_map_view_ui(self) -> None:
        """Build the Map View tab layout (large map with GPS panel alongside)."""
        with dpg.group(horizontal=True):
            self.map_view_tab.draw_ui()
            self.location_tab.draw_ui(600, 600)

    def build_ui(self) -> None:
        """
        Create the DearPyGui context, viewport, and all tab content.

        Blocks until the user closes the application (via the Escape key
        or the OS window-close button).
        """
        log.info("UIManager: building UI")
        dpg.create_context()

        with dpg.font_registry():
            default_font = dpg.add_font("assets/fonts/Noto_Sans/NotoSans-VariableFont_wdth,wght.ttf", 14)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=default_font)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
        dpg.bind_font(default_font)

        # Hard-coded to 1920×1080. Swap in get_screen_resolution() to go
        # fullscreen on the target display.
        width, height = (1920, 1080)

        log.info("UIManager: creating viewport %dx%d", width, height)
        dpg.create_viewport(
            title="Ground Station GUI",
            width=width,
            height=height,
            x_pos=0,
            y_pos=0,
            decorated=False,
        )

        dpg.set_exit_callback(lambda: self.shutdown())

        with dpg.handler_registry():
            dpg.add_key_press_handler(
                key=dpg.mvKey_Escape,
                callback=lambda: self.shutdown(),
            )

        with dpg.window(
                label="Ground Station UI",
                width=width,
                height=height,
                no_move=True,
                no_resize=True,
        ):
            with dpg.tab_bar():
                with dpg.tab(label="Flight Data"):
                    self._draw_flight_data_ui()

                with dpg.tab(label="COM Monitor"):
                    self._draw_com_monitor_ui()

                with dpg.tab(label="Map View"):
                    self._draw_map_view_ui()

                with dpg.tab(label="Settings"):
                    self.settings_window.draw_ui()

        log.info("UIManager: entering DPG main loop")
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()

        log.info("UIManager: DPG main loop exited — cleaning up")
        dpg.destroy_context()

    # -------------------------------------------------------------------------
    # Telemetry update methods
    #
    # Each method is intentionally small and single-purpose: format the value
    # and push it to the relevant DPG item(s). All methods are callable
    # individually for testing or future extensions.
    # -------------------------------------------------------------------------

    def update_temperature(self, t: float) -> None:
        """Push a new temperature reading (°C) to the last-packet table."""
        log.debug("update_temperature: %.1f °C", t)
        dpg.set_value(self.last_packet_window.system_status_tags["temperature"], f"{t:.1f} °C")

    def update_subsystem(self, status: int) -> None:
        """Push a subsystem status bitmask, displayed as a 3-bit binary string."""
        log.debug("update_subsystem: %d (0b%s)", status, format(status, "03b"))
        dpg.set_value(self.last_packet_window.system_status_tags["subsystem"], format(status, "03b"))

    def update_flight_mode(self, m: int) -> None:
        """Push a flight-mode flag (1 = ON, 0 = OFF)."""
        label = "ON" if m else "OFF"
        log.debug("update_flight_mode: %s", label)
        dpg.set_value(self.last_packet_window.system_status_tags["flight_mode"], label)

    def update_low_power(self, lp: int) -> None:
        """Push a low-power-mode flag (1 = ON, 0 = OFF)."""
        label = "ON" if lp else "OFF"
        log.debug("update_low_power: %s", label)
        dpg.set_value(self.last_packet_window.system_status_tags["low_power"], label)

    def update_status_events(self, e: int) -> None:
        """
        Push a flight-event index.

        Updates both the raw value in the last-packet table and the
        colour-coded state column in :class:`FlightEventWindow`.
        """
        log.debug("update_status_events: event=%d", e)
        dpg.set_value(self.last_packet_window.system_status_tags["status_events"], str(e))
        self.flight_events_window.update_event(e)

    def update_acceleration(self, a: float) -> None:
        """Push an acceleration reading (g) with a mission-elapsed timestamp."""
        elapsed = time.time() - _START_TIME
        log.debug("update_acceleration: %.4f g @ %.2f s", a, elapsed)
        dpg.set_value(self.last_packet_window.system_status_tags["accel"], f"{a:.2f} g")
        self.accelerometer_window.update_acceleration(elapsed, a)

    def update_altitude(
            self,
            pressure_height: float | None = None,
            gnss_height: float | None = None,
    ) -> None:
        """
        Push altitude readings from one or both sources.

        Parameters
        ----------
        pressure_height:
            Barometric altitude in metres. Pass ``None`` to skip.
        gnss_height:
            GNSS altitude in metres. Pass ``None`` to skip.
        """
        elapsed = time.time() - _START_TIME

        if gnss_height is not None:
            log.debug("update_altitude: gnss=%.1f m @ %.2f s", gnss_height, elapsed)
            # NOTE: parameter names are intentionally swapped here to match
            # the existing data-flow contract; correct when the back-end changes.
            self.altitude_window.update_altitude_gnss(elapsed, gnss_height)
            dpg.set_value(
                self.last_packet_window.system_status_tags["gnss_height"],
                f"{gnss_height}",
            )

        if pressure_height is not None:
            log.debug("update_altitude: pressure=%.1f m @ %.2f s", pressure_height, elapsed)
            self.altitude_window.update_altitude_pressure(elapsed, pressure_height)
            dpg.set_value(
                self.last_packet_window.system_status_tags["pressure_height"],
                f"{pressure_height}",
            )

    def update_gps(self, lat: float, lon: float) -> None:
        """
        Push a GPS fix to all map and location widgets.

        Propagates to both tab instances of :class:`MapViewWindow` and
        :class:`LocationWindow` so the map stays in sync regardless of
        which tab is active.
        """
        log.debug("update_gps: lat=%.6f, lon=%.6f", lat, lon)
        dpg.set_value(self.last_packet_window.system_status_tags["lat"], f"{lat}")
        dpg.set_value(self.last_packet_window.system_status_tags["lon"], f"{lon}")

        self.location_window.update_gps(lat, lon)
        self.location_tab.update_gps(lat, lon)
        self.map_view_window.update_location(lat, lon)
        self.map_view_tab.update_location(lat, lon)

    def update_battery(self, v: float) -> None:
        """Push a battery voltage reading (V)."""
        log.debug("update_battery: %.2f V", v)
        dpg.set_value(self.last_packet_window.system_status_tags["batteryVoltage"], f"{v} V")
        self.battery_window.update_voltage(v)

    def update_rssi(self, rssi: int) -> None:
        """Push a received-signal-strength indicator reading (dBm)."""
        log.debug("update_rssi: %d dBm", rssi)
        dpg.set_value(self.last_packet_window.system_status_tags["rssi"], f"{rssi} dBm")
        self.connection_window.update_rssi(rssi)

    def update_packet_delay(self, ms: int) -> None:
        """Push the time-since-last-packet value (milliseconds)."""
        log.debug("update_packet_delay: %d ms", ms)
        dpg.set_value(self.last_packet_window.system_status_tags["packet_delay"], f"{ms} ms")

    def update_all(self, data: dict[str, Any]) -> None:
        """
        Process a complete decoded telemetry packet.

        Appends the raw packet to the COM monitor table, then dispatches each
        known field to its dedicated ``update_*`` handler. Unknown fields are
        silently ignored.

        Parameters
        ----------
        data:
            Dictionary keyed by telemetry field names as produced by the
            TelemetryReceiver back-end.
        """
        log.debug("update_all: dispatching packet with %d fields: %s", len(data), list(data.keys()))
        log.info("incoming package: %s", data)

        self.com_monitor.add_row(data)

        # Dispatch table mapping data-dict keys to their handler methods.
        handlers: dict[str, Callable[[Any], None]] = {
            "temperature": self.update_temperature,
            "subsystem_status": self.update_subsystem,
            "flight_mode": self.update_flight_mode,
            "low_power_mode": self.update_low_power,
            "status_events": self.update_status_events,
            "acceleration": self.update_acceleration,
            "battery_voltage": self.update_battery,
            "rssi": self.update_rssi,
            "time_since_last_packet": self.update_packet_delay,
        }

        for key, handler in handlers.items():
            if key in data:
                handler(data[key])

        # Altitude may carry pressure, GNSS, or both readings in a single packet.
        if "height_pressure" in data or "height_gnss" in data:
            self.update_altitude(
                pressure_height=data.get("height_pressure"),
                gnss_height=data.get("height_gnss"),
            )

        # Lat and lon arrive together; skip the update if either is absent.
        if "lat_gnss" in data or "lon_gnss" in data:
            self.update_gps(
                lat=data.get("lat_gnss"),
                lon=data.get("lon_gnss"),
            )

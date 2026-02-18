import sys
import time
import dearpygui.dearpygui as dpg

from ui.windows import com_monitor_controller
# UI windows
from ui.windows.location_window import LocationWindow
from ui.windows.altitude_window import AltitudeWindow
from ui.windows.battery_window import BatteryWindow
from ui.windows.map_view_window import MapViewWindow
from ui.windows.com_monitor import ComMonitor
from ui.windows.last_packet_window import LastPacketWindow
from ui.windows.com_monitor_controller import ComMonitorController
from ui.windows.flight_events_window import FlightEventMonitor
from ui.windows.accelerometer_window import AccelerometerWindow
from ui.windows.commands_window import CommandsWindow

start_time = time.time()


def get_screen_resolution():
    """Cross-platform fullscreen resolution."""
    if sys.platform.startswith("win"):
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    # Linux/macOS
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h


class UIManager:
    def __init__(self):
        self.map_view = MapViewWindow()
        self.location = LocationWindow()
        self.altitude = AltitudeWindow()
        self.battery = BatteryWindow()
        self.com_monitor = ComMonitor()
        self.com_monitor_controller = ComMonitorController(self)
        self.last_packet = LastPacketWindow()
        self.flight_events = FlightEventMonitor()
        self.accelerometer_window = AccelerometerWindow()
        self.commands_window = CommandsWindow(receiver=self.com_monitor_controller)

    def shutdown(self):
        dpg.destroy_context()

    def _draw_flight_data_ui(self):
        with dpg.group(horizontal=True):
            with dpg.group(horizontal=False):
                self.last_packet.draw_ui(200, 700)
                self.battery.draw_ui(200, 200)
            with dpg.group(horizontal=False):
                self.altitude.draw_ui()
                self.flight_events.draw_ui()
            with dpg.group(horizontal=False):
                #with dpg.group(horizontal=True):
                #    self.map_view.draw_ui()
                #    self.location.draw_ui(200, 300)
                self.accelerometer_window.draw_ui()

    def _draw_com_monitor_ui(self):
        with dpg.group(horizontal=False):
            with dpg.group(horizontal=True):
                self.com_monitor_controller.draw_ui(400,400)
                self.commands_window.draw_ui(800, 400)
        self.com_monitor.draw_ui()

    def _draw_map_view_ui(self):
        with dpg.group(horizontal=True):
            self.map_view.draw_ui()
            self.location.draw_ui(200, 300)

    def _draw_commands_screen_ui(self):
        pass


    # --------------------------------------------------------
    #  Build UI
    # --------------------------------------------------------
    def build_ui(self):
        dpg.create_context()

        # Fullscreen viewport
        #width, height = get_screen_resolution()
        width, height = (1920, 1080)
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
                callback=lambda: self.shutdown()
            )

        # Main
        with dpg.window(
                label="Ground Station UI",
                width=width,
                height=height,
                no_move=True,
                no_resize=True
        ):
            with dpg.tab_bar():
                with dpg.tab(label="Flight Data"):
                    self._draw_flight_data_ui()
                with dpg.tab(label="COM Monitor"):
                    self._draw_com_monitor_ui()
                with dpg.tab(label="Map View"):
                    self._draw_map_view_ui()
                with dpg.tab(label="Commands"):
                    self._draw_commands_screen_ui()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def update_temperature(self, t: float):
        dpg.set_value(self.last_packet.system_status_tags["temperature"], f"{t:.1f} °C")

    def update_subsystem(self, status: int):

        dpg.set_value(self.last_packet.system_status_tags["subsystem"], format(status, "03b"))

    def update_flight_mode(self, m: int):
        dpg.set_value(self.last_packet.system_status_tags["flight_mode"], "ON" if m else "OFF")

    def update_low_power(self, lp: int):
        dpg.set_value(self.last_packet.system_status_tags["low_power"], "ON" if lp else "OFF")

    def update_status_events(self, e: int):
        dpg.set_value(self.last_packet.system_status_tags["status_events"], str(e))
        self.flight_events.update_event(e)

    def update_accel(self, a: float):
        dpg.set_value(self.last_packet.system_status_tags["accel"], f"{a:.2f} g")
        self.accelerometer_window.update_accel(a)

    def update_altitude(self, pressure_height: float = None, gnss_height: float = None):
        now = time.time()
        elapsed = now - start_time

        if gnss_height is not None:
            self.altitude.update_altitude_pressure(elapsed, gnss_height)
            dpg.set_value(self.last_packet.system_status_tags["gnss_height"], f"{gnss_height}")
        if pressure_height is not None:
            self.altitude.update_altitude_gnss(elapsed, pressure_height)
            dpg.set_value(self.last_packet.system_status_tags["pressure_height"], f"{pressure_height}")

    def update_gps(self, lat: float, lon: float):
        dpg.set_value(self.last_packet.system_status_tags["lat"], f"{lat}")
        dpg.set_value(self.last_packet.system_status_tags["lon"], f"{lon}")
        self.location.update_gps(lat, lon)
        self.map_view.update_location(lat, lon)

    def update_battery(self, v: float):
        dpg.set_value(self.last_packet.system_status_tags["batteryVoltage"], f"{v} V")
        self.battery.update_voltage(v)

    def update_rssi(self, rssi: int):
        dpg.set_value(self.last_packet.system_status_tags["rssi"], f"{rssi} dBm")

    def update_packet_delay(self, ms: int):
        dpg.set_value(self.last_packet.system_status_tags["packet_delay"], f"{ms} ms")

    def update_all(self, data: dict):
        self.com_monitor.add_row(data)
        """
        Calls the appropriate update method for each key in the data dict.
        Expected keys: temperature, subsystem, flight_mode, low_power, status_events,
                       accel, pressure_height, gnss_height, lat, lon, batteryVoltage,
                       rssi, packet_delay
        """
        if "temperature" in data:
            self.update_temperature(data["temperature"])
        if "subsystem_status" in data:
            self.update_subsystem(data["subsystem_status"])
        if "flight_mode" in data:
            self.update_flight_mode(data["flight_mode"])
        if "low_power_mode" in data:
            self.update_low_power(data["low_power_mode"])
        if "status_events" in data:
            self.update_status_events(data["status_events"])
        if "acceleration" in data:
            self.update_accel(data["acceleration"])
        if "height_pressure" in data and "height_gnss" in data:
            self.update_altitude(
                pressure_height=data.get("height_pressure"),
                gnss_height=data.get("height_gnss")
            )
        if "lat_gnss" in data and "lon_gnss" in data:
            self.update_gps(data["lat_gnss"], data["lon_gnss"])
        if "battery_voltage" in data:
            self.update_battery(data["battery_voltage"])
        if "rssi" in data:
            self.update_rssi(data["rssi"])
        if "time_since_last_packet" in data:
            self.update_packet_delay(data["time_since_last_packet"])

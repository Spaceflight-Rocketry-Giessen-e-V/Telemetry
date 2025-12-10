import dearpygui.dearpygui as dpg


class LastPacketWindow:
    # New grouped GUI elements
    system_status_tags = {
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

    def draw_ui(self, window_width=250, window_height=750):
        """Creates the panel holding all system status values."""
        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("System Status", bullet=False)

            # Acceleration
            dpg.add_text("Acceleration")
            dpg.add_text("0.00 g", tag=self.system_status_tags["accel"])

            # Temperature
            dpg.add_spacer()
            dpg.add_text("Temperature")
            dpg.add_text("0.0 °C", tag=self.system_status_tags["temperature"])

            # Subsystem Status
            dpg.add_spacer()
            dpg.add_text("Subsystem Status")
            dpg.add_text("0", tag=self.system_status_tags["subsystem"])

            # Flight Mode
            dpg.add_spacer()
            dpg.add_text("Flight Mode")
            dpg.add_text("0", tag=self.system_status_tags["flight_mode"])

            # Low Power
            dpg.add_spacer()
            dpg.add_text("Low Power Mode")
            dpg.add_text("OFF", tag=self.system_status_tags["low_power"])

            # Status Events
            dpg.add_spacer()
            dpg.add_text("Status Events")
            dpg.add_text("0", tag=self.system_status_tags["status_events"])

            # RSSI
            dpg.add_spacer()
            dpg.add_text("RSSI")
            dpg.add_text("0 dBm", tag=self.system_status_tags["rssi"])

            # Packet Delay
            dpg.add_spacer()
            dpg.add_text("Packet Delay")
            dpg.add_text("0 ms", tag=self.system_status_tags["packet_delay"])

            # Altitudes
            dpg.add_spacer()
            dpg.add_text("GNSS Height")
            dpg.add_text("0 m", tag=self.system_status_tags["gnss_height"])

            dpg.add_spacer()
            dpg.add_text("Pressure Height")
            dpg.add_text("0 m", tag=self.system_status_tags["pressure_height"])

            # GPS Coordinates
            dpg.add_spacer()
            dpg.add_text("Latitude")
            dpg.add_text("0.0", tag=self.system_status_tags["lat"])

            dpg.add_spacer()
            dpg.add_text("Longitude")
            dpg.add_text("0.0", tag=self.system_status_tags["lon"])

            # Battery
            dpg.add_spacer()
            dpg.add_text("Battery Voltage")
            dpg.add_text("0.0 V", tag=self.system_status_tags["batteryVoltage"])

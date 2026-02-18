import dearpygui.dearpygui as dpg


class ComMonitor:
    tag = "COM Monitor Table"

    columns = [
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
        ("time_since_last_packet", "time_since_last_packet"),
    ]

    def draw_ui(self):
        with dpg.child_window(label="Communication Monitor"):
            with dpg.table(
                header_row=True,
                tag=self.tag,
                clipper=True,
                scrollY=True,
            ):
                for label, _ in self.columns:
                    dpg.add_table_column(label=label)

    def add_row(self, data: dict):
        with dpg.table_row(parent=self.tag):
            for _, key in self.columns:
                value = data.get(key, "")

                if isinstance(value, float):
                    if key == "acceleration":
                        value = f"{value:.4f}"
                    elif key in ("lat_gnss", "lon_gnss"):
                        value = f"{value:.7f}"
                    else:
                        value = f"{value:.1f}"

                dpg.add_text(str(value))
                #dpg.set_x_scroll("Communication Monitor", dpg.get_x_scroll_max("Communication Monitor"))

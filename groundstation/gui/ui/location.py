import dearpygui.dearpygui as dpg


class Location:
    lat = 0.0
    lon = 0.0

    @staticmethod
    def decimal_to_dms(decimal: float):
        # Convert decimal degrees to degrees, minutes, seconds
        degrees = int(decimal)
        minutes_full = abs((decimal - degrees) * 60)
        minutes = int(minutes_full)
        seconds = (minutes_full - minutes) * 60
        return degrees, minutes, seconds

    @classmethod
    def draw_ui(cls):
        with dpg.child_window(label="GPS", width=600, height=400):
            # Two-column horizontal layout
            with dpg.group(horizontal=True):
                # Map view
                with dpg.group():
                    dpg.add_text("Map", color=[0, 255, 0])
                    with dpg.drawlist(width=400, height=400, tag="map_canvas"):
                        dpg.draw_rectangle((0, 0), (400, 400),
                                           color=(200, 200, 200, 255),
                                           fill=(240, 240, 240, 255))
                        dpg.draw_text((10, 10), "OpenStreetMap tiles coming soon...",
                                      size=15, color=(0, 0, 0, 255))

                # GPS coordinates
                with dpg.group():
                    dpg.add_text("GPS Coordinates", color=[255, 255, 0])

                    dpg.add_text("Decimal:", color=[200, 200, 200])
                    dpg.add_text("Latitude:", tag="lat_label")
                    dpg.add_text(f"{cls.lat:.6f}", tag="lat_value")
                    dpg.add_text("Longitude:", tag="lon_label")
                    dpg.add_text(f"{cls.lon:.6f}", tag="lon_value")

                    dpg.add_separator()

                    dpg.add_text("DMS:", color=[200, 200, 200])
                    dpg.add_text("Latitude:", tag="lat_dms_label")
                    dpg.add_text("0°0'0\"", tag="lat_dms_value")
                    dpg.add_text("Longitude:", tag="lon_dms_label")
                    dpg.add_text("0°0'0\"", tag="lon_dms_value")

    @classmethod
    def update_gps(cls, lat: float, lon: float):
        # Update UI
        cls.lat, cls.lon = lat, lon

        # Update decimal values
        dpg.set_value("lat_value", f"{lat:.6f}")
        dpg.set_value("lon_value", f"{lon:.6f}")

        # Update DMS values
        lat_d, lat_m, lat_s = cls.decimal_to_dms(lat)
        lon_d, lon_m, lon_s = cls.decimal_to_dms(lon)
        dpg.set_value("lat_dms_value", f"{lat_d}°{lat_m}'{lat_s:.2f}\"")
        dpg.set_value("lon_dms_value", f"{lon_d}°{lon_m}'{lon_s:.2f}\"")

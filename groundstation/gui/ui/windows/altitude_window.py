import dearpygui.dearpygui as dpg
import statistics


class AltitudeWindow:
    altitude_total_min = 0
    altitude_total_max = 1000

    altitude_min = None
    altitude_max = None
    altitude_current = None

    time_data_gnss = []
    time_data_pressure = []
    altitude_pressure_data = []
    altitude_gnss_data = []

    delta_data = []
    plot_active = True

    @classmethod
    def draw_ui(cls):
        with dpg.child_window(width=600, height=400):
            dpg.add_text("Altitude")

            with dpg.plot(label="Altitude vs Time", height=300, width=-1, zoom_mod=1):
                dpg.add_plot_legend()

                with dpg.plot_axis(dpg.mvXAxis, label="Time (s)", tag="xaxis"):
                    pass

                with dpg.plot_axis(dpg.mvYAxis, label="Altitude (m)", tag="yaxis"):

                    # Line 1 — Pressure altitude
                    dpg.add_line_series(
                        [], [],
                        tag="altitude_pressure_series",
                        label="Pressure Alt",
                        parent="yaxis"
                    )

                    # Line 2 — GNSS altitude
                    dpg.add_line_series(
                        [], [],
                        tag="altitude_gnss_series",
                        label="GNSS Alt",
                        parent="yaxis"
                    )

            with dpg.group(horizontal=True):
                # Altitude min/max
                with dpg.group(horizontal=False):
                    dpg.add_text("Min: 0 m", tag="alt_min")
                    dpg.add_spacer(width=10)
                    dpg.add_text("Max: 0 m", tag="alt_max")

                dpg.add_spacer(width=20)
                dpg.add_text("Current: 0 m", tag="alt_current")
                dpg.add_spacer(width=20)

                # Delta
                with dpg.group(horizontal=False):
                    dpg.add_text("Delta: 0 m", tag="alt_delta")
                    dpg.add_spacer(width=10)
                    dpg.add_text("Median Delta: 0 m", tag="alt_median_delta")

                dpg.add_spacer(height=10)
                dpg.add_button(label="Stop Plot", callback=lambda: cls.stop_plot())

    @classmethod
    def stop_plot(cls):
        cls.plot_active = False
        print("Altitude Plot stopped")

    @classmethod
    def update_altitude_pressure(cls, time_value, altitude_value):
        """Updates only the pressure-altitude line."""
        cls._update_altitude_common(time_value, altitude_value, source="pressure")

    @classmethod
    def update_altitude_gnss(cls, time_value, altitude_value):
        """Updates only the GNSS-altitude line."""
        cls._update_altitude_common(time_value, altitude_value, source="gnss")


    @classmethod
    def _update_altitude_common(cls, time_value, altitude_value, source):
        if not cls.plot_active:
            return

        # Append to correct data series
        if source == "pressure":
            cls.time_data_pressure.append(time_value)
            cls.altitude_pressure_data.append(altitude_value)
            series_tag = "altitude_pressure_series"
        else:
            cls.time_data_gnss.append(time_value)
            cls.altitude_gnss_data.append(altitude_value)
            series_tag = "altitude_gnss_series"

        # Track global min/max/current
        cls.altitude_current = altitude_value
        if cls.altitude_min is None or altitude_value < cls.altitude_min:
            cls.altitude_min = altitude_value
        if cls.altitude_max is None or altitude_value > cls.altitude_max:
            cls.altitude_max = altitude_value

        # Delta calculation
        if len(cls.altitude_pressure_data if source == "pressure" else cls.altitude_gnss_data) > 1:
            prev = (cls.altitude_pressure_data[-2]
                    if source == "pressure"
                    else cls.altitude_gnss_data[-2])
            delta = altitude_value - prev
        else:
            delta = 0

        cls.delta_data.append(delta)
        median_delta = statistics.median(cls.delta_data) if cls.delta_data else 0

        # Update selected line series
        if source == "pressure":
            dpg.set_value(series_tag, [cls.time_data_pressure, cls.altitude_pressure_data])
        else:
            dpg.set_value(series_tag, [cls.time_data_gnss, cls.altitude_gnss_data])

        # Auto-fit
        dpg.fit_axis_data("xaxis")
        dpg.fit_axis_data("yaxis")

        # Update labels (shared for both sources)
        dpg.set_value("alt_min", f"Min: {cls.altitude_min:.1f} m")
        dpg.set_value("alt_current", f"Current: {cls.altitude_current:.1f} m")
        dpg.set_value("alt_max", f"Max: {cls.altitude_max:.1f} m")
        dpg.set_value("alt_delta", f"Delta: {delta:.1f} m")
        dpg.set_value("alt_median_delta", f"Median Delta: {median_delta:.1f} m")

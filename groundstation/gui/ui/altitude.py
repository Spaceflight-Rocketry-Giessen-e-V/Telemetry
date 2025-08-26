import dearpygui.dearpygui as dpg
import statistics


class Altitude:
    altitude_total_min = 0
    altitude_total_max = 1000

    altitude_min = None
    altitude_max = None
    altitude_current = None

    time_data = []
    altitude_data = []
    delta_data = []

    # Flag to stop the plot
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
                    dpg.add_line_series([], [], tag="altitude_series", parent="yaxis")

            with dpg.group(horizontal=True):
                # Altitude min/max
                with dpg.group(horizontal=False):
                    dpg.add_text("Min: 0 m", tag="alt_min")
                    dpg.add_spacer(width=10)
                    dpg.add_text("Max: 0 m", tag="alt_max")

                # Altitude current
                dpg.add_spacer(width=20)
                dpg.add_text("Current: 0 m", tag="alt_current")
                dpg.add_spacer(width=20)

                # Altitude Deltas
                with dpg.group(horizontal=False):
                    dpg.add_text("Delta: 0 m", tag="alt_delta")
                    dpg.add_spacer(width=10)
                    dpg.add_text("Median Delta: 0 m", tag="alt_median_delta")

                # Stop Plot button
                dpg.add_spacer(height=10)
                dpg.add_button(label="Stop Plot", callback=lambda: cls.stop_plot())

    @classmethod
    def stop_plot(cls):
        cls.plot_active = False
        print("Altitude Plot stopped")

    @classmethod
    def update_altitude(cls, time_value, altitude_value):
        # Stop plot check
        if not cls.plot_active:
            return

        cls.time_data.append(time_value)
        cls.altitude_data.append(altitude_value)
        cls.altitude_current = altitude_value

        # Update min/max
        if cls.altitude_min is None or altitude_value < cls.altitude_min:
            cls.altitude_min = altitude_value
        if cls.altitude_max is None or altitude_value > cls.altitude_max:
            cls.altitude_max = altitude_value

        # Compute delta
        if len(cls.altitude_data) > 1:
            delta = altitude_value - cls.altitude_data[-2]
        else:
            delta = 0
        cls.delta_data.append(delta)

        # Compute median delta
        median_delta = statistics.median(cls.delta_data) if cls.delta_data else 0

        # Update the plot
        dpg.set_value("altitude_series", [cls.time_data, cls.altitude_data])
        dpg.fit_axis_data("xaxis")
        dpg.fit_axis_data("yaxis")

        # Update labels
        dpg.set_value("alt_min", f"Min: {cls.altitude_min:.1f} m")
        dpg.set_value("alt_current", f"Current: {cls.altitude_current:.1f} m")
        dpg.set_value("alt_max", f"Max: {cls.altitude_max:.1f} m")
        dpg.set_value("alt_delta", f"Delta: {delta:.1f} m")
        dpg.set_value("alt_median_delta", f"Median Delta: {median_delta:.1f} m")

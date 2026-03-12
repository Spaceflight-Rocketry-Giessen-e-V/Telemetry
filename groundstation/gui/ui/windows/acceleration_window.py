"""
acceleration_window.py
----------------------
Live acceleration chart with per-session statistics.

Plots acceleration (g) against mission elapsed time and tracks running
min, max, current value, per-sample delta, and median delta. The plot can
be frozen via the "Stop Plot" button; incoming data is still recorded while
the display is paused.
"""

import logging
import statistics

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class AccelerationWindow:
    """Live acceleration chart with statistics strip."""

    # DPG item tags
    _TAG_SERIES = "accel_series"
    _TAG_XAXIS = "accel_xaxis"
    _TAG_YAXIS = "accel_yaxis"
    _TAG_MIN = "accel_min"
    _TAG_MAX = "accel_max"
    _TAG_CURRENT = "accel_current"
    _TAG_DELTA = "accel_delta"
    _TAG_MEDIAN_DELTA = "accel_median_delta"

    # Session state — class-level because only one plot instance exists per run.
    time_data: list[float] = []
    accel_data: list[float] = []
    delta_data: list[float] = []

    accel_min: float | None = None
    accel_max: float | None = None
    accel_current: float | None = None

    plot_active: bool = True

    def __init__(self):
        log.debug("%s: initialised", self.__class__.__name__)

    @classmethod
    def draw_ui(cls, window_width: int = 600, window_height: int = 400) -> None:
        """
        Create the acceleration child-window with plot and statistics strip.

        Call once during UI construction.
        """
        log.debug("AccelerationWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("Acceleration", color=(255, 255, 0))

            with dpg.plot(label="Acceleration vs Time", height=300, width=-1, zoom_mod=1):
                dpg.add_plot_legend()

                with dpg.plot_axis(dpg.mvXAxis, label="Time (s)", tag=cls._TAG_XAXIS):
                    pass

                with dpg.plot_axis(dpg.mvYAxis, label="Acceleration (g)", tag=cls._TAG_YAXIS):
                    dpg.add_line_series(
                        [], [],
                        tag=cls._TAG_SERIES,
                        label="Acceleration",
                        parent=cls._TAG_YAXIS,
                    )

            with dpg.group(horizontal=True):
                with dpg.group(horizontal=False):
                    dpg.add_text("Min: 0 g", tag=cls._TAG_MIN)
                    dpg.add_spacer(width=10)
                    dpg.add_text("Max: 0 g", tag=cls._TAG_MAX)

                dpg.add_spacer(width=20)
                dpg.add_text("Current: 0 g", tag=cls._TAG_CURRENT)
                dpg.add_spacer(width=20)

                with dpg.group(horizontal=False):
                    dpg.add_text("Delta: 0 g", tag=cls._TAG_DELTA)
                    dpg.add_spacer(width=10)
                    dpg.add_text("Median Delta: 0 g", tag=cls._TAG_MEDIAN_DELTA)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Stop Plot", callback=lambda: cls.stop_plot())

    @classmethod
    def stop_plot(cls) -> None:
        """Freeze the plot. New data is still recorded but not drawn."""
        cls.plot_active = False
        log.info("AccelerationWindow: plot frozen by user")

    @classmethod
    def update_acceleration(cls, time_value: float, accel_value: float) -> None:
        """
        Append a new data point and refresh the plot and statistics labels.

        Parameters
        ----------
        time_value:
            Mission elapsed time in seconds.
        accel_value:
            Acceleration reading in g.
        """
        if not cls.plot_active:
            log.debug("AccelerationWindow: plot frozen, skipping update (t=%.2f)", time_value)
            return

        cls.time_data.append(time_value)
        cls.accel_data.append(accel_value)

        cls.accel_current = accel_value
        if cls.accel_min is None or accel_value < cls.accel_min:
            cls.accel_min = accel_value
            log.debug("AccelerationWindow: new min = %.4f g", accel_value)
        if cls.accel_max is None or accel_value > cls.accel_max:
            cls.accel_max = accel_value
            log.debug("AccelerationWindow: new max = %.4f g", accel_value)

        delta = accel_value - cls.accel_data[-2] if len(cls.accel_data) > 1 else 0.0
        cls.delta_data.append(delta)
        median_delta = statistics.median(cls.delta_data) if cls.delta_data else 0.0

        dpg.set_value(cls._TAG_SERIES, [cls.time_data, cls.accel_data])
        dpg.fit_axis_data(cls._TAG_XAXIS)
        dpg.fit_axis_data(cls._TAG_YAXIS)

        dpg.set_value(cls._TAG_MIN, f"Min: {cls.accel_min:.2f} g")
        dpg.set_value(cls._TAG_CURRENT, f"Current: {cls.accel_current:.2f} g")
        dpg.set_value(cls._TAG_MAX, f"Max: {cls.accel_max:.2f} g")
        dpg.set_value(cls._TAG_DELTA, f"Delta: {delta:.2f} g")
        dpg.set_value(cls._TAG_MEDIAN_DELTA, f"Median Delta: {median_delta:.2f} g")

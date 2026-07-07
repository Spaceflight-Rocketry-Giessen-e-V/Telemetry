"""
acceleration_window.py
----------------------
Live acceleration chart with per-session statistics.

Plots acceleration (g) against mission elapsed time and tracks running
min, max, current value, per-sample delta, and median delta. The plot can
be frozen via the "Stop Plot" button or fully reset via "Reset Plot";
incoming data is still recorded while the display is paused.
"""

import logging
import math
import statistics

import dearpygui.dearpygui as dpg

from ui.windows.plot_coordinator import PlotCoordinator

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
    _TAG_BTN_STOP_RESUME = "accel_btn_stop_resume"

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
                    dpg.add_button(
                        label="Stop Plot",
                        tag=cls._TAG_BTN_STOP_RESUME,
                        callback=lambda: PlotCoordinator.toggle(),
                        width=100
                    )
                    dpg.add_button(label="Reset Plot",
                                   callback=lambda: PlotCoordinator.reset_all(), width=100)
                dpg.add_spacer(width=10)
                with dpg.group(horizontal=False):
                    dpg.add_text("Min: 0 g", tag=cls._TAG_MIN)
                    dpg.add_text("Max: 0 g", tag=cls._TAG_MAX)
                dpg.add_spacer(width=10)
                dpg.add_text("Current: 0 g", tag=cls._TAG_CURRENT)

                with dpg.group(horizontal=False):
                    dpg.add_text("Delta: 0 g", tag=cls._TAG_DELTA)
                    dpg.add_text("Median Delta: 0 g", tag=cls._TAG_MEDIAN_DELTA)



    @classmethod
    def stop_plot(cls) -> None:
        """Freeze the plot. New data is still recorded but not drawn."""
        cls.plot_active = False
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Resume Plot")
        log.info("AccelerationWindow: plot frozen")

    @classmethod
    def resume_plot(cls) -> None:
        """Resume live drawing after a stop."""
        cls.plot_active = True
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Stop Plot")
        log.info("AccelerationWindow: plot resumed")

    @classmethod
    def reset_plot(cls) -> None:
        """
        Clear all session data and statistics, and wipe the chart.

        The plot is also resumed automatically so the operator does not need
        a second click after a reset (common workflow: reset between flights).
        """
        log.info("AccelerationWindow: plot reset by user")

        # Clear all series data
        cls.time_data.clear()
        cls.accel_data.clear()
        cls.delta_data.clear()

        # Reset statistics
        cls.accel_min = None
        cls.accel_max = None
        cls.accel_current = None

        # Ensure the plot resumes on reset — avoids a redundant "Resume" click
        cls.plot_active = True
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Stop Plot")

        # Wipe the series on the chart
        dpg.set_value(cls._TAG_SERIES, [[], []])

        # Reset the statistics strip
        dpg.set_value(cls._TAG_MIN, "Min: 0 g")
        dpg.set_value(cls._TAG_MAX, "Max: 0 g")
        dpg.set_value(cls._TAG_CURRENT, "Current: 0 g")
        dpg.set_value(cls._TAG_DELTA, "Delta: 0 g")
        dpg.set_value(cls._TAG_MEDIAN_DELTA, "Median Delta: 0 g")

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

        if math.isnan(accel_value) or math.isinf(accel_value):
            log.warning("AccelerationWindow: dropping non-finite acceleration %r", accel_value)
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

        if len(cls.accel_data) > 1:
            delta = accel_value - cls.accel_data[-2]
            cls.delta_data.append(delta)
        else:
            delta = 0.0
        median_delta = statistics.median(cls.delta_data) if cls.delta_data else 0.0

        dpg.set_value(cls._TAG_SERIES, [cls.time_data, cls.accel_data])
        dpg.fit_axis_data(cls._TAG_XAXIS)
        dpg.fit_axis_data(cls._TAG_YAXIS)

        dpg.set_value(cls._TAG_MIN, f"Min: {cls.accel_min:.2f} g")
        dpg.set_value(cls._TAG_CURRENT, f"Current: {cls.accel_current:.2f} g")
        dpg.set_value(cls._TAG_MAX, f"Max: {cls.accel_max:.2f} g")
        dpg.set_value(cls._TAG_DELTA, f"Delta: {delta:.2f} g")
        dpg.set_value(cls._TAG_MEDIAN_DELTA, f"Median Delta: {median_delta:.2f} g")
"""
altitude_window.py
------------------
Live dual-source altitude chart with per-session statistics.

Two independent data series are maintained:
  - **Pressure altitude** — derived from the barometric sensor.
  - **GNSS altitude**     — reported by the GPS receiver.

Pressure and GNSS each track their own min / max / current statistics.
"""

import logging
import math

import dearpygui.dearpygui as dpg

from ui.windows.plot_coordinator import PlotCoordinator

log = logging.getLogger(__name__)


class AltitudeWindow:
    """Live dual-source altitude chart with statistics strip."""

    # DPG item tags
    _TAG_XAXIS = "xaxis"
    _TAG_YAXIS = "yaxis"
    _TAG_SERIES_PRESSURE = "altitude_pressure_series"
    _TAG_SERIES_GNSS = "altitude_gnss_series"
    _TAG_P_MIN = "alt_p_min"
    _TAG_P_MAX = "alt_p_max"
    _TAG_P_CUR = "alt_p_current"
    _TAG_G_MIN = "alt_g_min"
    _TAG_G_MAX = "alt_g_max"
    _TAG_G_CUR = "alt_g_current"
    _TAG_BTN_STOP_RESUME = "alt_btn_stop_resume"

    # Session state
    time_data_pressure: list[float] = []
    time_data_gnss: list[float] = []
    altitude_pressure_data: list[float] = []
    altitude_gnss_data: list[float] = []

    # Per-source statistics (pressure and GNSS are tracked independently).
    pressure_min: float | None = None
    pressure_max: float | None = None
    pressure_current: float | None = None
    gnss_min: float | None = None
    gnss_max: float | None = None
    gnss_current: float | None = None

    plot_active: bool = True

    def __init__(self):
        log.debug("%s: initialised", self.__class__.__name__)

    @classmethod
    def draw_ui(cls, window_width: int = 600, window_height: int = 400) -> None:
        """
        Create the altitude child-window with dual-line plot and statistics strip.

        Call once during UI construction.
        """
        log.debug("AltitudeWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("Altitude", color=(255, 255, 0))

            with dpg.plot(label="Altitude vs Time", height=300, width=-1, zoom_mod=1):
                dpg.add_plot_legend()

                with dpg.plot_axis(dpg.mvXAxis, label="Time (s)", tag=cls._TAG_XAXIS):
                    pass

                with dpg.plot_axis(dpg.mvYAxis, label="Altitude (m)", tag=cls._TAG_YAXIS):
                    dpg.add_line_series(
                        [], [],
                        tag=cls._TAG_SERIES_PRESSURE,
                        label="Pressure Alt",
                        parent=cls._TAG_YAXIS,
                    )
                    dpg.add_line_series(
                        [], [],
                        tag=cls._TAG_SERIES_GNSS,
                        label="GNSS Alt",
                        parent=cls._TAG_YAXIS,
                    )

            with dpg.group(horizontal=True):
                with dpg.group(horizontal=False):
                    dpg.add_button(
                        label="Stop Plot",
                        tag=cls._TAG_BTN_STOP_RESUME,
                        callback=lambda: PlotCoordinator.toggle(), width=100
                    )
                    dpg.add_button(label="Reset Plot",
                                   callback=lambda: PlotCoordinator.reset_all(), width=100)
                dpg.add_spacer(width=10)
                with dpg.group(horizontal=False):
                    dpg.add_text("Pressure", color=(180, 200, 255))
                    dpg.add_text("Min: 0 m", tag=cls._TAG_P_MIN)
                    dpg.add_text("Max: 0 m", tag=cls._TAG_P_MAX)
                    dpg.add_text("Cur: 0 m", tag=cls._TAG_P_CUR)
                dpg.add_spacer(width=10)
                with dpg.group(horizontal=False):
                    dpg.add_text("GNSS", color=(180, 255, 180))
                    dpg.add_text("Min: 0 m", tag=cls._TAG_G_MIN)
                    dpg.add_text("Max: 0 m", tag=cls._TAG_G_MAX)
                    dpg.add_text("Cur: 0 m", tag=cls._TAG_G_CUR)


    @classmethod
    def stop_plot(cls) -> None:
        """Freeze the plot. Incoming data is still recorded but not drawn."""
        cls.plot_active = False
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Resume Plot")
        log.info("AltitudeWindow: plot frozen")

    @classmethod
    def resume_plot(cls) -> None:
        """Resume live drawing after a stop."""
        cls.plot_active = True
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Stop Plot")
        log.info("AltitudeWindow: plot resumed")

    @classmethod
    def reset_plot(cls) -> None:
        """
        Clear all session data and statistics, and wipe the chart.

        The plot is also resumed automatically so the operator does not need
        a second click after a reset (common workflow: reset between flights).
        """
        log.info("AltitudeWindow: plot reset by user")

        # Clear all series data
        cls.time_data_pressure.clear()
        cls.time_data_gnss.clear()
        cls.altitude_pressure_data.clear()
        cls.altitude_gnss_data.clear()

        # Reset statistics
        cls.pressure_min = cls.pressure_max = cls.pressure_current = None
        cls.gnss_min = cls.gnss_max = cls.gnss_current = None

        # Ensure the plot resumes on reset — avoids a redundant "Resume" click
        cls.plot_active = True
        if dpg.does_item_exist(cls._TAG_BTN_STOP_RESUME):
            dpg.set_item_label(cls._TAG_BTN_STOP_RESUME, "Stop Plot")

        # Wipe both series on the chart
        dpg.set_value(cls._TAG_SERIES_PRESSURE, [[], []])
        dpg.set_value(cls._TAG_SERIES_GNSS, [[], []])

        # Reset both statistics strips
        for tag in (cls._TAG_P_MIN, cls._TAG_G_MIN):
            dpg.set_value(tag, "Min: 0 m")
        for tag in (cls._TAG_P_MAX, cls._TAG_G_MAX):
            dpg.set_value(tag, "Max: 0 m")
        for tag in (cls._TAG_P_CUR, cls._TAG_G_CUR):
            dpg.set_value(tag, "Cur: 0 m")

    @classmethod
    def update_altitude_pressure(cls, time_value: float, altitude_value: float) -> None:
        """Append a pressure-altitude reading and refresh the display."""
        log.debug("AltitudeWindow: pressure alt %.1f m @ t=%.2f s", altitude_value, time_value)
        cls._update_altitude_common(time_value, altitude_value, source="pressure")

    @classmethod
    def update_altitude_gnss(cls, time_value: float, altitude_value: float) -> None:
        """Append a GNSS-altitude reading and refresh the display."""
        log.debug("AltitudeWindow: gnss alt %.1f m @ t=%.2f s", altitude_value, time_value)
        cls._update_altitude_common(time_value, altitude_value, source="gnss")

    @classmethod
    def _update_altitude_common(
            cls,
            time_value: float,
            altitude_value: float,
            source: str,
    ) -> None:
        """
        Shared update path for both altitude sources.

        Appends the reading to the correct series, updates shared statistics
        (min/max/current), then repaints the DPG items.

        Parameters
        ----------
        source:
            ``"pressure"`` or ``"gnss"``.
        """
        if not cls.plot_active:
            return

        if math.isnan(altitude_value) or math.isinf(altitude_value):
            log.warning("AltitudeWindow: dropping non-finite %s altitude %r", source, altitude_value)
            return

        if source == "pressure":
            cls.time_data_pressure.append(time_value)
            cls.altitude_pressure_data.append(altitude_value)
            series_tag = cls._TAG_SERIES_PRESSURE
            source_data = cls.altitude_pressure_data
            source_time = cls.time_data_pressure
            cls.pressure_current = altitude_value
            if cls.pressure_min is None or altitude_value < cls.pressure_min:
                cls.pressure_min = altitude_value
            if cls.pressure_max is None or altitude_value > cls.pressure_max:
                cls.pressure_max = altitude_value
            min_tag, max_tag, cur_tag = cls._TAG_P_MIN, cls._TAG_P_MAX, cls._TAG_P_CUR
            stat_min, stat_max, stat_cur = cls.pressure_min, cls.pressure_max, cls.pressure_current
        else:
            cls.time_data_gnss.append(time_value)
            cls.altitude_gnss_data.append(altitude_value)
            series_tag = cls._TAG_SERIES_GNSS
            source_data = cls.altitude_gnss_data
            source_time = cls.time_data_gnss
            cls.gnss_current = altitude_value
            if cls.gnss_min is None or altitude_value < cls.gnss_min:
                cls.gnss_min = altitude_value
            if cls.gnss_max is None or altitude_value > cls.gnss_max:
                cls.gnss_max = altitude_value
            min_tag, max_tag, cur_tag = cls._TAG_G_MIN, cls._TAG_G_MAX, cls._TAG_G_CUR
            stat_min, stat_max, stat_cur = cls.gnss_min, cls.gnss_max, cls.gnss_current

        log.debug("AltitudeWindow: %s min=%.1f max=%.1f cur=%.1f",
                  source, stat_min, stat_max, stat_cur)

        dpg.set_value(series_tag, [source_time, source_data])
        dpg.fit_axis_data(cls._TAG_XAXIS)
        dpg.fit_axis_data(cls._TAG_YAXIS)

        dpg.set_value(min_tag, f"Min: {stat_min:.1f} m")
        dpg.set_value(max_tag, f"Max: {stat_max:.1f} m")
        dpg.set_value(cur_tag, f"Cur: {stat_cur:.1f} m")

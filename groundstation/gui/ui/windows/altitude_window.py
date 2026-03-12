"""
altitude_window.py
------------------
Live dual-source altitude chart with per-session statistics.

Two independent data series are maintained:
  - **Pressure altitude** — derived from the barometric sensor.
  - **GNSS altitude**     — reported by the GPS receiver.

Shared statistics (min, max, current, delta, median delta) are updated
whenever either source provides a new reading.
"""

import logging
import statistics

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class AltitudeWindow:
    """Live dual-source altitude chart with statistics strip."""

    # DPG item tags
    _TAG_XAXIS = "xaxis"
    _TAG_YAXIS = "yaxis"
    _TAG_SERIES_PRESSURE = "altitude_pressure_series"
    _TAG_SERIES_GNSS = "altitude_gnss_series"
    _TAG_MIN = "alt_min"
    _TAG_MAX = "alt_max"
    _TAG_CURRENT = "alt_current"
    _TAG_DELTA = "alt_delta"
    _TAG_MEDIAN_DELTA = "alt_median_delta"

    # Session state
    time_data_pressure: list[float] = []
    time_data_gnss: list[float] = []
    altitude_pressure_data: list[float] = []
    altitude_gnss_data: list[float] = []

    delta_data: list[float] = []
    altitude_min: float | None = None
    altitude_max: float | None = None
    altitude_current: float | None = None

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
                    dpg.add_text("Min: 0 m", tag=cls._TAG_MIN)
                    dpg.add_spacer(width=10)
                    dpg.add_text("Max: 0 m", tag=cls._TAG_MAX)

                dpg.add_spacer(width=20)
                dpg.add_text("Current: 0 m", tag=cls._TAG_CURRENT)
                dpg.add_spacer(width=20)

                with dpg.group(horizontal=False):
                    dpg.add_text("Delta: 0 m", tag=cls._TAG_DELTA)
                    dpg.add_spacer(width=10)
                    dpg.add_text("Median Delta: 0 m", tag=cls._TAG_MEDIAN_DELTA)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Stop Plot", callback=lambda: cls.stop_plot())

    @classmethod
    def stop_plot(cls) -> None:
        """Freeze the plot. Incoming data is still recorded but not drawn."""
        cls.plot_active = False
        log.info("AltitudeWindow: plot frozen by user")

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
        (min/max/current/delta), then repaints the DPG items.

        Parameters
        ----------
        source:
            ``"pressure"`` or ``"gnss"``.
        """
        if not cls.plot_active:
            return

        if source == "pressure":
            cls.time_data_pressure.append(time_value)
            cls.altitude_pressure_data.append(altitude_value)
            series_tag = cls._TAG_SERIES_PRESSURE
            source_data = cls.altitude_pressure_data
            source_time = cls.time_data_pressure
        else:
            cls.time_data_gnss.append(time_value)
            cls.altitude_gnss_data.append(altitude_value)
            series_tag = cls._TAG_SERIES_GNSS
            source_data = cls.altitude_gnss_data
            source_time = cls.time_data_gnss

        cls.altitude_current = altitude_value
        if cls.altitude_min is None or altitude_value < cls.altitude_min:
            cls.altitude_min = altitude_value
            log.debug("AltitudeWindow: new min = %.1f m (source=%s)", altitude_value, source)
        if cls.altitude_max is None or altitude_value > cls.altitude_max:
            cls.altitude_max = altitude_value
            log.debug("AltitudeWindow: new max = %.1f m (source=%s)", altitude_value, source)

        delta = altitude_value - source_data[-2] if len(source_data) > 1 else 0.0
        cls.delta_data.append(delta)
        median_delta = statistics.median(cls.delta_data) if cls.delta_data else 0.0

        dpg.set_value(series_tag, [source_time, source_data])
        dpg.fit_axis_data(cls._TAG_XAXIS)
        dpg.fit_axis_data(cls._TAG_YAXIS)

        dpg.set_value(cls._TAG_MIN, f"Min: {cls.altitude_min:.1f} m")
        dpg.set_value(cls._TAG_CURRENT, f"Current: {cls.altitude_current:.1f} m")
        dpg.set_value(cls._TAG_MAX, f"Max: {cls.altitude_max:.1f} m")
        dpg.set_value(cls._TAG_DELTA, f"Delta: {delta:.1f} m")
        dpg.set_value(cls._TAG_MEDIAN_DELTA, f"Median Delta: {median_delta:.1f} m")

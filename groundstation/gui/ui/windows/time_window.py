"""
time_window.py
--------------
Live clock displaying the current time in three mission-relevant time zones.

Updated every frame via a DearPyGui visible handler so the display ticks
without any manual polling from the main loop.

Time zones:
  - CET/CEST — Germany     (Europe/Berlin)
  - WET/WEST — Portugal    (Europe/Lisbon)
  - EST/EDT  — Eastern USA (America/New_York)
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)

_ZONES: list[tuple[str, str]] = [
    ("Germany  (CET/CEST)", "Europe/Berlin"),
    ("Portugal (WET/WEST)", "Europe/Lisbon"),
    ("USA East (EST/EDT)", "America/New_York"),
]


class TimeWindow:
    """Renders a live clock table showing time in three mission time zones."""

    _TIME_FORMAT = "%H:%M:%S"

    def __init__(self):
        self._time_tags: list[str] = []
        log.debug("%s: initialised", self.__class__.__name__)

    def draw_ui(self, window_width: int = 300, window_height: int = 160) -> None:
        """
        Create the mission-time child-window and attach the visible-handler tick.

        Call once during UI construction.
        """
        log.debug("TimeWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("Mission Time", color=(255, 255, 0))
            dpg.add_separator()
            dpg.add_spacer(height=4)

            table_tag = "time_window_table"
            with dpg.table(
                    tag=table_tag,
                    header_row=False,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    row_background=True,
                    resizable=True,
            ):
                dpg.add_table_column(label="Zone")
                dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=110)

                for i, (label, tz_name) in enumerate(_ZONES):
                    now = datetime.now(ZoneInfo(tz_name))
                    time_tag = f"time_window_time_{i}"
                    self._time_tags.append(time_tag)

                    with dpg.table_row():
                        dpg.add_text(label)
                        dpg.add_text(
                            now.strftime(self._TIME_FORMAT),
                            tag=time_tag,
                            color=(180, 220, 255, 255),
                        )

        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(callback=self._tick)
        dpg.bind_item_handler_registry(table_tag, handler)

    def _tick(self) -> None:
        """Update all time labels with the current time in each zone."""
        for i, (_, tz_name) in enumerate(_ZONES):
            now = datetime.now(ZoneInfo(tz_name))
            dpg.set_value(self._time_tags[i], now.strftime(self._TIME_FORMAT))

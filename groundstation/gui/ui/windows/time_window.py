"""
time_window.py
--------------
Live clock displaying the current time in three mission-relevant time zones
(Germany, Portugal, US East). Ticks every frame via a DearPyGui visible handler,
so it needs no telemetry and no manual polling.

Modular widget: per-instance tags, and the item-handler registry it creates is
deleted on teardown so a removed/reloaded clock leaves nothing behind.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import dearpygui.dearpygui as dpg

from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)

_ZONES: list[tuple[str, str]] = [
    ("Germany  (CET/CEST)", "Europe/Berlin"),
    ("Portugal (WET/WEST)", "Europe/Lisbon"),
    ("USA East (EST/EDT)", "America/New_York"),
]


class TimeWindow(Widget):
    """Live multi-timezone mission clock."""

    TYPE_ID = "time"
    DISPLAY_NAME = "Mission Time"
    DEFAULT_CELLS = (3, 2)
    MIN_CELLS = (3, 2)

    _TIME_FORMAT = "%H:%M:%S"

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self._handler_registry: int | None = None

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Mission Time"), color=(255, 255, 0))
        dpg.add_separator()
        dpg.add_spacer(height=4)

        with dpg.table(
                tag=self.tag("table"),
                header_row=False,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
                row_background=True, resizable=True,
        ):
            dpg.add_table_column(label="Zone")
            dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=110)

            for i, (label, tz_name) in enumerate(_ZONES):
                now = datetime.now(ZoneInfo(tz_name))
                with dpg.table_row():
                    dpg.add_text(label)
                    dpg.add_text(now.strftime(self._TIME_FORMAT), tag=self.tag(f"cell_{i}"),
                                 color=(180, 220, 255, 255))

        with dpg.item_handler_registry() as self._handler_registry:
            dpg.add_item_visible_handler(callback=self._tick)
        dpg.bind_item_handler_registry(self.tag("table"), self._handler_registry)

    def _tick(self) -> None:
        for i, (_, tz_name) in enumerate(_ZONES):
            now = datetime.now(ZoneInfo(tz_name))
            dpg.set_value(self.tag(f"cell_{i}"), now.strftime(self._TIME_FORMAT))

    def destroy(self) -> None:
        if self._handler_registry is not None and dpg.does_item_exist(self._handler_registry):
            dpg.delete_item(self._handler_registry)
        self._handler_registry = None
        super().destroy()

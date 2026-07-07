"""
flight_events_window.py
-----------------------
Sequential flight-event status table.

Event labels and the abort threshold come from SettingsManager. Modular widget:
subscribes to ``tele/status_events`` (mark an event done/ABORT), ``flight/armed``
(reset on arm and disarm), and ``settings/flight_events/changed`` (rebuild the
table with new labels). Per-instance tags, so multiple event tables can coexist.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class FlightEventWindow(Widget):
    """Flight-event status table driven by the telemetry bus."""

    TYPE_ID = "flight_events"
    DISPLAY_NAME = "Flight Events"
    DEFAULT_CELLS = (4, 5)
    MIN_CELLS = (3, 3)

    COLOR_PENDING = (200, 200, 200, 255)
    COLOR_COMPLETE = (0, 255, 0, 255)
    COLOR_ABORT = (255, 0, 0, 255)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self.current_event = -1
        self._row_count = 0

    def _event_config(self) -> tuple[list[dict], int]:
        fe = self.ctx.settings.data.get("flight_events", {})
        events = fe.get("events", [])
        abort_threshold = fe.get("abort_threshold", len(events))
        return events, abort_threshold

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Flight Event Status"), color=(255, 255, 0))
        dpg.add_separator()
        dpg.add_group(tag=self.tag("holder"))
        self._render_table()

        self.subscribe(topics.tele("status_events"), self._on_event)
        self.subscribe(topics.FLIGHT_ARMED, lambda _=None: self.reset())
        self.subscribe(topics.settings_changed("flight_events"), lambda _=None: self._render_table())

    def _render_table(self) -> None:
        holder = self.tag("holder")
        dpg.delete_item(holder, children_only=True)
        self.current_event = -1
        events, abort_threshold = self._event_config()
        self._row_count = len(events)

        with dpg.table(parent=holder, header_row=True,
                       borders_innerH=True, borders_outerH=True,
                       borders_innerV=True, borders_outerV=True, row_background=True):
            dpg.add_table_column(label="#", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="Event", width_stretch=True)
            dpg.add_table_column(label="State", width_fixed=True, init_width_or_weight=95)

            for i, evt in enumerate(events):
                label = evt.get("label", f"Event {i}")
                with dpg.table_row():
                    dpg.add_text(f"{i:02d}")
                    dpg.add_text(label)
                    dpg.add_text("-", tag=self.tag(f"row_{i}"), color=self.COLOR_PENDING)

    def _on_event(self, sample) -> None:
        event_number = int(sample.value)
        self.current_event = event_number
        events, abort_threshold = self._event_config()
        if not (0 <= event_number < self._row_count):
            return
        if event_number < len(events):
            is_abort = events[event_number].get("is_abort", event_number >= abort_threshold)
        else:
            is_abort = event_number >= abort_threshold
        color = self.COLOR_ABORT if is_abort else self.COLOR_COMPLETE
        label = "⚠ ABORT" if is_abort else "✓ done"
        tag = self.tag(f"row_{event_number}")
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, default_value=label, color=color)

    def reset(self) -> None:
        """Clear every event indicator back to pending (on arm and disarm)."""
        self.current_event = -1
        for i in range(self._row_count):
            tag = self.tag(f"row_{i}")
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, default_value="-", color=self.COLOR_PENDING)

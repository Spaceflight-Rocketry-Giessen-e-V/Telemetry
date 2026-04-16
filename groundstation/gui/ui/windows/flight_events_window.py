"""
flight_events_window.py
-----------------------
Sequential flight-event status table.

Event labels and the abort-threshold index are read from SettingsManager so
they can be edited in the Settings tab without modifying source code. Each
event is shown as pending, done (green), or ABORT (red) depending on the
current event index and the abort threshold.
"""

import itertools
import logging

import dearpygui.dearpygui as dpg

from ui.settings_manager import settings

log = logging.getLogger(__name__)


class FlightEventWindow:
    """Renders a flight-event status table and tracks the current event index."""

    COLOR_PENDING = (200, 200, 200, 255)  # grey  — not yet reached
    COLOR_COMPLETE = (0, 255, 0, 255)  # green — successfully passed
    COLOR_ABORT = (255, 0, 0, 255)  # red   — abort-level event

    # Class-level counter so multiple instances produce unique DPG tags.
    _id_counter = itertools.count()

    def __init__(self, instance_id: str | None = None):
        uid = instance_id if instance_id is not None else str(next(self._id_counter))

        self.current_event = -1
        self._row_tags: list[str] = []
        self._uid = uid

        log.debug("FlightEventWindow[%s]: initialised", uid)

    @staticmethod
    def _event_config() -> tuple[list[dict], int]:
        """
        Return ``(events, abort_threshold)`` from settings.

        ``events`` is a list of ``{"label": str, "is_abort": bool}`` dicts.
        ``abort_threshold`` is the first index at which ``is_abort`` is True.
        """
        fe = settings.data.get("flight_events", {})
        events = fe.get("events", [])
        abort_threshold = fe.get("abort_threshold", len(events))
        return events, abort_threshold

    def draw_ui(self, window_width: int = 400, window_height: int = 400) -> None:
        """
        Build the flight-event table.

        Row tags are derived from the event list in settings, so calling this
        after a settings change will reflect updated labels.
        """
        log.debug("FlightEventWindow[%s]: drawing UI (%dx%d)", self._uid, window_width, window_height)

        events, abort_threshold = self._event_config()
        self._row_tags = [f"flight_event_{self._uid}_{i}" for i in range(len(events))]

        with dpg.child_window(label="Flight Events", width=window_width, height=window_height):
            dpg.add_text("Flight Event Status", color=(255, 255, 0))
            dpg.add_separator()

            with dpg.table(
                    header_row=True,
                    borders_innerH=True, borders_outerH=True,
                    borders_innerV=True, borders_outerV=True,
                    row_background=True,
            ):
                dpg.add_table_column(label="#", width_fixed=True, init_width_or_weight=30)
                dpg.add_table_column(label="Event", width_stretch=True)
                dpg.add_table_column(label="State", width_fixed=True, init_width_or_weight=80)

                for i, evt in enumerate(events):
                    label = evt.get("label", f"Event {i}")
                    is_abort = evt.get("is_abort", i >= abort_threshold)

                    with dpg.table_row():
                        dpg.add_text(f"{i:02d}")
                        dpg.add_text(label)
                        dpg.add_text(
                            "-",
                            tag=self._row_tags[i],
                            color=self.COLOR_PENDING,
                        )

        log.debug("FlightEventWindow[%s]: %d events rendered, abort_threshold=%d",
                  self._uid, len(events), abort_threshold)

    def update_event(self, event_number: int) -> None:
        """
        Update the display for *event_number* only.

        Only the specified event is marked done or ABORT.
        All other events are left in their current state.
        """
        _, abort_threshold = self._event_config()

        if event_number != self.current_event:
            log.info("FlightEventWindow[%s]: event updated %d → %d",
                     self._uid, self.current_event, event_number)

        self.current_event = event_number

        if 0 <= event_number < len(self._row_tags):
            tag = self._row_tags[event_number]
            is_abort = event_number >= abort_threshold
            color = self.COLOR_ABORT if is_abort else self.COLOR_COMPLETE
            label = "ABORT" if is_abort else "done"
            if is_abort:
                log.warning("FlightEventWindow[%s]: abort event reached at index %d", self._uid, event_number)
            dpg.configure_item(tag, default_value=label, color=color)
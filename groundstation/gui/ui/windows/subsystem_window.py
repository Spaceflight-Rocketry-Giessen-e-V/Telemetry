"""
subsystem_window.py
-------------------
Subsystem status box — a red/green indicator per bit of the ``subsystem_status``
telemetry field (LSB first: Sensorics 1, Sensorics 2, Recovery). A set bit is
green (OK), a clear bit is red; indicators start grey until the first packet.

Each indicator is a small filled rectangle on its own drawlist, so it does not
depend on any particular glyph in the UI font. Modular widget: subscribes to
``tele/subsystem_status``; every tag is per-instance.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class SubsystemWindow(Widget):
    """One red/green box per subsystem bit, driven by the telemetry bus."""

    TYPE_ID = "subsystem"
    DISPLAY_NAME = "Subsystem Status"
    DEFAULT_CELLS = (4, 2)
    MIN_CELLS = (2, 2)

    COLOR_OK = (0, 200, 0, 255)
    COLOR_FAULT = (200, 0, 0, 255)
    COLOR_UNKNOWN = (110, 110, 110, 255)
    COLOR_BORDER = (0, 0, 0, 255)

    # (display label, bit index)
    DEFAULT_SUBSYSTEMS: list[tuple[str, int]] = [
        ("Sensorics 1", 0),
        ("Sensorics 2", 1),
        ("Recovery", 2),
    ]

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        # Config may override the bit→label mapping; default is the flight layout.
        self.subsystems = [tuple(x) for x in self.config.get("subsystems", self.DEFAULT_SUBSYSTEMS)]

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Subsystem Status"), color=(255, 255, 0))
        dpg.add_separator()
        dpg.add_spacer(height=4)

        for label, bit in self.subsystems:
            with dpg.group(horizontal=True):
                with dpg.drawlist(width=20, height=20):
                    dpg.draw_rectangle(
                        (2, 2), (18, 18),
                        fill=self.COLOR_UNKNOWN,
                        color=self.COLOR_BORDER,
                        tag=self.tag(f"box_{bit}"),
                    )
                dpg.add_text(label)
            dpg.add_spacer(height=4)

        self.subscribe(topics.tele("subsystem_status"), self._on_status)

    def _on_status(self, sample) -> None:
        status = int(sample.value)
        for _, bit in self.subsystems:
            box = self.tag(f"box_{bit}")
            if dpg.does_item_exist(box):
                ok = bool(status & (1 << bit))
                dpg.configure_item(box, fill=self.COLOR_OK if ok else self.COLOR_FAULT)
        log.debug("SubsystemWindow[%s]: status=%d", self.iid, status)

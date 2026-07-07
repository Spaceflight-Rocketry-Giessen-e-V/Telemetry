"""
subsystem_window.py
-------------------
Subsystem status box — a red/green indicator per bit of the ``subsystem_status``
telemetry field.

Bit → subsystem mapping (LSB first)::

    bit 0 → Sensorics 1
    bit 1 → Sensorics 2
    bit 2 → Recovery

A set bit is shown green (OK); a clear bit is shown red (fault/inactive).
Indicators start grey until the first status packet arrives. Each indicator is
a small filled rectangle drawn on its own drawlist, so it does not depend on
any particular glyph being present in the UI font.
"""

import logging

import dearpygui.dearpygui as dpg

log = logging.getLogger(__name__)


class SubsystemWindow:
    """Renders one red/green box per subsystem bit and updates it per packet."""

    COLOR_OK = (0, 200, 0, 255)        # green — bit set
    COLOR_FAULT = (200, 0, 0, 255)     # red   — bit clear
    COLOR_UNKNOWN = (110, 110, 110, 255)  # grey — no data yet
    COLOR_BORDER = (0, 0, 0, 255)

    # (display label, bit index)
    SUBSYSTEMS: list[tuple[str, int]] = [
        ("Sensorics 1", 0),
        ("Sensorics 2", 1),
        ("Recovery", 2),
    ]

    def __init__(self):
        self._box_tags: dict[int, str] = {}
        log.debug("%s: initialised", self.__class__.__name__)

    def draw_ui(self, window_width: int = 400, window_height: int = 150) -> None:
        """Create the subsystem-status child-window. Call once during UI construction."""
        log.debug("SubsystemWindow: drawing UI (%dx%d)", window_width, window_height)

        with dpg.child_window(width=window_width, height=window_height):
            dpg.add_text("Subsystem Status", color=(255, 255, 0))
            dpg.add_separator()
            dpg.add_spacer(height=4)

            for label, bit in self.SUBSYSTEMS:
                box_tag = f"subsystem_box_{bit}"
                self._box_tags[bit] = box_tag
                with dpg.group(horizontal=True):
                    with dpg.drawlist(width=20, height=20):
                        dpg.draw_rectangle(
                            (2, 2), (18, 18),
                            fill=self.COLOR_UNKNOWN,
                            color=self.COLOR_BORDER,
                            tag=box_tag,
                        )
                    dpg.add_text(label)
                dpg.add_spacer(height=4)

    def update_status(self, status: int) -> None:
        """Colour each indicator green (bit set) or red (bit clear)."""
        for _, bit in self.SUBSYSTEMS:
            box_tag = self._box_tags.get(bit)
            if box_tag and dpg.does_item_exist(box_tag):
                ok = bool(status & (1 << bit))
                dpg.configure_item(box_tag, fill=self.COLOR_OK if ok else self.COLOR_FAULT)
        log.debug("SubsystemWindow: status=%d (0b%s)", status, format(status, "03b"))

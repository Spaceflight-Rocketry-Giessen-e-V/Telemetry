"""
pump.py
-------
The manual render loop that replaces the blocking ``dpg.start_dearpygui()``.

Running the loop by hand lets us drain the telemetry bus once per frame *on the
UI thread*, which is the whole point of the bus: background threads only enqueue,
and every subscriber callback (and therefore every ``dpg.*`` call inside it) runs
here, on the render thread.

Behaviourally this is a drop-in for ``start_dearpygui()``: it blocks until
``dpg.stop_dearpygui()`` is called (e.g. by the Escape handler or the viewport
close button), at which point ``is_dearpygui_running()`` goes false and the loop
returns so the caller can run its shutdown/teardown as before.
"""

import logging
from typing import Callable, Optional

import dearpygui.dearpygui as dpg

from ui.core.bus import TelemetryBus

log = logging.getLogger(__name__)


def run_render_loop(bus: TelemetryBus, on_frame: Optional[Callable[[], None]] = None) -> None:
    """
    Drive DearPyGui frame-by-frame, draining *bus* before each rendered frame.

    Parameters
    ----------
    bus:
        The telemetry bus to pump once per frame.
    on_frame:
        Optional hook run after the pump and before rendering (diagnostics,
        periodic housekeeping). Kept lightweight — it runs every frame.

    The viewport must already be set up and shown by the caller.
    """
    log.info("pump: entering manual render loop")
    frames = 0
    while dpg.is_dearpygui_running():
        try:
            bus.pump()
            if on_frame is not None:
                on_frame()
        except Exception:  # noqa: BLE001 — never let a frame's work kill the loop
            log.error("pump: error during frame work", exc_info=True)
        dpg.render_dearpygui_frame()
        frames += 1
    log.info("pump: render loop exited after %d frames", frames)

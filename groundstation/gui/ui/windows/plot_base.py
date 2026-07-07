"""
plot_base.py
------------
Shared Stop / Resume / Reset behaviour for live-plot widgets.

Replaces the old class-level ``PlotCoordinator`` singleton. Control is now
carried on the bus: a widget's Stop/Reset buttons publish ``plot/stop`` /
``plot/resume`` / ``plot/reset``, and every plot instance subscribes to those
topics, so one click still freezes/resets *all* coordinated plots at once and
keeps their button labels in sync — but through fan-out, not shared class state,
so two independent plots can coexist.

The mission clock is rebased on ``plot/reset`` by :class:`~ui.core.serial_service.SerialService`,
so plots only clear their own series here.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class PlotWidgetBase(Widget):
    """Base for coordinated live-plot widgets."""

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self.active = True

    # -- controls -------------------------------------------------------------

    def _build_plot_controls(self) -> None:
        """Add the Stop/Resume and Reset buttons (call inside build)."""
        dpg.add_button(label="Stop Plot", tag=self.tag("stop_btn"), width=100, callback=self._toggle)
        dpg.add_button(label="Reset Plot", width=100,
                       callback=lambda: self.ctx.bus.publish(topics.PLOT_RESET, None))

    def _subscribe_plot_control(self) -> None:
        """Subscribe to the shared plot-control topics (call inside build)."""
        self.subscribe(topics.PLOT_STOP, self._on_stop)
        self.subscribe(topics.PLOT_RESUME, self._on_resume)
        # Both reset (user button) and clear (on arm) wipe the series + resume;
        # they differ only in whether the mission clock is rebased, which is
        # SerialService's concern, not the plot's.
        self.subscribe(topics.PLOT_RESET, self._on_reset)
        self.subscribe(topics.PLOT_CLEAR, self._on_reset)

    def _toggle(self) -> None:
        self.ctx.bus.publish(topics.PLOT_STOP if self.active else topics.PLOT_RESUME, None)

    def _set_btn_label(self, label: str) -> None:
        if dpg.does_item_exist(self.tag("stop_btn")):
            dpg.set_item_label(self.tag("stop_btn"), label)

    def _on_stop(self, _=None) -> None:
        self.active = False
        self._set_btn_label("Resume Plot")

    def _on_resume(self, _=None) -> None:
        self.active = True
        self._set_btn_label("Stop Plot")

    def _on_reset(self, _=None) -> None:
        self.active = True
        self._set_btn_label("Stop Plot")
        self._clear()
        log.info("%s[%s]: reset", self.TYPE_ID, self.iid)

    # -- subclass hook --------------------------------------------------------

    def _clear(self) -> None:
        """Clear series data + statistics. Implemented by the concrete plot."""
        raise NotImplementedError

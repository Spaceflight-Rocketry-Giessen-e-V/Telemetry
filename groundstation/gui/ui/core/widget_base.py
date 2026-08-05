"""
widget_base.py
--------------
Base class for every dashboard widget.

The whole modular dashboard rests on two rules this class enforces:

1. **Per-instance tag namespacing.** Every DearPyGui tag a widget uses flows
   through :py:meth:`tag`, which prefixes it with the widget's ``TYPE_ID`` and
   its unique ``iid``. No two instances can ever produce the same tag, so the
   old hardcoded-global-tag collisions (``"battery_bar"``, ``"xaxis"``, …) —
   which forced widgets to be de-facto singletons — simply cannot happen. Two
   batteries, two altitude plots, two maps: all fine.

2. **Owned lifecycle.** The layout engine calls :py:meth:`mount` (which creates
   the widget's root ``child_window`` at the geometry the grid computed and then
   runs the subclass :py:meth:`build`), and :py:meth:`destroy` (which
   unsubscribes every bus subscription and deletes the root). A widget therefore
   cleans up after itself when a dashboard is reloaded or a widget is removed.

Subclasses implement :py:meth:`build` (populate the current container + subscribe
to bus topics) and, if they hold external resources (threads, sockets), override
:py:meth:`destroy` to release them before calling ``super().destroy()``.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

import dearpygui.dearpygui as dpg

from ui.core.services import ServiceHub

log = logging.getLogger(__name__)


class Widget(ABC):
    """Abstract, instance-safe dashboard widget."""

    # -- class-level metadata (drives the registry + add-widget catalog) ------
    TYPE_ID: str = ""            # stable JSON identifier, e.g. "battery"
    DISPLAY_NAME: str = ""       # human label, e.g. "Battery Voltage"
    DEFAULT_CELLS: tuple[int, int] = (3, 3)   # (colspan, rowspan)
    MIN_CELLS: tuple[int, int] = (1, 1)
    SINGLETON: bool = False      # True → registry refuses a second instance
    BORDER: bool = True          # draw a border around the root child_window

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None) -> None:
        self.iid = iid
        self.ctx = ctx
        self.config = dict(config or {})
        self._subs: list[int] = []
        self._root = self.tag("root")
        log.debug("%s[%s]: constructed", self.TYPE_ID, self.iid)

    # -- tag namespacing ------------------------------------------------------

    def tag(self, name: str) -> str:
        """
        Namespaced DPG tag: ``"{TYPE_ID}__{iid}__{name}"``.

        This is the *only* way a widget should produce a tag. Passing a literal
        string tag to ``dpg.add_*`` re-introduces the collision bug.
        """
        return f"{self.TYPE_ID}__{self.iid}__{name}"

    # -- bus helpers ----------------------------------------------------------

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """Subscribe to a bus topic and remember the token for teardown."""
        self._subs.append(self.ctx.bus.subscribe(topic, callback))

    # -- lifecycle ------------------------------------------------------------

    def mount(self, canvas: str, x: int, y: int, width: int, height: int) -> None:
        """
        Create the root ``child_window`` at (x, y) sized (width, height) inside
        *canvas*, then run :py:meth:`build` to populate it.

        Called by the layout engine. The grid owns pixel geometry; the widget
        owns content. Positions are absolute within the (scrollable) canvas.
        """
        with dpg.child_window(
                tag=self._root,
                parent=canvas,
                pos=(x, y),
                width=width,
                height=height,
                border=self.BORDER,
        ):
            self.build(width, height)
        # Opt-in compact font for dense widgets, bound to the root so it cascades
        # to all content. Falls back silently if no small font was provided.
        if self.config.get("compact") and getattr(self.ctx, "font_small", None):
            dpg.bind_item_font(self._root, self.ctx.font_small)
        log.debug("%s[%s]: mounted at (%d,%d) %dx%d", self.TYPE_ID, self.iid, x, y, width, height)

    def relayout(self, x: int, y: int, width: int, height: int) -> None:
        """Reposition/resize the root (called on viewport resize)."""
        if dpg.does_item_exist(self._root):
            dpg.configure_item(self._root, pos=[x, y], width=width, height=height)

    @abstractmethod
    def build(self, width: int, height: int) -> None:
        """
        Populate the current container (the root child_window is on the stack)
        and subscribe to bus topics.

        Add items with no explicit ``parent`` so they land in the root, or pass
        ``parent=self._root``. Create every tag via :py:meth:`tag`.
        """

    def on_config_changed(self, config: dict) -> None:
        """Live-refresh after a settings/config change. Default: store it."""
        self.config = dict(config)

    def get_config(self) -> dict:
        """Return the per-instance config blob to serialize into the dashboard JSON."""
        return dict(self.config)

    def set_locked(self, locked: bool) -> None:
        """
        Freeze/unfreeze the widget root (Lock Layout during flight).

        No-op for the config-driven MVP where nothing is draggable, but wired so
        an interactive engine can flip ``no_move``/``no_resize`` later.
        """

    def destroy(self) -> None:
        """Unsubscribe every bus token and delete the root (and its children)."""
        for token in self._subs:
            self.ctx.bus.unsubscribe(token)
        self._subs.clear()
        if dpg.does_item_exist(self._root):
            dpg.delete_item(self._root)
        log.debug("%s[%s]: destroyed", self.TYPE_ID, self.iid)

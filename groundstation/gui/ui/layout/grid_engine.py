"""
grid_engine.py
--------------
Renders a dashboard document as widgets placed on a fluid fixed-cell grid.

The engine creates one scrollable *canvas* ``child_window`` inside the parent
container (a tab), then for every widget entry: resolves the type against the
registry, constructs it with its persisted ``iid`` and ``config``, computes its
pixel rect from the grid, and mounts it. On viewport resize it recomputes the
fluid column width and repositions every widget.

This engine is *config-driven only* — dashboards come from JSON and there is no
runtime drag/resize editor. ``teardown_all`` + ``load`` is enough to hot-reload
a hand-edited dashboard file.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core.registry import WidgetRegistry
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget
from ui.layout import grid_math
from ui.layout.grid_math import GridSpec

log = logging.getLogger(__name__)

# Horizontal slack subtracted from the viewport width so widgets never overflow
# the canvas into a horizontal scrollbar (accounts for the vertical scrollbar +
# child padding).
_WIDTH_SLACK = 24


class GridLayoutEngine:
    """Places registry-resolved widgets from a dashboard doc onto a grid."""

    def __init__(self, registry: WidgetRegistry, ctx: ServiceHub) -> None:
        self._registry = registry
        self._ctx = ctx
        self._spec = GridSpec()
        self._canvas: str | None = None
        # Parallel lists of live widgets and their placed cell rects.
        self._widgets: list[Widget] = []
        self._rects: list[grid_math.CellRect] = []
        self._locked = False

    # -- load / teardown ------------------------------------------------------

    def load(self, doc: dict, parent: str, canvas_tag: str = "grid_canvas") -> None:
        """
        Build every widget in *doc* into a fresh canvas under *parent*.

        Skips (with a warning) any widget whose ``type`` is not registered or
        whose ``iid`` duplicates one already placed, rather than aborting the
        whole dashboard.
        """
        self.teardown_all()
        self._spec = GridSpec(**doc["grid"])
        self._canvas = canvas_tag

        dpg.add_child_window(tag=canvas_tag, parent=parent, width=-1, height=-1, border=False)

        vw = self._viewport_w()
        placed: set[tuple[str, str]] = set()
        for entry in doc["widgets"]:
            type_id, iid = entry["type"], entry["iid"]
            if not self._registry.is_registered(type_id):
                log.warning("grid: skipping unknown widget type %r (iid=%s)", type_id, iid)
                continue
            if (type_id, iid) in placed:
                log.warning("grid: skipping duplicate (type, iid) (%r, %r)", type_id, iid)
                continue
            rect: grid_math.CellRect = tuple(entry["cell"])  # type: ignore[assignment]
            try:
                widget = self._registry.create(type_id, iid, self._ctx, entry.get("config", {}))
                x, y, w, h = grid_math.cell_to_px(self._spec, rect, vw)
                widget.mount(canvas_tag, x, y, w, h)
            except Exception:  # noqa: BLE001 — one bad widget must not kill the dashboard
                log.error("grid: failed to build widget %r (iid=%s)", type_id, iid, exc_info=True)
                continue
            self._widgets.append(widget)
            self._rects.append(rect)
            placed.add((type_id, iid))

        clashes = grid_math.find_overlaps(self._rects)
        if clashes:
            log.warning("grid: %d overlapping widget placement(s): %s", len(clashes), clashes)

        log.info("grid: loaded dashboard '%s' — %d widget(s) placed",
                 doc.get("name"), len(self._widgets))

    def teardown_all(self) -> None:
        """Destroy every live widget (unsubscribe + delete) and drop the canvas."""
        for widget in self._widgets:
            try:
                widget.destroy()
            except Exception:  # noqa: BLE001
                log.error("grid: error destroying widget %s[%s]", widget.TYPE_ID, widget.iid, exc_info=True)
        self._widgets.clear()
        self._rects.clear()
        if self._canvas and dpg.does_item_exist(self._canvas):
            dpg.delete_item(self._canvas)
        self._canvas = None

    # -- responsive relayout --------------------------------------------------

    def on_viewport_resize(self) -> None:
        """Recompute fluid columns and reposition every widget. Bind to the DPG resize callback."""
        vw = self._viewport_w()
        for widget, rect in zip(self._widgets, self._rects):
            x, y, w, h = grid_math.cell_to_px(self._spec, rect, vw)
            widget.relayout(x, y, w, h)

    def set_locked(self, locked: bool) -> None:
        """Lock/unlock every widget (freeze the dashboard during flight)."""
        self._locked = locked
        for widget in self._widgets:
            widget.set_locked(locked)

    # -- helpers --------------------------------------------------------------

    def _viewport_w(self) -> float:
        try:
            vw = dpg.get_viewport_client_width()
        except Exception:  # noqa: BLE001 — viewport may not exist yet (headless tests)
            vw = 1920
        return max(1.0, vw - _WIDTH_SLACK)

    @property
    def widgets(self) -> list[Widget]:
        return list(self._widgets)

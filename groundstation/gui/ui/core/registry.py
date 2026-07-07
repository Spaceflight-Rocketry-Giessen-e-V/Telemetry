"""
registry.py
-----------
Maps a widget ``TYPE_ID`` to its class so dashboards can be built from JSON.

The layout engine looks up ``type`` strings from a dashboard file here and
constructs instances; an "add widget" catalog (future) enumerates
:py:meth:`meta`. Unknown types are reported by :py:meth:`create` raising
``KeyError`` — the engine catches it and skips the widget with a warning rather
than crashing the whole dashboard.
"""

import logging

from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class WidgetRegistry:
    """Registry of widget classes keyed by ``TYPE_ID``."""

    def __init__(self) -> None:
        self._types: dict[str, type[Widget]] = {}

    def register(self, cls: type[Widget]) -> type[Widget]:
        """Register a Widget subclass. Usable as a decorator; returns *cls*."""
        if not cls.TYPE_ID:
            raise ValueError(f"{cls.__name__} has no TYPE_ID")
        if cls.TYPE_ID in self._types and self._types[cls.TYPE_ID] is not cls:
            log.warning("registry: TYPE_ID %r re-registered (%s → %s)",
                        cls.TYPE_ID, self._types[cls.TYPE_ID].__name__, cls.__name__)
        self._types[cls.TYPE_ID] = cls
        log.debug("registry: registered %r → %s", cls.TYPE_ID, cls.__name__)
        return cls

    def is_registered(self, type_id: str) -> bool:
        return type_id in self._types

    def get(self, type_id: str) -> type[Widget]:
        return self._types[type_id]

    def create(self, type_id: str, iid: str, ctx: ServiceHub, config: dict | None = None) -> Widget:
        """Instantiate a widget by type. Raises ``KeyError`` for unknown types."""
        cls = self._types[type_id]
        return cls(iid, ctx, config or {})

    def meta(self) -> list[dict]:
        """Catalog of registered widget types (for an add-widget palette)."""
        return [
            {
                "type_id": cls.TYPE_ID,
                "name": cls.DISPLAY_NAME,
                "default_cells": cls.DEFAULT_CELLS,
                "min_cells": cls.MIN_CELLS,
                "singleton": cls.SINGLETON,
            }
            for cls in self._types.values()
        ]

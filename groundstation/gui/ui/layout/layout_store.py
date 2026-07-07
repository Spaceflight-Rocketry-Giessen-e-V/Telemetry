"""
layout_store.py
---------------
Load and save dashboard documents (JSON), separate from ``settings.json``.

A dashboard is a versioned document::

    {
      "schema": 1,
      "name": "flight-default",
      "grid": { "cols": 12, "cell_h": 80, "gutter": 8, "margin": 12 },
      "widgets": [
        { "type": "battery", "iid": "b7d20114", "cell": [6, 0, 3, 3],
          "config": { "title": "Main Pack" } }
      ]
    }

``cell`` is ``[col, row, colspan, rowspan]``. ``iid`` is a stable per-instance id
(persisted so a widget's namespaced tags survive save/reload). ``config`` is the
opaque per-instance blob a widget round-trips via ``get_config()``.

This module only does IO + light structural validation; the engine resolves
``type`` against the registry and reports unknown types.
"""

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1

# Repo-root-relative dashboards directory (…/gui/dashboards).
DASHBOARDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboards")


class DashboardError(ValueError):
    """Raised when a dashboard document is structurally invalid."""


def dashboard_path(name: str) -> str:
    """Absolute path to a named dashboard file under :data:`DASHBOARDS_DIR`."""
    return os.path.join(DASHBOARDS_DIR, f"{name}.json")


def validate(doc: Any) -> dict:
    """
    Structurally validate a loaded dashboard doc and return it unchanged.

    Checks the top-level shape and each widget entry; does NOT check widget
    types against the registry (the engine does that so it can skip unknowns
    without failing the whole load).
    """
    if not isinstance(doc, dict):
        raise DashboardError("dashboard root must be an object")
    if doc.get("schema") != SCHEMA_VERSION:
        raise DashboardError(f"unsupported schema {doc.get('schema')!r}; expected {SCHEMA_VERSION}")
    grid = doc.get("grid")
    if not isinstance(grid, dict):
        raise DashboardError("dashboard 'grid' must be an object")
    widgets = doc.get("widgets")
    if not isinstance(widgets, list):
        raise DashboardError("dashboard 'widgets' must be a list")

    # Tags are namespaced as ``TYPE_ID__iid__name``, so an iid only has to be
    # unique within a widget type — different types may reuse the same iid.
    seen_keys: set[tuple[str, str]] = set()
    for i, w in enumerate(widgets):
        if not isinstance(w, dict):
            raise DashboardError(f"widget[{i}] must be an object")
        for key in ("type", "iid", "cell"):
            if key not in w:
                raise DashboardError(f"widget[{i}] missing '{key}'")
        cell = w["cell"]
        if not (isinstance(cell, list) and len(cell) == 4 and all(isinstance(n, int) for n in cell)):
            raise DashboardError(f"widget[{i}] 'cell' must be [col,row,colspan,rowspan] ints")
        key = (w["type"], w["iid"])
        if key in seen_keys:
            raise DashboardError(f"duplicate widget (type, iid) {key!r}")
        seen_keys.add(key)
        w.setdefault("config", {})
    return doc


def load_dashboard(path: str) -> dict:
    """Read and validate a dashboard document from *path*."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    validate(doc)
    log.info("Dashboard '%s' loaded (%d widgets) from %s",
             doc.get("name"), len(doc["widgets"]), path)
    return doc


def save_dashboard(path: str, doc: dict) -> None:
    """Validate and atomically write a dashboard document to *path*."""
    validate(doc)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    log.info("Dashboard '%s' saved to %s", doc.get("name"), path)

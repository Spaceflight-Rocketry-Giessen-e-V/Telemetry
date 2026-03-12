"""
settings_manager.py
-------------------
Centralised settings store for the Ground Station GUI.

All configurable values are defined here as defaults. On first run, a
``settings.json`` file is created from those defaults. On every subsequent
launch the file is read back so user preferences persist across sessions.

Usage::

    from settings_manager import settings  # singleton instance

    v = settings.get("battery.voltage_min")
    settings.set("battery.voltage_min", 5.2)  # persists to disk immediately
"""

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# Path to the on-disk settings file, co-located with this module.
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Default values used when no settings.json exists yet.
DEFAULTS: dict[str, Any] = {
    "battery": {
        "voltage_min": 5.4,
        "voltage_max": 8.4,
        "voltage_critical": 5.6,
    },
    "connection": {
        "rssi_min": -110,
        "rssi_max": -30,
        "rssi_warn": -90,
    },
    # Each entry: {"label": str, "is_abort": bool}
    "flight_events": {
        "abort_threshold": 14,
        "events": [
            {"label": "50 m", "is_abort": False},
            {"label": "100 m", "is_abort": False},
            {"label": "150 m", "is_abort": False},
            {"label": "200 m", "is_abort": False},
            {"label": "Armed", "is_abort": False},
            {"label": "Liftoff detected", "is_abort": False},
            {"label": "Booster burnout detected", "is_abort": False},
            {"label": "Drogue deployed (apogee)", "is_abort": False},
            {"label": "Drogue deployed (timer)", "is_abort": False},
            {"label": "Drogue deployed (command)", "is_abort": False},
            {"label": "Main deployed (altitude)", "is_abort": False},
            {"label": "Main deployed (timer)", "is_abort": False},
            {"label": "Main deployed (command)", "is_abort": False},
            {"label": "Landing detected", "is_abort": False},
        ],
    },
    # Each group: {"group": str, "commands": [{"label": str, "code": str}]}
    "commands": {
        "groups": [
            {
                "group": "Ping",
                "commands": [{"label": "Ping", "code": "p"}],
            },
            {
                "group": "Main Chute (m)",
                "commands": [
                    {"label": "50m", "code": "a"},
                    {"label": "100m", "code": "b"},
                    {"label": "150m", "code": "c"},
                    {"label": "200m", "code": "d"},
                ],
            },
            {
                "group": "Low Power",
                "commands": [
                    {"label": "ON", "code": "l"},
                    {"label": "OFF", "code": "m"},
                ],
            },
            {
                "group": "Flight Mode",
                "commands": [
                    {"label": "ARM", "code": "f"},
                    {"label": "DISARM", "code": "g"},
                ],
            },
            {
                "group": "Parachutes",
                "commands": [
                    {"label": "Drogue", "code": "q"},
                    {"label": "Main", "code": "r"},
                ],
            },
        ],
    },
}


class SettingsManager:
    """
    Thread-safe (read-heavy) key/value store backed by ``settings.json``.

    Keys use dot-notation for nested access, e.g. ``"battery.voltage_min"``.
    The full settings dict is also accessible directly via :attr:`data`.
    """

    def __init__(self, path: str = SETTINGS_FILE):
        self._path = path
        self.data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Read settings.json, merging stored values onto defaults so new keys are always present."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self.data = self._deep_merge(DEFAULTS, stored)
                log.info("Settings loaded from '%s'", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                log.error("Failed to read settings file (%s); using defaults", exc)
                self.data = self._deep_merge(DEFAULTS, {})
        else:
            log.info("No settings file found — creating defaults at '%s'", self._path)
            self.data = self._deep_merge(DEFAULTS, {})
            self._save()

    def _save(self) -> None:
        """Serialise current data to disk."""
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2, ensure_ascii=False)
            log.debug("Settings saved to '%s'", self._path)
        except OSError as exc:
            log.error("Failed to write settings file: %s", exc)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """
        Retrieve a value by dot-separated key path.

        Example::

            settings.get("battery.voltage_min")  # → 5.4
        """
        parts = dotted_key.split(".")
        node = self.data
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                log.warning("Settings key '%s' not found; returning default", dotted_key)
                return default
        return node

    def set(self, dotted_key: str, value: Any) -> None:
        """
        Update a single value by dot-separated key path and persist to disk.

        Example::

            settings.set("battery.voltage_critical", 5.5)
        """
        parts = dotted_key.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        old = node.get(parts[-1])
        node[parts[-1]] = value
        log.debug("Setting '%s' changed: %s → %s", dotted_key, old, value)
        self._save()

    def set_section(self, section: str, value: Any) -> None:
        """Replace an entire top-level section and persist to disk."""
        old_keys = list(self.data.get(section, {}).keys()) if isinstance(self.data.get(section), dict) else []
        self.data[section] = value
        log.info("Settings section '%s' replaced (keys were: %s)", section, old_keys)
        self._save()

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Recursively merge *override* into *base*, returning a new dict."""
        result = dict(base)
        for key, val in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = SettingsManager._deep_merge(result[key], val)
            else:
                result[key] = val
        return result


# Module-level singleton — import this everywhere.
settings = SettingsManager()

"""
services.py
-----------
The :class:`ServiceHub` bundles the shared services every widget needs and is
handed to each widget as ``ctx`` at construction.

Passing one bundle (instead of letting widgets reach back into ``UIManager``)
is what lets a widget be constructed, tested, and torn down in isolation — and
what lets two instances of the same widget coexist. Widgets read
``ctx.bus`` / ``ctx.settings`` / ``ctx.clock`` / ``ctx.serial`` and never import
the top-level orchestrator.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ui.core.bus import TelemetryBus
from ui.core.mission_clock import MissionClock

if TYPE_CHECKING:  # avoid import cycles at runtime
    from ui.core.serial_service import SerialService
    from ui.settings_manager import SettingsManager


@dataclass
class ServiceHub:
    """Shared services injected into every widget as ``ctx``."""

    bus: TelemetryBus
    settings: "SettingsManager"
    clock: MissionClock
    serial: Optional["SerialService"] = None
    # A smaller DPG font id, created at startup. Widgets that set ``"compact":
    # true`` in their config bind this to their root so dense content (tables,
    # stat strips, control rows) fits without overflowing the cell.
    font_small: Optional[int] = None

"""
mission_clock.py
----------------
Single source of mission-elapsed time.

The plot widgets share one clock so every time axis restarts together on arm /
reset. Previously ``UIManager`` owned ``_mission_start`` and computed elapsed
time inline for each plot update; that logic now lives here and is injected into
widgets via the :class:`~ui.core.services.ServiceHub`.

A ``time_fn`` seam (defaulting to :func:`time.time`) keeps the clock unit-testable
without real wall-clock sleeps.
"""

import logging
import time
from typing import Callable

log = logging.getLogger(__name__)


class MissionClock:
    """Monotonic-ish mission clock: seconds since the last :py:meth:`reset`."""

    def __init__(self, time_fn: Callable[[], float] = time.time) -> None:
        self._time = time_fn
        self._start = self._time()

    def reset(self) -> None:
        """Restart the clock at t=0 (called on arm / Reset Plot)."""
        self._start = self._time()
        log.info("MissionClock: reset")

    def elapsed(self) -> float:
        """Seconds since the last reset (or construction)."""
        return self._time() - self._start

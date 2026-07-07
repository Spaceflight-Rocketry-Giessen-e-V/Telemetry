"""
bus.py
------
Thread-safe publish/subscribe telemetry bus with a main-thread delivery seam.

Why this exists
===============
Telemetry arrives on the serial receiver's daemon thread, but DearPyGui item
calls (``dpg.set_value`` etc.) are only safe on the thread that runs the render
loop. The bus decouples the two:

  - :py:meth:`publish` is thread-safe and only *enqueues* — it never invokes a
    subscriber. Any thread may call it.
  - :py:meth:`pump` drains the queue and invokes subscriber callbacks. It must
    be called once per rendered frame on the UI thread (see :mod:`ui.core.pump`).

Because callbacks only ever run inside ``pump()``, every widget can safely call
``dpg.*`` from its subscription handlers. This replaces the old
``UIManager.update_all`` dispatch table: producers publish named topics and
widgets subscribe to the ones they care about, with no central wiring.

Topics are plain strings. The canonical set is documented in
``docs/modular-dashboard-plan.md`` (``tele/<field>``, ``gps/fix``,
``flight/armed``, ``mission/reset``, ``plot/stop|resume|reset``,
``settings/<section>/changed``, ``packet/raw``).
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

log = logging.getLogger(__name__)

Callback = Callable[[Any], None]


@dataclass
class Sample:
    """
    A single telemetry value with both wall-clock and mission-elapsed time.

    Publishers stamp ``mission_t`` from the shared :class:`~ui.core.mission_clock.MissionClock`
    so plot widgets get a consistent time axis without each keeping its own
    clock (the old UIManager computed elapsed time inline for every plot).
    """

    value: Any
    wall_t: float
    mission_t: float


class TelemetryBus:
    """
    Topic → subscribers map with thread-safe publishing and framed delivery.

    Delivery model
    --------------
    ``publish`` enqueues ``(topic, payload)`` and returns immediately. ``pump``
    (called on the UI thread) drains a *snapshot* of the queue and dispatches
    each item to that topic's subscribers. Items published *by* a callback are
    delivered on the next ``pump`` — this bounds each pump to finite work and
    avoids re-entrancy surprises.

    A single lock guards the subscriber tables; the queue is already
    thread-safe. Subscriber exceptions are logged and swallowed so one bad
    handler cannot stall the pump or drop sibling subscribers.
    """

    def __init__(self) -> None:
        self._subs: dict[str, dict[int, Callback]] = {}
        self._tok_topic: dict[int, str] = {}
        self._next_token = 0
        self._lock = threading.Lock()
        self._q: "queue.Queue[tuple[str, Any]]" = queue.Queue()

    # -- subscription ---------------------------------------------------------

    def subscribe(self, topic: str, callback: Callback) -> int:
        """
        Register *callback* for *topic* and return an opaque unsubscribe token.

        The callback receives the published payload (usually a :class:`Sample`,
        but any object — a raw packet dict, a bool — depending on the topic).
        """
        with self._lock:
            self._next_token += 1
            token = self._next_token
            self._subs.setdefault(topic, {})[token] = callback
            self._tok_topic[token] = topic
        log.debug("bus: subscribe token=%d topic=%r", token, topic)
        return token

    def unsubscribe(self, token: int) -> None:
        """Remove a subscription by its token. Safe to call with a stale token."""
        with self._lock:
            topic = self._tok_topic.pop(token, None)
            if topic is None:
                return
            subs = self._subs.get(topic)
            if subs is not None:
                subs.pop(token, None)
                if not subs:
                    del self._subs[topic]
        log.debug("bus: unsubscribe token=%d topic=%r", token, topic)

    # -- publish / deliver ----------------------------------------------------

    def publish(self, topic: str, payload: Any = None) -> None:
        """
        Enqueue a payload for *topic*. Thread-safe; never runs a callback.

        Delivery happens on the next :py:meth:`pump`.
        """
        self._q.put((topic, payload))

    def pump(self) -> int:
        """
        Deliver all currently-queued items to their subscribers.

        Call once per rendered frame on the UI thread. Returns the number of
        items delivered (handy for tests and diagnostics). Items enqueued by a
        callback during this pump are left for the next pump.
        """
        pending = self._q.qsize()
        delivered = 0
        for _ in range(pending):
            try:
                topic, payload = self._q.get_nowait()
            except queue.Empty:
                break
            delivered += 1
            self._dispatch(topic, payload)
        return delivered

    def _dispatch(self, topic: str, payload: Any) -> None:
        # Snapshot subscribers under the lock so a handler may (un)subscribe
        # mid-dispatch without mutating the list we are iterating.
        with self._lock:
            handlers = list(self._subs.get(topic, {}).values())
        for cb in handlers:
            try:
                cb(payload)
            except Exception:  # noqa: BLE001 — one handler must not kill the pump
                log.error("bus: subscriber for topic %r raised", topic, exc_info=True)

    # -- diagnostics ----------------------------------------------------------

    def subscriber_count(self, topic: str) -> int:
        """Number of live subscribers for *topic* (test/diagnostic helper)."""
        with self._lock:
            return len(self._subs.get(topic, {}))

    def sample(self, value: Any, mission_t: float) -> Sample:
        """Convenience factory stamping ``wall_t`` with the current time."""
        return Sample(value=value, wall_t=time.time(), mission_t=mission_t)

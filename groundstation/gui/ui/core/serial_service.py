"""
serial_service.py
-----------------
Owns the serial :class:`TelemetryReceiver` and turns decoded packets into bus
events. This is the single producer of telemetry topics.

Threading contract
==================
:py:meth:`_on_packet` runs on the receiver's ``telemetry-rx`` daemon thread. It
does **not** touch DearPyGui — it only calls ``bus.publish`` (a thread-safe
enqueue). Every subscriber (and therefore every ``dpg.*`` call) runs later, on
the UI thread, when the pump drains the queue. That is what makes the old
"serial thread calls ``dpg.set_value`` directly" bug impossible.

Derived topics (``gps/fix``, ``flight/armed``, ``plot/reset`` on arm) are
computed here so the guards live in one place instead of being duplicated across
widgets, and every ``tele/*`` sample is stamped with mission-elapsed time from
the shared clock.
"""

import logging
import time
from typing import Optional

import serial.tools.list_ports

from ui.core import topics
from ui.core.bus import Sample, TelemetryBus
from ui.core.mission_clock import MissionClock

log = logging.getLogger(__name__)

# Fields carried in a complete packet that are NOT telemetry values to fan out.
_NON_TELE_FIELDS = frozenset({"timestamp"})


class SerialService:
    """Bridges :class:`TelemetryReceiver` to the telemetry bus."""

    def __init__(self, bus: TelemetryBus, clock: MissionClock) -> None:
        self.bus = bus
        self.clock = clock
        self._rx = None  # TelemetryReceiver when running
        self._armed = False  # last-seen flight-mode state, for edge detection
        # A user-initiated plot reset should also rebase the mission clock so the
        # time axis restarts at 0 (the old PlotCoordinator reset hook).
        self.bus.subscribe(topics.PLOT_RESET, lambda _=None: self.clock.reset())

    # -- port discovery -------------------------------------------------------

    @staticmethod
    def list_ports() -> list[str]:
        """Enumerate available serial port device names."""
        return [p.device for p in serial.tools.list_ports.comports()]

    # -- lifecycle ------------------------------------------------------------

    def is_running(self) -> bool:
        return self._rx is not None and self._rx.is_running()

    def is_connected(self) -> bool:
        return self._rx is not None and self._rx.is_connected()

    def start(self, port: str, baudrate: int) -> None:
        """
        Open *port* at *baudrate* and begin publishing packets.

        Raises whatever :class:`serial.Serial` raises on a bad port so the caller
        (the COM panel) can surface it; a stale stopped receiver is torn down
        first so we never leak a port.
        """
        if self.is_running():
            log.warning("SerialService: start ignored — already running")
            return
        if self._rx is not None:
            self._rx.stop()
            self._rx = None

        from telemetry.com_controller import TelemetryReceiver  # deferred (heavy import)

        self._armed = False
        self._rx = TelemetryReceiver(com_port=port, baudrate=baudrate)
        self._rx.set_ui_callback(self._on_packet)
        self._rx.start()
        self.bus.publish(topics.SERIAL_STATUS,
                         {"connected": True, "port": port, "message": f"Connected to {port}"})
        log.info("SerialService: started on %s @ %d", port, baudrate)

    def stop(self) -> None:
        """Stop the receiver if running and announce the disconnect."""
        if self._rx is not None:
            self._rx.stop()
            self._rx = None
        self.bus.publish(topics.SERIAL_STATUS,
                         {"connected": False, "port": "", "message": "Disconnected"})
        log.info("SerialService: stopped")

    # -- command sending ------------------------------------------------------

    def send_command(self, command: str) -> None:
        """Send a command (friendly name / registry key / bare char) to the device."""
        if self._rx is None:
            raise RuntimeError("Serial port is not open")
        self._rx.send_command(command)

    # -- packet → bus (runs on the serial thread) -----------------------------

    def _on_packet(self, packet: dict) -> None:
        """Publish one decoded packet as bus events. Serial thread; enqueue only."""
        fm = packet.get("flight_mode")
        armed = bool(fm) if fm is not None else self._armed
        arm_edge = armed and not self._armed
        disarm_edge = (not armed) and self._armed

        # On arm, restart the mission clock and clear the plots so a fresh flight
        # begins at t=0 (matches the old arm-transition behaviour).
        if arm_edge:
            self.clock.reset()
            self.bus.publish(topics.PLOT_RESET, None)

        mission_t = self.clock.elapsed()
        wall_t = time.time()

        for field, value in packet.items():
            if field in _NON_TELE_FIELDS:
                continue
            self.bus.publish(topics.tele(field), Sample(value=value, wall_t=wall_t, mission_t=mission_t))

        self.bus.publish(topics.PACKET_RAW, dict(packet))

        lat, lon = packet.get("lat_gnss"), packet.get("lon_gnss")
        if lat is not None and lon is not None:
            self.bus.publish(topics.GPS_FIX, (lat, lon))

        if arm_edge or disarm_edge:
            self.bus.publish(topics.FLIGHT_ARMED, armed)
        self._armed = armed

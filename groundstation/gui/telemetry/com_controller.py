"""
com_controller.py
-----------------
Serial telemetry back-end for the Ground Station GUI.

The :class:`TelemetryReceiver` class combines three responsibilities:

- **Receiver** — reads raw lines from the serial port in a background thread,
  parses field/value pairs out of them, and assembles complete packets.
- **Logger** — optionally appends each complete packet to a CSV file and/or a
  plain-text log file.  Log paths are timestamped at startup so each session
  gets its own files under ``logs/``.
- **Commander** — writes single-character command bytes back to the device,
  accepting friendly names, raw key names, or bare characters.

Typical usage
~~~~~~~~~~~~~
    from telemetry.com_controller import TelemetryReceiver

    rx = TelemetryReceiver(com_port="COM3", baudrate=115200)
    rx.set_ui_callback(my_ui_update_fn)
    rx.start()
    ...
    rx.stop()
"""

import csv
import logging
import os
import re
import serial
import threading
import time
from datetime import datetime

log = logging.getLogger(__name__)


class TelemetryReceiver:
    """
    Serial telemetry receiver, packet logger, and command sender.

    Parameters
    ----------
    com_port:
        Serial port identifier, e.g. ``"COM3"`` or ``"/dev/ttyUSB0"``.
    baudrate:
        Baud rate for the serial link (default 115 200).
    log_dir:
        Directory under which per-session log files are written.
        Created automatically if it does not exist.
    log_to_csv:
        Write each complete packet as a row in a CSV file.
    log_to_txt:
        Append every raw serial line (with ISO timestamp) to a text file.
    log_to_console:
        Print each complete packet dict to stdout (useful for debugging).
    ui_callback:
        Optional callable invoked with a copy of each complete packet dict.
        Can also be set later with :py:meth:`set_ui_callback`.
    """

    # ── Command registry ─────────────────────────────────────────────────────
    # Maps human-readable command names to the single ASCII character sent
    # over the serial link.
    COMMANDS: dict[str, str] = {
        "ping": "p",
        "main_chute_50": "a",
        "main_chute_100": "b",
        "main_chute_150": "c",
        "main_chute_200": "d",
        "low_power_on": "l",
        "low_power_off": "m",
        "flight_mode_on": "f",
        "flight_mode_off": "g",
        "eject_drogue": "q",
        "eject_main": "r",
    }

    # ── Packet field order ────────────────────────────────────────────────────
    # Defines the column order in the CSV log and the fields that must all be
    # present before a packet is considered complete and dispatched.
    FIELDS: list[str] = [
        "timestamp",
        "temperature",
        "subsystem_status",
        "flight_mode",
        "low_power_mode",
        "status_events",
        "acceleration",
        "height_pressure",
        "height_gnss",
        "lat_gnss",
        "lon_gnss",
        "battery_voltage",
        "rssi",
        "time_since_last_packet",
    ]

    # ── Line-parsing regex patterns ───────────────────────────────────────────
    # Each pattern captures exactly one value group from a raw serial line.
    # Integer fields have no decimal point; float fields do.
    PATTERNS: dict[str, str] = {
        "temperature": r"temperature > 80 C: (-?\d+)",
        "subsystem_status": r"subsystem_status: (\d+)",
        "flight_mode": r"flight_mode: (\d+)",
        "low_power_mode": r"low_power_mode: (\d+)",
        "status_events": r"status_events: (\d+)",
        "acceleration": r"acceleration: (-?\d+\.\d+)",
        "height_pressure": r"height_pressure: (-?\d+\.\d+)",
        "height_gnss": r"height_gnss: (-?\d+\.\d+)",
        "lat_gnss": r"lat_gnss: (-?\d+\.\d+)",
        "lon_gnss": r"lon_gnss: (-?\d+\.\d+)",
        "battery_voltage": r"battery_voltage: (\d+\.\d+)",
        "rssi": r"rssi: (-?\d+(?:\.\d+)?)",
        "time_since_last_packet": r"time_since_last_packet: (\d+)",
    }

    # Fields required for a packet to be considered complete (all except timestamp,
    # which is added by the receiver itself).
    _REQUIRED_FIELDS: frozenset[str] = frozenset(FIELDS[1:])

    # First data field of every transmit cycle. Used as a framing boundary: if it
    # arrives while a partial packet is still open, the previous cycle dropped a
    # line, so we discard the partial instead of blending two cycles together.
    _BOUNDARY_FIELD: str = FIELDS[1]  # "temperature"

    # Discard a partial packet left open longer than this (seconds) so a stalled
    # cycle can never merge with a later one.
    _STALE_TIMEOUT: float = 2.0

    # How long (seconds) the listen loop sleeps when the serial buffer is empty
    _POLL_INTERVAL: float = 0.01

    def __init__(
            self,
            com_port: str,
            baudrate: int = 115200,
            log_dir: str = "logs",
            log_to_csv: bool = True,
            log_to_txt: bool = True,
            log_to_console: bool = False,
            ui_callback=None,
    ):
        self.com_port = com_port
        self.baudrate = baudrate
        self.log_to_csv = log_to_csv
        self.log_to_txt = log_to_txt
        self.log_to_console = log_to_console
        self.ui_callback = ui_callback

        # Serial port handle and background thread — set on start()
        self.ser: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._running: bool = False

        # Accumulates field/value pairs until a full packet is ready
        self._packet_data: dict[str, object] = {}
        # Wall-clock time the current partial packet was opened (for staleness).
        self._packet_started_at: float = 0.0

        # ── Per-session log file paths ────────────────────────────────────────
        # Timestamped filenames prevent sessions from overwriting each other.
        os.makedirs(log_dir, exist_ok=True)
        session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = os.path.join(log_dir, f"telemetry_{session_ts}.csv")
        self.txt_file = os.path.join(log_dir, f"telemetry_{session_ts}.txt")

        # Write the CSV header immediately so the file is valid even if no
        # packets are received during this session.
        if self.log_to_csv:
            self._init_csv()

        log.info(
            "TelemetryReceiver: initialised — port=%s, baud=%d, csv=%s, txt=%s",
            com_port, baudrate,
            self.csv_file if log_to_csv else "disabled",
            self.txt_file if log_to_txt else "disabled",
        )

    # =========================================================================
    # State API
    # =========================================================================

    def is_running(self) -> bool:
        """Return ``True`` if the background listen thread is active."""
        return self._running

    def is_connected(self) -> bool:
        """Return ``True`` if the serial port is open."""
        return self.ser is not None and self.ser.is_open

    def set_ui_callback(self, callback) -> None:
        """
        Attach (or replace) the packet callback.

        The callable is invoked on the serial thread with a **copy** of the
        completed packet dict, so it must not block for long.
        """
        self.ui_callback = callback
        log.debug("TelemetryReceiver: UI callback set to %r", callback)

    # =========================================================================
    # Telemetry parsing
    # =========================================================================

    def parse_line(self, line: str) -> tuple[str | None, int | float | None]:
        """
        Try to extract a single field/value pair from a raw serial line.

        Returns
        -------
        (key, value)
            *key* is a string from :attr:`PATTERNS`; *value* is an ``int``
            for integer fields or a ``float`` for fields containing a decimal
            point.  Returns ``(None, None)`` if the line matches no pattern.
        """
        for key, pattern in self.PATTERNS.items():
            match = re.search(pattern, line)
            if match:
                raw = match.group(1)
                value = float(raw) if "." in raw else int(raw)
                log.debug("TelemetryReceiver: parsed '%s' = %s", key, value)
                return key, value

        log.debug("TelemetryReceiver: unrecognised line: %r", line)
        return None, None

    # =========================================================================
    # Logging helpers
    # =========================================================================

    def _init_csv(self) -> None:
        """Create the CSV log file and write the header row."""
        try:
            with open(self.csv_file, "w", newline="", encoding="utf-8") as fh:
                csv.DictWriter(fh, fieldnames=self.FIELDS).writeheader()
            log.info("TelemetryReceiver: CSV log initialised at '%s'", self.csv_file)
        except OSError as exc:
            log.error("TelemetryReceiver: failed to create CSV log: %s", exc)
            self.log_to_csv = False  # disable to avoid repeated errors

    def _log_txt(self, line: str) -> None:
        """Append one raw serial line (with ISO timestamp) to the text log."""
        try:
            with open(self.txt_file, "a", encoding="utf-8") as fh:
                fh.write(f"{datetime.now().isoformat()}  {line}\n")
        except OSError as exc:
            log.error("TelemetryReceiver: text log write failed: %s", exc)

    def _log_csv(self, packet: dict) -> None:
        """Append a complete packet dict as one CSV row."""
        try:
            with open(self.csv_file, "a", newline="", encoding="utf-8") as fh:
                csv.DictWriter(fh, fieldnames=self.FIELDS).writerow(packet)
        except OSError as exc:
            log.error("TelemetryReceiver: CSV log write failed: %s", exc)

    # =========================================================================
    # Packet assembly
    # =========================================================================

    def _process_line(self, line: str) -> None:
        """
        Handle one decoded serial line.

        1. Optionally append it to the text log.
        2. Try to parse a field/value pair and store it in the accumulator.
        3. When all required fields are present, finalise and dispatch the packet.
        """
        # ── Text log ──────────────────────────────────────────────────────────
        if self.log_to_txt:
            self._log_txt(line)

        # ── Parse ─────────────────────────────────────────────────────────────
        key, value = self.parse_line(line)
        if key:
            # ── Framing ───────────────────────────────────────────────────────
            # The wire format has no delimiter, so frame on the fixed field order:
            # the boundary field opens a new cycle, and a partial packet still
            # open at that point (or gone stale) lost a line and must be dropped
            # rather than merged with the incoming cycle.
            if self._packet_data:
                stale = (time.time() - self._packet_started_at) > self._STALE_TIMEOUT
                if key == self._BOUNDARY_FIELD or stale:
                    log.warning(
                        "TelemetryReceiver: discarding incomplete packet "
                        "(%d/%d fields, reason=%s): %s",
                        len(self._packet_data), len(self._REQUIRED_FIELDS),
                        "new-cycle" if key == self._BOUNDARY_FIELD else "stale",
                        sorted(self._packet_data),
                    )
                    self._packet_data.clear()

            if not self._packet_data:
                self._packet_started_at = time.time()
            self._packet_data[key] = value

        # ── Check for packet completeness ─────────────────────────────────────
        if not self._REQUIRED_FIELDS.issubset(self._packet_data):
            return  # packet not yet complete; wait for more lines

        # ── Finalise packet ───────────────────────────────────────────────────
        self._packet_data["timestamp"] = datetime.now().isoformat()
        packet = self._packet_data.copy()
        self._packet_data.clear()

        log.info("TelemetryReceiver: packet complete — %d fields", len(packet))
        log.debug("TelemetryReceiver: packet contents: %s", packet)

        # ── Dispatch ──────────────────────────────────────────────────────────
        if self.log_to_console:
            print(packet)

        if self.log_to_csv:
            self._log_csv(packet)

        if self.ui_callback:
            try:
                self.ui_callback(packet)
            except Exception as exc:  # noqa: BLE001
                log.error("TelemetryReceiver: UI callback raised an exception: %s", exc, exc_info=True)

    # =========================================================================
    # Serial listen thread
    # =========================================================================

    def _listen(self) -> None:
        """
        Background thread body.

        Reads lines from the serial port and hands them to
        :py:meth:`_process_line`.  Stops automatically on a
        :class:`serial.SerialException` (e.g. device unplugged).
        """
        log.info("TelemetryReceiver: listen thread started on %s", self.com_port)

        while self._running:
            try:
                if self.ser.in_waiting:
                    raw = self.ser.readline()
                    # readline() returns whatever it has (no trailing newline) when
                    # the 1 s timeout fires mid-line. Parsing that truncated text
                    # would misread a value, so drop it and wait for a full line.
                    if not raw.endswith(b"\n"):
                        if raw:
                            log.warning("TelemetryReceiver: dropping partial line (no newline): %r", raw)
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line:
                        self._process_line(line)
                else:
                    # Nothing in the buffer — yield the CPU briefly
                    time.sleep(self._POLL_INTERVAL)

            except serial.SerialException as exc:
                # Device disconnected or OS-level serial error — stop the thread
                log.error("TelemetryReceiver: serial error — %s", exc)
                self._running = False

            except Exception as exc:  # noqa: BLE001
                # Unexpected error — log but keep running so a bad line doesn't
                # crash the entire session.
                log.warning("TelemetryReceiver: unexpected error in listen loop: %s", exc, exc_info=True)

        log.info("TelemetryReceiver: listen thread exited")

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def start(self) -> None:
        """
        Open the serial port and start the background listen thread.

        Safe to call only once; subsequent calls are ignored if already running.
        """
        if self._running:
            log.warning("TelemetryReceiver: start() called but already running — ignoring")
            return

        log.info("TelemetryReceiver: opening %s @ %d baud", self.com_port, self.baudrate)
        self.ser = serial.Serial(self.com_port, self.baudrate, timeout=1)

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True, name="telemetry-rx")
        self._thread.start()
        log.info("TelemetryReceiver: started (thread id=%d)", self._thread.ident)

    def stop(self) -> None:
        """
        Signal the listen thread to stop and close the serial port.

        Blocks for up to 2 seconds waiting for the thread to exit cleanly.
        """
        log.info("TelemetryReceiver: stop() called")
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                # The thread may still be inside in_waiting/readline on self.ser.
                # Closing the port now would race it, so leave the port open (the
                # thread is a daemon and won't block process exit) and bail out.
                log.error(
                    "TelemetryReceiver: listen thread did not exit within timeout; "
                    "leaving serial port open to avoid a race with the live thread"
                )
                return

        if self.ser and self.ser.is_open:
            self.ser.close()
            log.info("TelemetryReceiver: serial port closed")

        self.ser = None
        self._thread = None

    # =========================================================================
    # Command sending
    # =========================================================================

    def send_raw_command(self, cmd: str) -> None:
        """
        Write a single ASCII character directly to the serial port.

        Parameters
        ----------
        cmd:
            Exactly one ASCII letter (case-insensitive; sent as lowercase).

        Raises
        ------
        RuntimeError:
            If the serial port is not open.
        ValueError:
            If *cmd* is not a single alphabetic character.
        """
        if not self.is_connected():
            raise RuntimeError("Serial port is not open")

        if not cmd or len(cmd) != 1 or not (cmd.isascii() and cmd.isalpha()):
            raise ValueError(f"Command must be a single ASCII letter, got: {cmd!r}")

        encoded = cmd.lower().encode("ascii")
        self.ser.write(encoded)
        self.ser.flush()
        log.info("TelemetryReceiver: raw command sent: %r", cmd.lower())

    def send_command(self, command: str) -> None:
        """
        Send a command by friendly name, registry key, or raw character.

        Accepts any of:
          - A single character:  ``"p"``
          - A registry key:      ``"flight_mode_on"``
          - A friendly name:     ``"PING"``  (case-insensitive, mapped via COMMANDS)

        Raises
        ------
        RuntimeError:
            If the serial port is not open.
        ValueError:
            If *command* cannot be resolved to a known command character.
        """
        if not self.is_connected():
            raise RuntimeError("Serial port is not open")

        normalised = command.strip().lower()
        log.debug("TelemetryReceiver: send_command called with %r (normalised: %r)", command, normalised)

        # 1. Check registry (e.g. "flight_mode_on" → "f")
        if normalised in self.COMMANDS:
            cmd_char = self.COMMANDS[normalised]
            log.info("TelemetryReceiver: command '%s' resolved via registry → '%s'", normalised, cmd_char)

        # 2. Accept bare single-character commands (e.g. "p", "f")
        elif len(normalised) == 1 and normalised.isalpha():
            cmd_char = normalised
            log.info("TelemetryReceiver: bare character command: '%s'", cmd_char)

        else:
            raise ValueError(
                f"Unknown command: {command!r}. "
                f"Valid keys: {sorted(self.COMMANDS.keys())}"
            )

        self.send_raw_command(cmd_char)

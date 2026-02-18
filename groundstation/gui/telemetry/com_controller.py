import serial
import re
import csv
from datetime import datetime
import threading
import time
import os


class TelemetryReceiver:
    """
    Acts as:
      - telemetry receiver
      - command sender
      - serial connection controller
    """

    COMMANDS = {
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

    FIELDS = [
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

    PATTERNS = {
        "temperature": r"temperature > 80 C: (\d+)",
        "subsystem_status": r"subsystem_status: (\d+)",
        "flight_mode": r"flight_mode: (\d+)",
        "low_power_mode": r"low_power_mode: (\d+)",
        "status_events": r"status_events: (\d+)",
        "acceleration": r"acceleration: (-?\d+\.\d+)",
        "height_pressure": r"height_pressure: (\d+\.\d+)",
        "height_gnss": r"height_gnss: (\d+\.\d+)",
        "lat_gnss": r"lat_gnss: (-?\d+\.\d+)",
        "lon_gnss": r"lon_gnss: (-?\d+\.\d+)",
        "battery_voltage": r"battery_voltage: (\d+\.\d+)",
        "rssi": r"rssi: (-?\d+)",
        "time_since_last_packet": r"time_since_last_packet: (\d+)",
    }

    def __init__(
        self,
        com_port,
        baudrate=115200,
        csv_file="telemetry_log.csv",
        txt_file="telemetry_log.txt",
        log_to_txt=True,
        log_to_csv=True,
        log_to_console=False,
        ui_callback=None,
    ):
        self.com_port = com_port
        self.baudrate = baudrate

        self.csv_file = csv_file
        self.txt_file = txt_file
        self.log_to_csv = log_to_csv
        self.log_to_txt = log_to_txt
        self.log_to_console = log_to_console

        self.ui_callback = ui_callback

        self.ser = None
        self._thread = None
        self._running = False
        self.packet_data = {}

        # Ensure CSV header
        if self.log_to_csv and not os.path.exists(self.csv_file):
            with open(self.csv_file, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=self.FIELDS).writeheader()

    # ------------------------------------------------------------------
    # Controller / state API (for UIs)
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        return self._running

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def set_ui_callback(self, callback):
        """Allow UIs to attach / replace the telemetry callback."""
        self.ui_callback = callback

    # ------------------------------------------------------------------
    # Telemetry parsing
    # ------------------------------------------------------------------

    def parse_line(self, line):
        for key, pattern in self.PATTERNS.items():
            match = re.search(pattern, line)
            if match:
                value = match.group(1)
                return key, float(value) if "." in value else int(value)
        return None, None

    def _log_txt(self, line):
        with open(self.txt_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} {line}\n")

    def _process_line(self, line):
        if self.log_to_txt:
            self._log_txt(line)

        key, value = self.parse_line(line)
        if key:
            self.packet_data[key] = value

        if all(field in self.packet_data for field in self.FIELDS[1:]):
            self.packet_data["timestamp"] = datetime.now().isoformat()

            if self.log_to_console:
                print(self.packet_data)

            if self.log_to_csv:
                with open(self.csv_file, "a", newline="") as f:
                    csv.DictWriter(f, fieldnames=self.FIELDS).writerow(self.packet_data)

            if self.ui_callback:
                self.ui_callback(self.packet_data.copy())

            self.packet_data.clear()

    # ------------------------------------------------------------------
    # Serial thread
    # ------------------------------------------------------------------

    def _listen(self):
        while self._running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode("utf-8", errors="strict").strip()
                    if line:
                        self._process_line(line)
                else:
                    time.sleep(0.01)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                self._running = False
            except Exception as e:
                print(f"Error: {e}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return

        self.ser = serial.Serial(self.com_port, self.baudrate, timeout=1)
        self._running = True

        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

        if self._thread:
            self._thread.join(timeout=1)

        if self.ser and self.ser.is_open:
            self.ser.close()

    # ------------------------------------------------------------------
    # Command sending (controller-facing)
    # ------------------------------------------------------------------

    def send_raw_command(self, cmd: str):
        if not self.is_connected():
            raise RuntimeError("Serial port not open")

        if not cmd or len(cmd) != 1:
            raise ValueError("Command must be a single character")

        self.ser.write(cmd.lower().encode("ascii"))
        self.ser.flush()

    def send_command(self, command: str):
        """
        Accepts:
          - "p"
          - "PING"
          - "flight_mode_on"
        """
        if not self.is_connected():
            raise RuntimeError("Serial port not open")

        command = command.strip().lower()

        if command in self.COMMANDS:
            cmd_char = self.COMMANDS[command]
        elif len(command) == 1 and command.isalpha():
            cmd_char = command
        else:
            raise ValueError(f"Invalid command: {command}")

        self.send_raw_command(cmd_char)

"""
com_monitor_controller.py
-------------------------
Serial port control panel and telemetry thread manager.

Lets the operator select a COM port and baud rate, then start or stop the
:class:`TelemetryReceiver` background thread. On each received packet, the
:py:meth:`update_ui` callback forwards the parsed data to
:class:`UIManager.update_all`.
"""

import logging

import dearpygui.dearpygui as dpg
import serial.tools.list_ports

log = logging.getLogger(__name__)


class ComMonitorController:
    """Renders the serial-port control panel and manages the telemetry thread."""

    _TAG_STATUS = "monitor_status_label"

    # Common serial baud rates offered in the dropdown.
    _BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]

    def __init__(self, ui_manager=None):
        """
        Parameters
        ----------
        ui_manager:
            The top-level :class:`UIManager` instance. Its
            :py:meth:`update_all` method is called on every received packet.
        """
        self.ui_manager = ui_manager
        self.com_port_selector = None  # DPG item id for the COM-port combo
        self.baudrate_input = None  # DPG item id for the baud-rate input
        self.controller = None  # TelemetryReceiver instance when running

        log.debug("%s: initialised", self.__class__.__name__)

    def draw_ui(self, window_width: int = 300, window_height: int = 200) -> None:
        """
        Render the COM-port selector, baud-rate input, and Start/Stop buttons.

        Available serial ports are enumerated at draw time; the user can
        also type a port name manually into the combo widget.
        """
        log.debug("ComMonitorController: drawing UI (%dx%d)", window_width, window_height)

        com_ports = [port.device for port in serial.tools.list_ports.comports()]
        log.info("ComMonitorController: detected ports: %s", com_ports)

        with dpg.child_window(label="COM Monitor", width=window_width, height=window_height):
            dpg.add_text("COM Port Settings", color=(255, 255, 0))
            dpg.add_separator()

            self.com_port_selector = dpg.add_combo(
                items=com_ports,
                label="Port",
                width=120,
                default_value=com_ports[0] if com_ports else "",
            )

            # Default baud rate is 115 200, the most common rate for telemetry links.
            # A dropdown of common rates is friendlier than +/- stepping.
            self.baudrate_input = dpg.add_combo(
                items=self._BAUD_RATES,
                label="Baud",
                width=120,
                default_value="115200",
            )

            dpg.add_spacer(height=4)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", width=80, callback=self.start_monitor)
                dpg.add_button(label="Stop", width=80, callback=self.stop_monitor)

            dpg.add_spacer(height=6)
            dpg.add_separator()
            dpg.add_text("Monitor stopped.", tag=self._TAG_STATUS)

    def start_monitor(self) -> None:
        """
        Start the :class:`TelemetryReceiver` on the selected port and baud rate.

        Does nothing if a receiver is already running.
        """
        if self.controller and self.controller.is_running():
            log.warning("ComMonitorController: start_monitor called but monitor is already running")
            dpg.configure_item(self._TAG_STATUS, default_value="Monitor already running!")
            return

        # A previous receiver may exist but be stopped (e.g. a serial error left
        # its port open without a stop()). Tear it down before opening a new one
        # so we don't leak the old port/thread.
        if self.controller:
            self.controller.stop()
            self.controller = None

        com_port = dpg.get_value(self.com_port_selector)
        baud_str = dpg.get_value(self.baudrate_input)
        baudrate = int(baud_str) if baud_str else 115200

        if not com_port:
            log.warning("ComMonitorController: start_monitor called with no COM port selected")
            dpg.configure_item(self._TAG_STATUS, default_value="Select a COM port first!")
            return

        log.info("ComMonitorController: starting receiver on %s @ %d baud", com_port, baudrate)

        # Deferred import to avoid circular dependencies and allow this module
        # to load even when the telemetry back-end is not installed.
        from telemetry.com_controller import TelemetryReceiver  # noqa: PLC0415

        self.controller = TelemetryReceiver(com_port=com_port, baudrate=baudrate)
        self.controller.set_ui_callback(self.update_ui)
        self.controller.start()

        dpg.configure_item(self._TAG_STATUS, default_value=f"Monitor started on {com_port}.")
        log.info("ComMonitorController: receiver started successfully")

    def stop_monitor(self) -> None:
        """Stop the running :class:`TelemetryReceiver` if one is active."""
        if self.controller:
            log.info("ComMonitorController: stopping receiver")
            self.controller.stop()
        else:
            log.debug("ComMonitorController: stop_monitor called but no receiver is running")

        dpg.configure_item(self._TAG_STATUS, default_value="Monitor stopped.")

    def update_ui(self, packet: dict) -> None:
        """
        Called by :class:`TelemetryReceiver` for every decoded packet.

        Forwards the packet to UIManager so all sub-windows are updated
        in a single pass.
        """
        log.debug("ComMonitorController: packet received with keys: %s", list(packet.keys()))

        if self.ui_manager:
            self.ui_manager.update_all(packet)
        else:
            log.warning("ComMonitorController: no ui_manager set; packet dropped")

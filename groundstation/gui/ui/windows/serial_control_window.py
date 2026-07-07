"""
serial_control_window.py
------------------------
Serial-link control panel: pick a COM port and baud rate, Start/Stop the
receiver, and see the connection status.

Replaces the old ComMonitorController's UI half. It no longer owns the receiver
thread — the :class:`~ui.core.serial_service.SerialService` does — it just drives
it via ``ctx.serial`` and reflects ``serial/status`` bus events. Marked SINGLETON
so the registry refuses a second instance (two panels would fight over one port).
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class SerialControlWindow(Widget):
    """COM-port control panel bound to the SerialService."""

    TYPE_ID = "serial_control"
    DISPLAY_NAME = "COM Port"
    DEFAULT_CELLS = (3, 2)
    MIN_CELLS = (3, 2)
    SINGLETON = True

    _BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "COM Port Settings"), color=(255, 255, 0))
        dpg.add_separator()

        ports = self.ctx.serial.list_ports() if self.ctx.serial else []
        dpg.add_combo(items=ports, label="Port", width=120, tag=self.tag("port"),
                      default_value=ports[0] if ports else "")
        dpg.add_combo(items=self._BAUD_RATES, label="Baud", width=120, tag=self.tag("baud"),
                      default_value="115200")

        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Start", width=80, callback=self._start)
            dpg.add_button(label="Stop", width=80, callback=self._stop)
            dpg.add_button(label="↻", width=30, callback=self._refresh_ports)

        dpg.add_spacer(height=6)
        dpg.add_separator()
        dpg.add_text("Monitor stopped.", tag=self.tag("status"))

        self.subscribe(topics.SERIAL_STATUS, self._on_status)

    def _refresh_ports(self) -> None:
        if self.ctx.serial:
            dpg.configure_item(self.tag("port"), items=self.ctx.serial.list_ports())

    def _start(self) -> None:
        serial = self.ctx.serial
        if serial is None:
            return
        port = dpg.get_value(self.tag("port"))
        if not port:
            dpg.set_value(self.tag("status"), "Select a COM port first!")
            return
        baud_str = dpg.get_value(self.tag("baud"))
        baudrate = int(baud_str) if baud_str else 115200
        try:
            serial.start(port, baudrate)
        except Exception as exc:  # noqa: BLE001 — surface a bad port to the operator
            dpg.set_value(self.tag("status"), f"Error: {exc}")
            log.error("SerialControlWindow: start failed: %s", exc, exc_info=True)

    def _stop(self) -> None:
        if self.ctx.serial:
            self.ctx.serial.stop()

    def _on_status(self, status: dict) -> None:
        if dpg.does_item_exist(self.tag("status")):
            dpg.set_value(self.tag("status"), status.get("message", ""))

import dearpygui.dearpygui as dpg
import serial.tools.list_ports


class ComMonitorController:
    def __init__(self, ui_manager=None):
        self.ui_manager = ui_manager

        self.com_port_selector = None
        self.baudrate_input = None

        self.controller = None  # <-- ALWAYS exposed

    def draw_ui(self, window_width=200, window_height=300):
        with dpg.child_window(label="COM Monitor", width=window_width, height=window_height):
            dpg.add_text("COM Port Settings")

            com_ports = [port.device for port in serial.tools.list_ports.comports()]
            self.com_port_selector = dpg.add_combo(
                items=com_ports,
                label="COM Port",
                width=100,
                default_value=com_ports[0] if com_ports else "",
            )

            self.baudrate_input = dpg.add_input_int(
                label="Baudrate",
                default_value=115200,
                width=100,
            )

            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", callback=self.start_monitor)
                dpg.add_button(label="Stop", callback=self.stop_monitor)

            dpg.add_spacer(height=10)
            dpg.add_text("Last telemetry packet:", tag="telemetry_label")

    # ------------------------------------------------------------

    def start_monitor(self):
        if self.controller and self.controller.is_running():
            dpg.configure_item("telemetry_label", default_value="Monitor already running!")
            return

        com_port = dpg.get_value(self.com_port_selector)
        baudrate = dpg.get_value(self.baudrate_input)

        if not com_port:
            dpg.configure_item("telemetry_label", default_value="Select a COM port first!")
            return

        from telemetry.com_controller import TelemetryReceiver

        self.controller = TelemetryReceiver(
            com_port=com_port,
            baudrate=baudrate,
        )
        self.controller.set_ui_callback(self.update_ui)
        self.controller.start()

        dpg.configure_item("telemetry_label", default_value="Monitor started.")

    def stop_monitor(self):
        if self.controller:
            self.controller.stop()

        dpg.configure_item("telemetry_label", default_value="Monitor stopped.")

    # ------------------------------------------------------------

    def update_ui(self, packet: dict):
        display_text = "\n".join(f"{k}: {v}" for k, v in packet.items())
        dpg.configure_item("telemetry_label", default_value=display_text)

        if self.ui_manager:
            self.ui_manager.update_all(packet)

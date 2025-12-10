import dearpygui.dearpygui as dpg
import serial.tools.list_ports

class ComMonitorController:
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.com_ports = None
        self.baudrate_input = None
        self.com_port_selector = None
        self.receiver = None
        self.running = False

    def draw_ui(self):
        with dpg.child_window(label="COM Monitor", width=200, height=300):
            dpg.add_text("COM Port Settings")
            self.com_ports = [port.device for port in serial.tools.list_ports.comports()]
            self.com_port_selector = dpg.add_combo(items=self.com_ports, label="COM Port", width=100, default_value="COM3")
            self.baudrate_input = dpg.add_input_int(label="Baudrate", default_value=115200, width=100)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", callback=self.start_monitor)
                dpg.add_button(label="Stop", callback=self.stop_monitor)

            dpg.add_spacer(height=10)
            dpg.add_text("Last telemetry packet:", tag="telemetry_label")

    def start_monitor(self):
        if self.running:
            dpg.configure_item("telemetry_label", default_value="Monitor already running!")
            return

        com_port = dpg.get_value(self.com_port_selector)
        baudrate = dpg.get_value(self.baudrate_input)
        if not com_port:
            dpg.configure_item("telemetry_label", default_value="Select a COM port first!")
            return

        from telemetry.telemetry_receiver import TelemetryReceiver
        self.receiver = TelemetryReceiver(
            com_port=com_port,
            baudrate=baudrate,
            ui_callback=self.update_ui,
        )
        self.receiver.start_listening()
        self.running = True
        dpg.configure_item("telemetry_label", default_value="Monitor started.")

    def stop_monitor(self):
        if self.receiver:
            self.receiver.stop_listening()
        self.running = False
        dpg.configure_item("telemetry_label", default_value="Monitor stopped.")

    def update_ui(self, packet):
        display_text = "\n".join([f"{k}: {v}" for k, v in packet.items()])
        dpg.configure_item("telemetry_label", default_value=display_text)

        if self.ui_manager:
            self.ui_manager.update_all(packet)

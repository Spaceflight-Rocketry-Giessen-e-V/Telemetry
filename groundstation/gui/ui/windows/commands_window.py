import dearpygui.dearpygui as dpg


class CommandsWindow:
    def __init__(self, receiver):
        self.receiver_controller = receiver
        self.status_label = None

    def send(self, command):
        controller = self.receiver_controller.controller

        if not controller or not controller.is_connected():
            dpg.configure_item(self.status_label, default_value="Status: not connected")
            return

        try:
            controller.send_command(command)
            dpg.configure_item(
                self.status_label,
                default_value=f"Status: sent '{command}'"
            )
        except Exception as e:
            dpg.configure_item(self.status_label, default_value=f"Error: {e}")

    def draw_ui(self, window_width=220, window_height=320):
        with dpg.child_window(label="Commands", width=window_width, height=window_height):
            dpg.add_text("COMMANDS")
            with dpg.group(horizontal=True):
                with dpg.group(horizontal=False):
                    dpg.add_text("Ping")
                    dpg.add_button(label="Ping (p)", callback=lambda: self.send("p"))

                dpg.add_spacer()
                with dpg.group(horizontal=False):
                    dpg.add_text("Main Parachute Height")
                    dpg.add_button(label="50 m (a)", callback=lambda: self.send("a"))
                    dpg.add_button(label="100 m (b)", callback=lambda: self.send("b"))
                    dpg.add_button(label="150 m (c)", callback=lambda: self.send("c"))
                    dpg.add_button(label="200 m (d)", callback=lambda: self.send("d"))

                dpg.add_spacer()
                with dpg.group(horizontal=False):
                    dpg.add_text("Low Power Mode")
                    dpg.add_button(label="ON (l)", callback=lambda: self.send("l"))
                    dpg.add_button(label="OFF (m)", callback=lambda: self.send("m"))

                dpg.add_spacer()
                with dpg.group(horizontal=False):
                    dpg.add_text("Flight Mode")
                    dpg.add_button(label="ARM (f)", callback=lambda: self.send("f"))
                    dpg.add_button(label="DISARM (g)", callback=lambda: self.send("g"))

                dpg.add_spacer()
                with dpg.group(horizontal=False):
                    dpg.add_text("Parachute Ejection")
                    dpg.add_button(label="Eject Drogue (q)", callback=lambda: self.send("q"))
                    dpg.add_button(label="Eject Main (r)", callback=lambda: self.send("r"))

                dpg.add_spacer()
                with dpg.group(horizontal=False):
                    dpg.add_text("Status:")
                    self.status_label = dpg.add_text("idle")

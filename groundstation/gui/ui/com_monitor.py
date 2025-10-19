import dearpygui.dearpygui as dpg
import threading
import serial
import serial.tools.list_ports
import time


class ComMonitor:
    """HEX/BIN COM Monitor"""

    def __init__(self):
        self.monitor = None
        self.table = None
        self.lines = []
        self.running = False

    # --- Serial monitor thread ---
    class SerialMonitor:
        def __init__(self, port, baudrate=9600):
            self.port = port
            self.baudrate = baudrate
            self.running = False
            self.ser = None
            self.lines = []

        def start(self):
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
                self.running = True
                threading.Thread(target=self.read_loop, daemon=True).start()
            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")

        def stop(self):
            self.running = False
            if self.ser and self.ser.is_open:
                self.ser.close()

        def read_loop(self):
            while self.running:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    for b in data:
                        hex_val = f"{b:02X}"
                        bin_val = f"{b:08b}"
                        line = f"{hex_val} | {bin_val}"
                        self.lines.append(line)
                        if len(self.lines) > 100:
                            self.lines.pop(0)
                time.sleep(0.05)

    def draw_ui(self):
        with dpg.group(horizontal=True, width=0):  # Main horizontal split
            # --- Left side: controls ---
            with dpg.group(horizontal=False, width=250):
                dpg.add_text("COM Monitor")

                # COM port selection
                ports = [p.device for p in serial.tools.list_ports.comports()]
                dpg.add_text("Select COM Port:")
                self.port_combo = dpg.add_combo(items=ports, default_value=ports[0] if ports else "")

                # Baudrate
                dpg.add_text("Baudrate:")
                self.baud_input = dpg.add_input_int(default_value=9600)

                # Start/Stop buttons
                with dpg.group(horizontal=True):
                    self.start_btn = dpg.add_button(label="Start Monitoring", callback=self.start_monitor)
                    self.stop_btn = dpg.add_button(label="Stop Monitoring", callback=self.stop_monitor)

            # --- Right side: data table ---
            with dpg.group(horizontal=False, width=-1):
                self.table = dpg.add_table(header_row=True,
                                           resizable=True,
                                           policy=dpg.mvTable_SizingStretchProp,
                                           borders_innerH=True,
                                           height=0)  # let height autosize
                dpg.add_table_column(label="HEX", parent=self.table)
                dpg.add_table_column(label="BINARY", parent=self.table)

    def start_monitor(self):
        port = dpg.get_value(self.port_combo)
        baud = dpg.get_value(self.baud_input)
        self.monitor = self.SerialMonitor(port=port, baudrate=baud)
        self.monitor.start()
        self.running = True
        threading.Thread(target=self.update_table_loop, daemon=True).start()

    def stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
        self.running = False

    def update_table_loop(self):
        while self.running and self.monitor:
            dpg.delete_item(self.table, children_only=True)
            for line in self.monitor.lines:
                hex_val, bin_val = line.split(" | ")
                with dpg.table_row(parent=self.table):
                    dpg.add_text(hex_val)
                    dpg.add_text(bin_val)
            time.sleep(0.1)

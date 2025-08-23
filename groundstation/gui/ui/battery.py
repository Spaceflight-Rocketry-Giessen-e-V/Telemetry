import dearpygui.dearpygui as dpg


class Battery:
    voltage_min = 9.0
    voltage_max = 12.6
    voltage_critical = 10.5
    voltage_current = 12.6  # starting voltage

    @classmethod
    def draw_ui(cls):
        with dpg.child_window(label="Battery", width=300, height=200):
            dpg.add_text("Battery Status")
            dpg.add_progress_bar(default_value=1.0, width=-1, height=30, tag="battery_bar")
            with dpg.group(horizontal=True):
                dpg.add_text(f"{cls.voltage_current:.2f}V", tag="battery_label")
                dpg.add_text("UNDERVOLTAGE", tag="battery_warning", color=(255, 0, 0, 255))

            # Min, Max, Critical labels
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=False):
                dpg.add_text(f"Min: {cls.voltage_min:.2f}V", tag="battery_min")
                dpg.add_text(f"Critical: {cls.voltage_critical:.2f}V", tag="battery_critical")
                dpg.add_text(f"Max: {cls.voltage_max:.2f}V", tag="battery_max")

            dpg.hide_item("battery_warning")

    @classmethod
    def update_voltage(cls, voltage):
        # Clamp voltage to Min/Max limits
        cls.voltage_current = max(cls.voltage_min, min(voltage, cls.voltage_max))

        # Update progress bar
        fraction = (cls.voltage_current - cls.voltage_min) / (cls.voltage_max - cls.voltage_min)
        dpg.set_value("battery_bar", fraction)

        # Update voltage label
        dpg.set_value("battery_label", f"{cls.voltage_current:.2f}V")

        # Show warning if voltage below critical
        if cls.voltage_current <= cls.voltage_critical:
            dpg.show_item("battery_warning")
        else:
            dpg.hide_item("battery_warning")

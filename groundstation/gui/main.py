import os
import sys
import time
import threading
import random
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

import simulation
import ui.location
import ui.altitude
import ui.battery
import ui.map_view
from ui.com_monitor import ComMonitor


# ---------- Cross-platform Screen Resolution ----------
def get_screen_resolution():
    """Detect screen resolution cross-platform."""
    if sys.platform.startswith("win"):
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    else:  # Linux / macOS
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height


def start_simulation():
    ui.map_view.Map.update_location(ui.location.Location.lat, ui.location.Location.lon)
    simulation.init_simulation()
    threading.Thread(target=simulation.update_fake_data, daemon=True).start()


def shutdown():
    dpg.destroy_context()


# ---------- UI Build ----------
def draw_main_ui():
    with dpg.group(horizontal=True):
        with dpg.group(horizontal=False):
            # Altitude View
            ui.altitude.Altitude.draw_ui()

            with dpg.group(horizontal=True):
                # Battery status view
                ui.battery.Battery.draw_ui()

                # Flight events view
                with dpg.child_window(width=300, height=400):
                    dpg.add_text("Flight Events")
                    dpg.add_listbox(items=[], tag="event_list", width=250, num_items=10)
        # Location view
        ui.map_view.Map.draw_ui()

        # Right panel
        # with dpg.child_window(width=300, height=400):
        #    dpg.add_text("Acceleration")
        #    dpg.add_text("Current: 0.0 m/s²", tag="accel_current")
        #    dpg.add_text("Min: 0.0 m/s²", tag="accel_min")
        #    dpg.add_text("Max: 0.0 m/s²", tag="accel_max")
        #    dpg.add_text("Avg: 0.0 m/s²", tag="accel_avg")


# ---------- Main View ----------
def build_ui():
    dpg.create_context()

    # Detect screen resolution dynamically
    screen_width, screen_height = get_screen_resolution()

    # Fullscreen, borderless viewport
    dpg.create_viewport(
        title="MeerKat Ground Station",
        width=screen_width,
        height=screen_height,
        x_pos=0,
        y_pos=0,
        decorated=False
    )

    # TODO fix close button not working
    # Clean exit on close
    dpg.set_exit_callback(lambda: shutdown())

    # Exit on Hotkey
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=lambda: shutdown())

    # Main window
    with dpg.window(
            label="MeerKat Ground Station",
            width=screen_width,
            height=screen_height,
            no_move=True,
            no_resize=True
    ):
        with dpg.tab_bar():
            with dpg.tab(label="Flight Data"):
                draw_main_ui()

                dpg.add_button(label="Start Simulation",
                               callback=lambda: start_simulation())

            with dpg.tab(label="COM Monitor"):
                com_monitor = ComMonitor()
                com_monitor.draw_ui()
    # demo.show_demo()

    dpg.setup_dearpygui()
    dpg.show_viewport()

    # TODO remove dev test
    # Launch fake data generator in background
    # threading.Thread(target=simulation.update_fake_data, daemon=True).start()

    dpg.start_dearpygui()


if __name__ == "__main__":
    build_ui()

import time, random
import dearpygui.dearpygui as dpg
import ui.location
import ui.altitude
import ui.battery

start_time = time.time()
target_altitude = 1000.0
current_altitude = 0.0
ascending = True
gps_lat, gps_lon = 50.0, 8.0
gps_drift = 0.0
event_triggered = {"launch": False, "stagesep": False, "airbrake": False, "chute": False, "landing": False,"launch": False, "stagesep": False, "airbrake": False, "chute": False, "landing": False}
"""
00 - Pad Idle
01 - Main Chute Altitude Set
02 - Armed
03 - Pyros Continuity Check
04 - Liftoff
05 - Booster Burnout
06 - Apogee detected 
07 - Pyro 1 signal sent (drogue)
08 - Pyro2 signal sent (drogue)
09 - Drogue deployment detected
10 - Pyro3 signal sent (main)
11 - Pyro4 signal sent (main)
12 - Main deployment detected
13 - Landed
14 - ABORT -Failed to initialize
15 - ABORT - No Continuity
"""


def init_simulation():
    global start_time
    start_time = time.time()


def update_fake_data():
    global current_altitude, gps_drift, ascending, event_triggered

    last_time = time.time()
    while dpg.is_dearpygui_running():
        now = time.time()
        dt = now - last_time
        last_time = now

        # --- Altitude simulation (piecewise curve) ---
        if ascending:
            jerk = random.uniform(-5, 5)  # minor random fluctuation

            # S1 Boost
            if current_altitude < 0.5 * target_altitude:
                current_altitude += 250 * dt + jerk
            # S1 Coast / StageSep
            elif current_altitude < 0.55 * target_altitude:
                current_altitude += 100 * dt + jerk
            # S2 Boost
            elif current_altitude < 0.9 * target_altitude:
                current_altitude += 250 * dt + jerk
            # Air brakes
            elif current_altitude < 0.95 * target_altitude:
                current_altitude += 30 * dt + jerk
            else:
                ascending = False
        else:
            descent_rate = 200 if not event_triggered["chute"] else 50
            jerk = random.uniform(-5, 5)  # minor random fluctuation
            current_altitude -= descent_rate * dt - jerk
            if current_altitude < 0:
                current_altitude = 0

        # Update altitude plot
        elapsed = now - start_time
        ui.altitude.Altitude.update_altitude(elapsed, current_altitude)

        # --- GPS drift ---
        drift_limit = 0.001
        gps_drift += random.uniform(-0.00005, 0.00006)
        gps_drift = max(-drift_limit, min(drift_limit, gps_drift))
        ui.location.Location.update_gps(gps_lat + gps_drift, gps_lon + gps_drift)

        # --- Battery ---
        voltage = max(9.0, 12.6 - (now - start_time) * 0.1)
        ui.battery.Battery.update_voltage(voltage)

        # --- Acceleration ---
        # accel = random.uniform(-1, 5)
        # dpg.set_value("accel_current", f"Current: {accel:.2f} m/s²")

        # --- Event triggers ---
        if not event_triggered["launch"]:
            add_event("Launch")
            event_triggered["launch"] = True

        if not event_triggered["stagesep"] and current_altitude >= target_altitude / 2:
            add_event("Stage Sep")
            event_triggered["stagesep"] = True

        if not event_triggered["airbrake"] and current_altitude >= 0.9 * target_altitude:
            add_event("Airbrakes")
            event_triggered["airbrake"] = True

        if not event_triggered["chute"] and not ascending and current_altitude <= 800:
            add_event("Chute Deploy")
            event_triggered["chute"] = True

        if not event_triggered["landing"] and not ascending and current_altitude <= 0:
            add_event("Landing")
            event_triggered["landing"] = True

        time.sleep(0.1)


def add_event(event_name):
    items = dpg.get_item_configuration("event_list")["items"]
    dpg.configure_item("event_list", items=[event_name] + items)

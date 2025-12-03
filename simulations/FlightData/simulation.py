import os
import time
import csv
import json
from dataclasses import dataclass
import numpy as np
import matplotlib
import dearpygui.dearpygui as dpg
from PIL import Image
from matplotlib import pyplot as plt

matplotlib.use("Agg")

# ---------------------------
# Default constants
# ---------------------------
DEFAULTS = {
    "GRAVITY": 10.0,
    "A_ASCENT": 35.0,
    "V_DESCENT": 15.0,
    "WIND": 10.0,
    "BATT_DRAIN": 0.11,
    "DT": 0.125,
    "LAT0": 49.811425,
    "LON0": 8.855205,
    "POS0": 50.0,
    "BATT0": 8.4,
    "V_DESCENT_DROGUE": 25.0,
    "V_DESCENT_MAIN": 5.0,
    "MAIN_CHUTE_DEPLOYMENT_HEIGHT": 150.0,
}

# Units for UI labels
UNITS = {
    "GRAVITY": "m/s^2",
    "A_ASCENT": "m/s^2",
    "V_DESCENT": "m/s",
    "WIND": "m/s",
    "BATT_DRAIN": "V/s",
    "DT": "s",
    "LAT0": "deg",
    "LON0": "deg",
    "POS0": "m",
    "BATT0": "V",
    "V_DESCENT_DROGUE": "m/s",
    "V_DESCENT_MAIN": "m/s",
    "MAIN_CHUTE_DEPLOYMENT_HEIGHT": "m",

}

CSV_DIR = "flight_data"
os.makedirs(CSV_DIR, exist_ok=True)


# ---------------------------------------------
# Simulation helpers
# ---------------------------------------------
def deg_per_meter():
    return 360 / (2 * np.pi * 6_371_000)


def battery_drain(start_v, t, drain_rate):
    return start_v - drain_rate * t


@dataclass
class Phase:
    name: str
    t_start: float
    duration: float
    acc: np.ndarray
    vel: np.ndarray
    height: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    pos: np.ndarray
    bat: np.ndarray
    event: np.ndarray


def create_phase(name, t_start, t_end, acc_func, vel_func, h_func,
                 lat_func, lon_func, pos_func, bat_func, event_val, dt):
    t = np.arange(t_start, t_end, dt)
    t_rel = t - t_start
    return Phase(
        name=name,
        t_start=t_start,
        duration=t_end - t_start,
        acc=acc_func(t_rel),
        vel=vel_func(t_rel),
        height=h_func(t_rel),
        lat=lat_func(t_rel),
        lon=lon_func(t_rel),
        pos=pos_func(t_rel),
        bat=bat_func(t_rel),
        event=np.full(t.size, event_val, dtype=int)
    ), t


def simulate(constants):
    """Run a full rocket flight simulation with safe handling and all events."""
    GRAVITY = constants["GRAVITY"]
    A_ASCENT = constants["A_ASCENT"]
    V_DESCENT = constants["V_DESCENT"]
    WIND = constants["WIND"]
    BATT_DRAIN = constants["BATT_DRAIN"]
    DT = constants["DT"]
    LAT0 = constants["LAT0"]
    LON0 = constants["LON0"]
    POS0 = constants["POS0"]
    BATT0 = constants["BATT0"]
    V_DESCENT_DROGUE = constants["V_DESCENT_DROGUE"]
    V_DESCENT_MAIN = constants["V_DESCENT_MAIN"]
    MAIN_CHUTE_DEPLOYMENT_HEIGHT = constants["MAIN_CHUTE_DEPLOYMENT_HEIGHT"]

    deg_m = deg_per_meter()

    # Event codes
    EVT = {
        "PAD_IDLE": 0,
        "MAIN_CHUTE_ALTITUDE_SET": 1,
        "ARMED": 2,
        "PYROS_CONTINUITY_CHECK": 3,
        "LIFTOFF": 4,
        "BOOSTER_BURNOUT": 5,
        "APOGEE_DETECTED": 6,
        "PYRO1_DROGUE": 7,
        "PYRO2_DROGUE": 8,
        "DROGUE_DEPLOYMENT_DETECTED": 9,
        "PYRO3_MAIN": 10,
        "PYRO4_MAIN": 11,
        "MAIN_DEPLOYMENT_DETECTED": 12,
        "LANDED": 13,
        "ABORT_INIT_FAIL": 14,
        "ABORT_NO_CONTINUITY": 15
    }

    def safe_last(arr, default):
        """Return last element of arr or default if empty."""
        return arr[-1] if len(arr) > 0 else default

    def create_safe_phase(name, t_start, t_end, acc_func, vel_func, h_func,
                          lat_func, lon_func, pos_func, bat_func, event_val):
        """Create a phase safely, return phase object."""
        duration = max(0, t_end - t_start)
        phase, _ = create_phase(
            name, t_start, t_start + duration,
            acc_func=acc_func,
            vel_func=vel_func,
            h_func=h_func,
            lat_func=lat_func,
            lon_func=lon_func,
            pos_func=pos_func,
            bat_func=bat_func,
            event_val=event_val,
            dt=DT
        )
        return phase

    # -------------------------
    # Phase 1: Launchpad
    # -------------------------
    t1 = 3
    phase1 = create_safe_phase(
        "Launchpad", 0, t1,
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, LAT0),
        lambda t: np.full_like(t, LON0),
        lambda t: np.full_like(t, POS0),
        lambda t: np.full_like(t, BATT0),
        EVT["PAD_IDLE"]
    )

    # -------------------------
    # Phase 2: Powered Ascent
    # -------------------------
    t2 = 3
    net_acc = A_ASCENT - GRAVITY
    phase2 = create_safe_phase(
        "Powered Ascent", t1, t1 + t2,
        lambda t: np.full_like(t, net_acc),
        lambda t: net_acc * t,
        lambda t: 0.5 * net_acc * t ** 2,
        lambda t: LAT0 - WIND / np.sqrt(2) * deg_m * t,
        lambda t: LON0 + WIND / np.sqrt(2) * deg_m * t,
        lambda t: POS0 + WIND * t,
        lambda t: battery_drain(BATT0, t, BATT_DRAIN),
        EVT["LIFTOFF"]
    )

    # Get phase2 end state safely
    v_end = safe_last(phase2.vel, 0)
    h_end = safe_last(phase2.height, 0)
    lat_end = safe_last(phase2.lat, LAT0)
    lon_end = safe_last(phase2.lon, LON0)
    pos_end = safe_last(phase2.pos, POS0)
    bat_end = safe_last(phase2.bat, BATT0)

    # -------------------------
    # Phase 3: Coasting
    # -------------------------
    t3 = max(0, t2 * net_acc / GRAVITY) if GRAVITY else 0
    phase3 = create_safe_phase(
        "Coasting", t1 + t2, t1 + t2 + t3,
        lambda t: np.full_like(t, -GRAVITY),
        lambda t: v_end - GRAVITY * t,
        lambda t: h_end + v_end * t - 0.5 * GRAVITY * t ** 2,
        lambda t: lat_end - WIND / np.sqrt(2) * deg_m * t,
        lambda t: lon_end + WIND / np.sqrt(2) * deg_m * t,
        lambda t: pos_end + WIND * t,
        lambda t: battery_drain(bat_end, t, BATT_DRAIN),
        EVT["APOGEE_DETECTED"]
    )

    # -------------------------
    # Phase 4A: DROGUE descent from apogee
    # -------------------------
    apogee_height = safe_last(phase3.height, 0)
    t_apogee = phase3.t_start + phase3.duration

    t4a = (apogee_height-MAIN_CHUTE_DEPLOYMENT_HEIGHT) / V_DESCENT_DROGUE if apogee_height > 0 else 0

    phase4a = create_safe_phase(
        "Drogue Descent", t_apogee, t_apogee + t4a,
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, -V_DESCENT_DROGUE),
        lambda t: apogee_height - V_DESCENT_DROGUE * t,
        lambda t: safe_last(phase3.lat, LAT0) - WIND / np.sqrt(2) * deg_m * t,
        lambda t: safe_last(phase3.lon, LON0) + WIND / np.sqrt(2) * deg_m * t,
        lambda t: safe_last(phase3.pos, POS0) + WIND * t,
        lambda t: battery_drain(safe_last(phase3.bat, BATT0), t, BATT_DRAIN),
        EVT["DROGUE_DEPLOYMENT_DETECTED"]
    )

    # Correct event at start
    if len(phase4a.event) > 0:
        phase4a.event[0] = EVT["DROGUE_DEPLOYMENT_DETECTED"]

    # -------------------------
    # Phase 4B: MAIN CHUTE descent (when height reaches MAIN_CHUTE_DEPLOYMENT_HEIGHT)
    # -------------------------
    h_start_main = MAIN_CHUTE_DEPLOYMENT_HEIGHT
    t4b = MAIN_CHUTE_DEPLOYMENT_HEIGHT / V_DESCENT_MAIN

    phase4b = create_safe_phase(
        "Main Descent", phase4a.t_start + phase4a.duration, phase4a.t_start + phase4a.duration + t4b,
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, -V_DESCENT_MAIN),
        lambda t: h_start_main - V_DESCENT_MAIN * t,
        lambda t: safe_last(phase4a.lat, LAT0) - WIND / np.sqrt(2) * deg_m * t,
        lambda t: safe_last(phase4a.lon, LON0) + WIND / np.sqrt(2) * deg_m * t,
        lambda t: safe_last(phase4a.pos, POS0) + WIND * t,
        lambda t: battery_drain(safe_last(phase4a.bat, BATT0), t, BATT_DRAIN),
        EVT["MAIN_DEPLOYMENT_DETECTED"]
    )

    if len(phase4b.event) > 0:
        phase4b.event[0] = EVT["MAIN_DEPLOYMENT_DETECTED"]

    # -------------------------
    # Phase 5: Landing
    # -------------------------
    t5 = 5
    phase5 = create_safe_phase(
        "Landing", t1 + t2 + t3 + t4a + t4b, t1 + t2 + t3 + t4a + t4b + t5,
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, safe_last(phase4b.lat, LAT0)),
        lambda t: np.full_like(t, safe_last(phase4b.lon, LON0)),
        lambda t: np.full_like(t, safe_last(phase4b.pos, POS0)),
        lambda t: battery_drain(safe_last(phase4b.bat, BATT0), t, BATT_DRAIN),
        EVT["LANDED"]
    )

    # -------------------------
    # Concatenate all phases
    # -------------------------
    phases = [phase1, phase2, phase3, phase4a, phase4b, phase5]
    sim_data = {
        k: np.concatenate([getattr(p, k) for p in phases])
        for k in ["acc", "vel", "height", "lat", "lon", "pos", "bat", "event"]
    }
    sim_data["time"] = np.concatenate([np.arange(p.t_start, p.t_start + p.duration, DT) for p in phases])

    return sim_data


# -------------------------
# CSV + JSON IO
# -------------------------
def make_filename(prefix="flight_data"):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}"


def write_simulation(sim_data, constants, folder_path=None):
    if folder_path is None:
        file_path = os.path.join(CSV_DIR, make_filename())
    else:
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, make_filename())

    # Prepare derived arrays
    time_a = sim_data["time"]
    acc_a = sim_data["acc"]
    vel_a = sim_data["vel"]
    height_a = sim_data["height"]
    lat_a = sim_data["lat"]
    lon_a = sim_data["lon"]
    pos_a = sim_data["pos"]
    bat_a = sim_data["bat"]
    event_a = sim_data["event"]

    height_gnss = height_a * 1.1
    flight_mode = (event_a >= 2).astype(int)
    low_power_mode = np.zeros_like(time_a, dtype=int)
    temperature_c = np.full_like(time_a, 20.0, dtype=float)
    subsystem_status = np.full_like(time_a, 7, dtype=int)

    # CSV
    csv_file = file_path + ".csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        headers = [
            "time (s)",
            "acceleration (m/s^2)",
            "velocity (m/s)",
            "height (m)",
            "gnss_height (m)",
            "latitude (deg)",
            "longitude (deg)",
            "displacement (m)",
            "battery (V)",
            "event_code (int)",
            "flight_mode (0=manual/1=auto)",
            "low_power_mode (0/1)",
            "temperature_c (°C)",
            "subsystem_status (int)"
        ]
        writer.writerow(headers)
        for row in zip(time_a, acc_a, vel_a, height_a, height_gnss,
                       lat_a, lon_a, pos_a, bat_a, event_a,
                       flight_mode, low_power_mode, temperature_c, subsystem_status):
            writer.writerow(row)

    # JSON (constants)
    json_file = file_path + ".json"
    with open(json_file, 'w') as f:
        json.dump(constants, f, indent=4)

    return csv_file, json_file


def read_simulation_from_csv(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        data = {k: [] for k in reader.fieldnames}
        for row in reader:
            for k, v in row.items():
                # Try to parse floats; if fails, keep as string
                try:
                    data[k].append(float(v))
                except Exception:
                    data[k].append(v)
    # Convert numeric columns to numpy arrays. Strings remain lists.
    out = {}
    for k, v in data.items():
        # if all entries are numbers, convert to numpy array
        if len(v) == 0:
            out[k] = np.array([])
        else:
            try:
                arr = np.array(v, dtype=float)
                out[k] = arr
            except Exception:
                out[k] = np.array(v, dtype=object)
    return out


# -------------------------
# Plotting
# -------------------------
def plot_simulation_data_to_png(sim_data, png_path, title="Flight Simulation"):
    time_s = sim_data["time"]
    acc = sim_data["acc"]
    vel = sim_data["vel"]
    height = sim_data["height"]
    lat = sim_data["lat"]
    lon = sim_data["lon"]
    pos = sim_data["pos"]
    bat = sim_data["bat"]
    event = sim_data["event"]

    height_gnss = height * 1.1  # simulated GNSS height

    EVT_LABELS = [
        "Pad Idle", "Main Chute Altitude Set", "Armed", "Pyros Check", "Liftoff",
        "Booster Burnout", "Apogee", "Pyro1 Drogue", "Pyro2 Drogue",
        "Drogue Deploy", "Pyro3 Main", "Pyro4 Main", "Main Deploy", "Landed",
        "ABORT Init Fail", "ABORT No Continuity"
    ]

    fig, axs = plt.subplots(4, 2, figsize=(10, 10), dpi=150)
    axs01b = axs[0, 1].twinx()
    axs31b = axs[3, 1].twinx()

    # -------------------------
    # Left column: acc, vel, height, battery
    # -------------------------
    axs[0, 0].plot(time_s, acc, color='k', lw=0.8)
    axs[1, 0].plot(time_s, vel, color='k', lw=0.8)
    axs[2, 0].plot(time_s, height, color='k', lw=0.8)
    axs[3, 0].plot(time_s, bat, color='k', lw=0.8)

    # -------------------------
    # Right column: lat/lon, pos, GNSS height, event
    # -------------------------
    axs[0, 1].plot(time_s, lat, color='k', lw=0.8)
    axs01b.plot(time_s, lon, color='r', lw=0.6)
    axs[1, 1].plot(time_s, pos, color='k', lw=0.8)
    axs[2, 1].plot(time_s, height_gnss, color='k', lw=0.8)
    axs[3, 1].plot(time_s, event, color='k', lw=0.8)

    # -------------------------
    # Axes formatting
    # -------------------------
    for ax_row in axs:
        for ax in ax_row:
            ax.set_xlim(0, np.max(time_s) if time_s.size else 1)
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.set_xlabel("Time (s)")

    # Twin axes formatting
    axs01b.set_ylabel("Longitude (°)")
    axs[0, 0].set_ylabel("Acceleration (m/s²)")
    axs[1, 0].set_ylabel("Velocity (m/s)")
    axs[2, 0].set_ylabel("Height (m)")
    axs[3, 0].set_ylabel("Battery (V)")

    axs[0, 1].set_ylabel("Latitude (°)")
    axs[1, 1].set_ylabel("Displacement (m)")
    axs[2, 1].set_ylabel("GNSS Height (m)")
    axs[3, 1].set_ylabel("Event")

    # Map event codes to labels on the y-axis
    axs31b.set_yticks(np.arange(len(EVT_LABELS)))
    axs31b.set_yticklabels(EVT_LABELS)
    axs31b.set_ylim(axs[3, 1].get_ylim())  # synchronize y-limits

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    png_out = png_path + ".png"
    fig.savefig(png_out, bbox_inches='tight')
    plt.close(fig)
    return png_out


# -----------------------------
# GUI Callback Functions
# -----------------------------
STATE = {
    "last_png": None,
    "last_csv": None,
    "last_json": None,
    "texture_tag": None,
    "sim_data": None
}


def run_simulation_callback(sender, app_data, user_data):
    """Run the simulation with current constants, save CSV/JSON/PNG, and display PNG in GUI."""
    # 1. Read constants from GUI (values are floats)
    constants = {k: dpg_get_value(v) for k, v in user_data["mapping"].items()}

    # 2. Run simulation
    sim_data = simulate(constants)
    STATE["sim_data"] = sim_data

    # 3. Specify destination folder
    base_path = os.path.join(CSV_DIR, time.strftime("%Y-%m-%d_%H-%M-%S"))

    # 4. Save CSV + JSON
    csv_path, json_path = write_simulation(sim_data, constants, base_path)
    STATE["last_csv"] = csv_path
    STATE["last_json"] = json_path

    # 5. Save PNG plot
    png_base_path = os.path.join(CSV_DIR, time.strftime("%Y-%m-%d_%H-%M-%S"), make_filename("flight_data"))
    png_path = plot_simulation_data_to_png(sim_data, png_base_path, title=os.path.basename(csv_path))
    STATE["last_png"] = png_path

    # 6. Load PNG into DearPyGui
    load_png_into_dpg(png_path)

    # 7. Update status text
    dpg_set_value("status_text",
                  f"Simulation saved.\nCSV: {csv_path}\nJSON: {json_path}\nPNG: {png_path}")


def run_sim_only_callback(sender, app_data, user_data):
    constants = {k: dpg_get_value(v) for k, v in user_data["mapping"].items()}
    sim_data = simulate(constants)
    STATE["sim_data"] = sim_data

    # Save only PNG
    png_base_path = os.path.join(CSV_DIR, "temp_plot")
    png_path = plot_simulation_data_to_png(sim_data, png_base_path)
    STATE["last_png"] = png_path

    load_png_into_dpg(png_path)
    dpg_set_value("status_text", "Simulation executed (not saved).")


def load_png_into_dpg(png_path):
    """Load PNG into DPG texture. Updates existing texture dynamically."""
    if not os.path.exists(png_path):
        dpg_set_value("status_text", f"PNG not found: {png_path}")
        return

    # Load image with PIL and normalize to float32 for DPG
    img = Image.open(png_path).convert("RGBA")
    img_width, img_height = img.size
    data = np.array(img, dtype=np.float32).flatten() / 255.0  # normalize to [0,1]

    # If texture exists, update it
    if STATE.get("texture_tag") and dpg.does_item_exist(STATE["texture_tag"]):
        dpg.set_value(STATE["texture_tag"], data)
    else:
        # Create a new dynamic texture
        with dpg.texture_registry(show=False):
            tex_tag = dpg.generate_uuid()
            dpg.add_dynamic_texture(img_width, img_height, data, tag=tex_tag)
            STATE["texture_tag"] = tex_tag

        # Assign texture to image widget
        if dpg.does_item_exist("plot_image"):
            dpg.configure_item("plot_image", texture_tag=STATE["texture_tag"])


# Small DPG helpers to wrap API differences
def dpg_get_value(item):
    try:
        return float(dpg.get_value(item))
    except Exception:
        # fallback: try to get default_value
        try:
            return float(dpg.get_item_configuration(item).get("default_value"))
        except Exception:
            return 0.0


def dpg_set_value(item, value):
    try:
        dpg.set_value(item, value)
    except Exception:
        try:
            dpg.configure_item(item, default_value=value)
        except Exception:
            pass


def load_json_selected(sender, app_data, user_data):
    file_path = app_data['file_path_name']

    try:
        with open(file_path, "r") as f:
            constants = json.load(f)

        for key, tag in user_data["mapping"].items():
            if key in constants:
                dpg_set_value(tag, float(constants[key]))

        dpg_set_value("status_text", f"Loaded constants from {file_path}")

    except Exception as e:
        dpg_set_value("status_text", f"Error loading JSON: {e}")


def load_json_callback(sender, app_data, user_data):
    dpg.configure_item("json_file_dialog", show=True, user_data=user_data)


# -------------------------
# GUI construction
# -------------------------

# Build GUI
dpg.create_context()

GRAY = (60 / 255, 60 / 255, 60 / 255, 1.0)
default_img_width, default_img_height = 1184, 1477
count = default_img_width * default_img_height

# flat RGBA gray image
default_texture = GRAY * count

with dpg.texture_registry():
    dpg.add_dynamic_texture(
        width=default_img_width,
        height=default_img_height,
        default_value=default_texture,
        tag="plot_texture"
    )

# Load JSON file dialog
with dpg.file_dialog(directory_selector=False, show=False, callback=load_json_selected, tag="json_file_dialog"):
    dpg.add_file_extension(".json", color=(0, 255, 0, 255))

# Main view
with dpg.window(label="Flight Simulation GUI", width=1900, height=1040, no_resize=True, no_move=True,
                no_scrollbar=True):
    with dpg.group(horizontal=True):
        # left side
        with dpg.child_window(width=550, height=1000):
            mapping = {}
            dpg.add_text("Editable constants (units shown):")

            for key, val in DEFAULTS.items():
                tag = f"input_{key}"
                unit = UNITS.get(key, "")
                label = f"{key} [{unit}]" if unit else key
                dpg.add_input_float(label=label, default_value=float(val), tag=tag)
                mapping[key] = tag

            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load JSON Parameters",
                               callback=load_json_callback,
                               user_data={"mapping": mapping})

                dpg.add_button(label="Run Simulation",
                               callback=run_sim_only_callback,
                               user_data={"mapping": mapping})
                dpg.add_button(label="Save Simulation",
                               callback=run_simulation_callback,
                               user_data={"mapping": mapping})
            dpg.add_spacer()
            dpg.add_text("", tag="status_text")

        # right side
        with dpg.child_window(width=700, height=1000, autosize_x=True, autosize_y=True):
            dpg.add_text("Generated plot:")

            texture_height = 900
            texture_width = int(texture_height * (1485 / 1477))  # scale width proportionally

            dpg.add_image("plot_texture", tag="plot_image",
                          width=texture_width, height=texture_height)

dpg.create_viewport(title='Flight Simulation', width=1920, height=1080, resizable=False)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

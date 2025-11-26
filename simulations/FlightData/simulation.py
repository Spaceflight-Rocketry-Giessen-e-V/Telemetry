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
    "V_ASCENT": 30.0,
    "V_DESCENT": 20.0,
    "WIND": 20.0,
    "BATT_DRAIN": 0.11,
    "DT": 0.125,
    "LAT0": 50.587249,
    "LON0": 8.683231,
    "POS0": 100.0,
    "BATT0": 8.4,
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
    V_ASCENT = constants["V_ASCENT"]
    V_DESCENT = constants["V_DESCENT"]
    WIND = constants["WIND"]
    BATT_DRAIN = constants["BATT_DRAIN"]
    DT = constants["DT"]
    LAT0 = constants["LAT0"]
    LON0 = constants["LON0"]
    POS0 = constants["POS0"]
    BATT0 = constants["BATT0"]

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
    net_acc = V_ASCENT - GRAVITY
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
    # Phase 4: Descent (with drogue and main chutes)
    # -------------------------
    h_last = safe_last(phase3.height, 0)
    t4 = h_last / V_DESCENT if V_DESCENT and h_last > 0 else 0
    lat_last = safe_last(phase3.lat, LAT0)
    lon_last = safe_last(phase3.lon, LON0)
    pos_last = safe_last(phase3.pos, POS0)
    bat_last = safe_last(phase3.bat, BATT0)

    # Descent phase
    phase4 = create_safe_phase(
        "Descent", t1 + t2 + t3, t1 + t2 + t3 + t4,
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, -V_DESCENT),
        lambda t: h_last - V_DESCENT * t,
        lambda t: lat_last - WIND / np.sqrt(2) * deg_m * t,
        lambda t: lon_last + WIND / np.sqrt(2) * deg_m * t,
        lambda t: pos_last + WIND * t,
        lambda t: battery_drain(bat_last, t, BATT_DRAIN),
        EVT["PYRO1_DROGUE"]
    )

    # Insert all relevant events within descent
    n = len(phase4.event)
    if n > 0:
        # Drogue events
        phase4.event[:n // 4] = EVT["PYRO1_DROGUE"]
        phase4.event[n // 4:n // 2] = EVT["PYRO2_DROGUE"]
        phase4.event[n // 2:3 * n // 4] = EVT["DROGUE_DEPLOYMENT_DETECTED"]
        # Main chute events
        phase4.event[3 * n // 4:] = EVT["MAIN_DEPLOYMENT_DETECTED"]

    # -------------------------
    # Phase 5: Landing
    # -------------------------
    t5 = 3
    phase5 = create_safe_phase(
        "Landing", t1 + t2 + t3 + t4, t1 + t2 + t3 + t4 + t5,
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.zeros_like(t),
        lambda t: np.full_like(t, safe_last(phase4.lat, LAT0)),
        lambda t: np.full_like(t, safe_last(phase4.lon, LON0)),
        lambda t: np.full_like(t, safe_last(phase4.pos, POS0)),
        lambda t: battery_drain(safe_last(phase4.bat, BATT0), t, BATT_DRAIN),
        EVT["LANDED"]
    )

    # -------------------------
    # Concatenate all phases
    # -------------------------
    phases = [phase1, phase2, phase3, phase4, phase5]
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


def write_simulation(sim_data, constants, file_path=None):
    if file_path is None:
        file_path = os.path.join(CSV_DIR, make_filename())

    # CSV
    csv_file = file_path + ".csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time", "acc", "vel", "height", "lat", "lon", "pos", "bat", "event"])
        for row in zip(sim_data["time"], sim_data["acc"], sim_data["vel"], sim_data["height"],
                       sim_data["lat"], sim_data["lon"], sim_data["pos"], sim_data["bat"], sim_data["event"]):
            writer.writerow(row)

    # JSON
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
                data[k].append(float(v))
    return {k: np.array(v) for k, v in data.items()}


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
    fig.savefig(png_path, bbox_inches='tight')
    plt.close(fig)
    return png_path


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
    # 1. Read constants from GUI
    constants = {k: dpg_get_value(v) for k, v in user_data["mapping"].items()}

    # 2. Run simulation
    sim_data = simulate(constants)
    STATE["sim_data"] = sim_data

    # 3. Create unique base filename
    base_path = os.path.join(CSV_DIR, make_filename())

    # 4. Save CSV + JSON
    csv_path, json_path = write_simulation(sim_data, constants, base_path)
    STATE["last_csv"] = csv_path
    STATE["last_json"] = json_path

    # 5. Save PNG plot
    png_path = base_path + ".png"
    plot_simulation_data_to_png(sim_data, png_path, title=os.path.basename(csv_path))
    STATE["last_png"] = png_path

    # 6. Load PNG into DearPyGui
    load_png_into_dpg(png_path)

    # 7. Update status text
    dpg_set_value("status_text",
                  f"Simulation saved.\nCSV: {csv_path}\nJSON: {json_path}\nPNG: {png_path}")


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
        return dpg.get_value(item)
    except Exception:
        return dpg.get_item_configuration(item).get("default_value")


def dpg_set_value(item, value):
    try:
        dpg.set_value(item, value)
    except Exception:
        try:
            dpg.configure_item(item, default_value=value)
        except Exception:
            pass


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

with dpg.window(label="Flight Simulation GUI", width=1900, height=1040, no_resize=True, no_move=True,
                no_scrollbar=True):
    with dpg.group(horizontal=True):
        # left side
        with dpg.child_window(width=360, height=1000):

            mapping = {}
            dpg.add_text("Editable constants:")

            for key, val in DEFAULTS.items():
                tag = f"input_{key}"
                if isinstance(val, int) or float(val).is_integer():
                    dpg.add_input_int(label=key, default_value=int(val), tag=tag)
                else:
                    dpg.add_input_float(label=key, default_value=float(val), tag=tag)
                mapping[key] = tag

            dpg.add_separator()
            dpg.add_button(label="Run Simulation", callback=run_simulation_callback, user_data={"mapping": mapping})
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

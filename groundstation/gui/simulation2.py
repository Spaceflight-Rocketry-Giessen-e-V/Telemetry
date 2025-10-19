import csv
import os
import time
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from matplotlib import pyplot as plt

CSV_FILE = "flight_data/flight_data.csv"

# Default flight parameters
G = 10.0
A = 30.0
V_DESCENT = 20
WIND = 20
BATT_DRAIN = 0.11
DT = 0.125

LAT0 = 50.587249
LON0 = 8.683231
POS0 = 100
BATT0 = 8.4


# ---------------------------------------------
# Simulation helpers
# ---------------------------------------------
def deg_per_meter():
    return 360 / (2 * np.pi * 6_371_000)


def battery_drain(start_v, t):
    return start_v - BATT_DRAIN * t


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
                 lat_func, lon_func, pos_func, bat_func, event_val):
    t = np.arange(t_start, t_end, DT)
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
        event=np.full(t.size, event_val)
    ), t


# ---------------------------------------------
# Simulation setup
# ---------------------------------------------
def simulate():
    """Run the full rocket flight simulation and return all arrays."""
    t1 = 3
    phase1, time1 = create_phase(
        "Launchpad", 0, t1,
        acc_func=lambda t: np.zeros_like(t),
        vel_func=lambda t: np.zeros_like(t),
        h_func=lambda t: np.zeros_like(t),
        lat_func=lambda t: np.full_like(t, LAT0),
        lon_func=lambda t: np.full_like(t, LON0),
        pos_func=lambda t: np.full_like(t, POS0),
        bat_func=lambda t: np.full_like(t, BATT0),
        event_val=0
    )

    t2 = 3
    deg_m = deg_per_meter()
    phase2, time2 = create_phase(
        "Powered Ascent", t1, t1 + t2,
        acc_func=lambda t: np.full_like(t, A - G),
        vel_func=lambda t: (A - G) * t,
        h_func=lambda t: 0.5 * (A - G) * t ** 2,
        lat_func=lambda t: LAT0 - WIND / np.sqrt(2) * deg_m * t,
        lon_func=lambda t: LON0 + WIND / np.sqrt(2) * deg_m * t,
        pos_func=lambda t: POS0 + WIND * t,
        bat_func=lambda t: battery_drain(BATT0, t),
        event_val=1
    )

    t3 = t2 * (A - G) / G
    v_end = phase2.vel[-1]
    h_end = phase2.height[-1]
    lat_end = phase2.lat[-1]
    lon_end = phase2.lon[-1]
    pos_end = phase2.pos[-1]
    bat_end = phase2.bat[-1]

    phase3, time3 = create_phase(
        "Coasting", t1 + t2, t1 + t2 + t3,
        acc_func=lambda t: np.full_like(t, -G),
        vel_func=lambda t: v_end - G * t,
        h_func=lambda t: h_end + v_end * t - 0.5 * G * t ** 2,
        lat_func=lambda t: lat_end - WIND / np.sqrt(2) * deg_m * t,
        lon_func=lambda t: lon_end + WIND / np.sqrt(2) * deg_m * t,
        pos_func=lambda t: pos_end + WIND * t,
        bat_func=lambda t: battery_drain(bat_end, t),
        event_val=2
    )

    t4 = phase3.height[-1] / V_DESCENT
    h_max = phase3.height[-1]
    lat_max = phase3.lat[-1]
    lon_max = phase3.lon[-1]
    pos_max = phase3.pos[-1]
    bat_max = phase3.bat[-1]

    phase4, time4 = create_phase(
        "Descent", t1 + t2 + t3, t1 + t2 + t3 + t4,
        acc_func=lambda t: np.zeros_like(t),
        vel_func=lambda t: np.full_like(t, -V_DESCENT),
        h_func=lambda t: h_max - V_DESCENT * t,
        lat_func=lambda t: lat_max - WIND / np.sqrt(2) * deg_m * t,
        lon_func=lambda t: lon_max + WIND / np.sqrt(2) * deg_m * t,
        pos_func=lambda t: pos_max + WIND * t,
        bat_func=lambda t: battery_drain(bat_max, t),
        event_val=3
    )
    phase4.event[int(len(phase4.event) / 2):] = 4  # main parachute

    t5 = 3
    phase5, time5 = create_phase(
        "Landing", t1 + t2 + t3 + t4, t1 + t2 + t3 + t4 + t5,
        acc_func=lambda t: np.zeros_like(t),
        vel_func=lambda t: np.zeros_like(t),
        h_func=lambda t: np.zeros_like(t),
        lat_func=lambda t: np.full_like(t, phase4.lat[-1]),
        lon_func=lambda t: np.full_like(t, phase4.lon[-1]),
        pos_func=lambda t: np.full_like(t, phase4.pos[-1]),
        bat_func=lambda t: battery_drain(phase4.bat[-1], t),
        event_val=5
    )

    phases = [phase1, phase2, phase3, phase4, phase5]
    time = np.concatenate([np.arange(p.t_start, p.t_start + p.duration, DT) for p in phases])
    acc = np.concatenate([p.acc for p in phases])
    vel = np.concatenate([p.vel for p in phases])
    height = np.concatenate([p.height for p in phases])
    lat = np.concatenate([p.lat for p in phases])
    lon = np.concatenate([p.lon for p in phases])
    pos = np.concatenate([p.pos for p in phases])
    bat = np.concatenate([p.bat for p in phases])
    event = np.concatenate([p.event for p in phases])

    return {
        "time": time, "acc": acc, "vel": vel, "height": height,
        "lat": lat, "lon": lon, "pos": pos, "bat": bat, "event": event
    }


# ---------------------------------------------
# CSV IO functions
# ---------------------------------------------
def make_csv_filename(prefix="flight_data"):
    """Generate a timestamped CSV filename like 'flight_data_2025-10-19_14-32-10.csv'."""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.csv"


def init_csv(file_path):
    """Create CSV with header."""
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp_ms", "time", "acc", "vel", "height",
            "lat", "lon", "pos", "bat", "event"
        ])


def write_simulation_to_csv(sim_data, file_path=None):
    """Write full simulation arrays to a new timestamped CSV."""
    if file_path is None:
        file_path = make_csv_filename()
    init_csv(file_path)

    timestamp_ms = int(time.time() * 1000)
    rows = zip(
        np.full_like(sim_data["time"], timestamp_ms, dtype=np.int64),
        sim_data["time"], sim_data["acc"], sim_data["vel"], sim_data["height"],
        sim_data["lat"], sim_data["lon"], sim_data["pos"], sim_data["bat"], sim_data["event"]
    )

    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Simulation saved to: {os.path.abspath(file_path)}")
    return file_path


def read_simulation_from_csv(file_path=None):
    """Read simulation CSV back into numpy arrays."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        data = {k: [] for k in reader.fieldnames}
        for row in reader:
            for k, v in row.items():
                data[k].append(float(v))
    for k in data:
        data[k] = np.array(data[k])
    return data


# ---------------------------------------------
# Plot
# ---------------------------------------------
def plot_simulation_data(sim_data, title="Flight Simulation"):
    """Plot the main parameters from the simulation data."""

    # Extract data
    time = sim_data["time"]
    acc = sim_data["acc"]
    vel = sim_data["vel"]
    height = sim_data["height"]
    lat = sim_data["lat"]
    lon = sim_data["lon"]
    pos = sim_data["pos"]
    bat = sim_data["bat"]
    event = sim_data["event"]

    # Derived
    height_gnss = height * 1.1

    # Create figure
    fig, axs = plt.subplots(4, 2, figsize=(8, 10), dpi=200)
    axs01b = axs[0, 1].twinx()
    axs31b = axs[3, 1].twinx()

    # --- Left column ---
    axs[0, 0].plot(time, acc, c='k', lw=0.8)
    axs[1, 0].plot(time, vel, c='k', lw=0.8)
    axs[2, 0].plot(time, height, c='k', lw=0.8)
    axs[3, 0].plot(time, bat, c='k', lw=0.8)

    # --- Right column ---
    axs[0, 1].plot(time, lat, c='k', lw=0.8)
    axs01b.plot(time, lon, c='r', lw=0.6)
    axs[1, 1].plot(time, pos, c='k', lw=0.8)
    axs[2, 1].plot(time, height_gnss, c='k', lw=0.8)
    axs[3, 1].plot(time, event, c='k', lw=0.8)

    # --- Formatting ---
    for ax_row in axs:
        for ax in ax_row:
            ax.set_xlim(0, np.max(time))
            ax.grid(True, linestyle='--', alpha=0.3)

    # Event names
    axs31b.set_yticks([0, 1, 2, 3, 4, 5])
    axs31b.set_yticklabels(['Standby', 'Launch', 'Coast', 'Drogue', 'Main', 'Landing'])
    axs31b.set_ylim(axs[3, 1].get_ylim())

    # Labels
    axs[0, 0].set_ylabel("Acceleration (m/s²)")
    axs[1, 0].set_ylabel("Velocity (m/s)")
    axs[2, 0].set_ylabel("Height (m)")
    axs[3, 0].set_ylabel("Battery (V)")

    axs[0, 1].set_ylabel("Latitude (°)")
    axs01b.set_ylabel("Longitude (°)")
    axs[1, 1].set_ylabel("Displacement (m)")
    axs[2, 1].set_ylabel("GNSS Height (m)")
    axs[3, 1].set_ylabel("Event")

    for ax_row in axs:
        for ax in ax_row:
            ax.set_xlabel("Time (s)")

    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    sim = simulate()
    plot_simulation_data(sim)
    file_name = make_csv_filename()
    csv_file = write_simulation_to_csv(sim, f"flight_data/{make_csv_filename()}")
    plot_simulation_data(sim, title=os.path.basename(csv_file))

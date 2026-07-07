"""
topics.py
---------
Canonical bus topic names, in one place so producers and subscribers cannot
drift apart on a typo.

``tele/<field>`` mirrors the exact field names the telemetry decoder emits (see
``TelemetryReceiver.FIELDS``); the payload is a :class:`~ui.core.bus.Sample`.
Derived and control topics carry small purpose-specific payloads documented
below.
"""

# Raw telemetry (payload: Sample) — <field> is one of TelemetryReceiver.FIELDS.
def tele(field: str) -> str:
    """Topic for a raw telemetry field, e.g. ``tele("battery_voltage")``."""
    return f"tele/{field}"


# Full decoded packet dict (payload: dict) — for table/monitor widgets.
PACKET_RAW = "packet/raw"

# Derived: fires only when both lat & lon are present (payload: (lat, lon)).
GPS_FIX = "gps/fix"

# Derived: flight-mode edge (payload: bool armed) — published only on a change.
FLIGHT_ARMED = "flight/armed"

# Plot control (payload: None) — fanned to every coordinated plot instance.
PLOT_STOP = "plot/stop"
PLOT_RESUME = "plot/resume"
# PLOT_RESET clears the plots AND rebases the mission clock (the user's Reset
# button). PLOT_CLEAR only clears the plots — used on arm, where the clock has
# already been reset synchronously, so the clock must NOT be rebased a second
# time (which would shift the time origin mid-flight).
PLOT_RESET = "plot/reset"
PLOT_CLEAR = "plot/clear"

# Serial link status (payload: dict {connected: bool, port: str, message: str}).
SERIAL_STATUS = "serial/status"


def settings_changed(section: str) -> str:
    """Topic for a saved settings section, e.g. ``settings_changed("battery")``."""
    return f"settings/{section}/changed"

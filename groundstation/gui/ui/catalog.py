"""
catalog.py
----------
Builds the widget registry for the dashboard: the single place that knows every
placeable widget type. Adding a new widget = import it here and list it.

Kept separate from :mod:`ui.core.registry` (which is the generic mechanism) so
the mechanism has no dependency on the concrete widgets.
"""

from ui.core.registry import WidgetRegistry
from ui.windows.acceleration_window import AccelerationWindow
from ui.windows.altitude_window import AltitudeWindow
from ui.windows.battery_window import BatteryWindow
from ui.windows.commands_window import CommandsWindow
from ui.windows.connection_window import ConnectionWindow
from ui.windows.flight_events_window import FlightEventWindow
from ui.windows.last_packet_window import LastPacketWindow
from ui.windows.location_window import LocationWindow
from ui.windows.map_view_window import MapViewWindow
from ui.windows.serial_control_window import SerialControlWindow
from ui.windows.subsystem_window import SubsystemWindow
from ui.windows.time_window import TimeWindow

# Every placeable widget type. (The raw COM-monitor table is not yet migrated.)
WIDGET_TYPES = [
    SerialControlWindow,
    CommandsWindow,
    LastPacketWindow,
    FlightEventWindow,
    BatteryWindow,
    ConnectionWindow,
    SubsystemWindow,
    AltitudeWindow,
    AccelerationWindow,
    MapViewWindow,
    TimeWindow,
    LocationWindow,
]


def build_registry() -> WidgetRegistry:
    """Return a registry populated with every known widget type."""
    reg = WidgetRegistry()
    for cls in WIDGET_TYPES:
        reg.register(cls)
    return reg

"""
Headless construction smoke test for the migrated widgets.

Creates a real DearPyGui context (no viewport shown), then mounts, drives via the
bus, and destroys each widget — proving the mount/build/destroy lifecycle, that
two instances coexist without tag collisions, and that destroy() unsubscribes.
"""

import unittest

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.bus import Sample, TelemetryBus
from ui.core.mission_clock import MissionClock
from ui.core.services import ServiceHub
from ui.settings_manager import settings
from ui.windows.acceleration_window import AccelerationWindow
from ui.windows.altitude_window import AltitudeWindow
from ui.windows.battery_window import BatteryWindow
from ui.windows.connection_window import ConnectionWindow
from ui.windows.last_packet_window import LastPacketWindow
from ui.windows.location_window import LocationWindow
from ui.windows.subsystem_window import SubsystemWindow
from ui.windows.time_window import TimeWindow

WIDGET_CLASSES = [
    BatteryWindow, ConnectionWindow, SubsystemWindow, LastPacketWindow,
    LocationWindow, TimeWindow, AltitudeWindow, AccelerationWindow,
]


class TestWidgetSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dpg.create_context()

    @classmethod
    def tearDownClass(cls):
        dpg.destroy_context()

    def setUp(self):
        self.bus = TelemetryBus()
        self.ctx = ServiceHub(bus=self.bus, settings=settings, clock=MissionClock())
        self.win = dpg.add_window()
        self.canvas = dpg.add_child_window(parent=self.win)

    def tearDown(self):
        if dpg.does_item_exist(self.win):
            dpg.delete_item(self.win)

    def test_each_widget_mounts_and_destroys(self):
        for cls in WIDGET_CLASSES:
            w = cls("main", self.ctx, {})
            w.mount(self.canvas, 0, 0, 400, 300)
            self.assertTrue(dpg.does_item_exist(w._root), f"{cls.TYPE_ID}: root missing after mount")
            w.destroy()
            self.assertFalse(dpg.does_item_exist(w._root), f"{cls.TYPE_ID}: root not deleted on destroy")

    def test_two_batteries_coexist_without_collision(self):
        a = BatteryWindow("a", self.ctx, {})
        b = BatteryWindow("b", self.ctx, {})
        a.mount(self.canvas, 0, 0, 300, 200)
        b.mount(self.canvas, 0, 210, 300, 200)
        self.assertNotEqual(a.tag("bar"), b.tag("bar"))
        self.assertTrue(dpg.does_item_exist(a.tag("bar")))
        self.assertTrue(dpg.does_item_exist(b.tag("bar")))
        a.destroy()
        b.destroy()

    def test_two_altitude_plots_keep_independent_series(self):
        a = AltitudeWindow("a", self.ctx, {})
        b = AltitudeWindow("b", self.ctx, {})
        a.mount(self.canvas, 0, 0, 500, 400)
        b.mount(self.canvas, 0, 410, 500, 400)
        # feed only 'a'
        a._update("pressure", Sample(100.0, 0, 1.0))
        self.assertEqual(a.alt_pressure, [100.0])
        self.assertEqual(b.alt_pressure, [], "second plot must not share the first's data")
        a.destroy()
        b.destroy()

    def test_battery_reacts_to_bus_value(self):
        w = BatteryWindow("main", self.ctx, {})
        w.mount(self.canvas, 0, 0, 300, 200)
        self.bus.publish(topics.tele("battery_voltage"), Sample(6.0, 0, 0))
        self.bus.pump()
        self.assertEqual(dpg.get_value(w.tag("label")), "6.00 V")
        w.destroy()

    def test_last_packet_formats_from_raw(self):
        w = LastPacketWindow("main", self.ctx, {})
        w.mount(self.canvas, 0, 0, 300, 400)
        self.bus.publish(topics.PACKET_RAW, {"temperature": 21.4, "flight_mode": 1, "subsystem_status": 5})
        self.bus.pump()
        self.assertEqual(dpg.get_value(w.tag("temperature")), "21.4 °C")
        self.assertEqual(dpg.get_value(w.tag("flight_mode")), "ON")
        self.assertEqual(dpg.get_value(w.tag("subsystem")), "101")
        w.destroy()

    def test_destroy_unsubscribes_from_bus(self):
        w = BatteryWindow("main", self.ctx, {})
        w.mount(self.canvas, 0, 0, 300, 200)
        self.assertEqual(self.bus.subscriber_count(topics.tele("battery_voltage")), 1)
        w.destroy()
        self.assertEqual(self.bus.subscriber_count(topics.tele("battery_voltage")), 0)

    def test_plot_stop_resume_reset_via_bus(self):
        w = AccelerationWindow("main", self.ctx, {})
        w.mount(self.canvas, 0, 0, 500, 400)
        self.bus.publish(topics.PLOT_STOP, None)
        self.bus.pump()
        self.assertFalse(w.active)
        w._on_accel(Sample(2.0, 0, 1.0))  # frozen: dropped
        self.assertEqual(w.accel_data, [])
        self.bus.publish(topics.PLOT_RESUME, None)
        self.bus.pump()
        self.assertTrue(w.active)
        w._on_accel(Sample(2.0, 0, 1.0))
        self.assertEqual(w.accel_data, [2.0])
        self.bus.publish(topics.PLOT_RESET, None)
        self.bus.pump()
        self.assertEqual(w.accel_data, [])
        w.destroy()


if __name__ == "__main__":
    unittest.main()

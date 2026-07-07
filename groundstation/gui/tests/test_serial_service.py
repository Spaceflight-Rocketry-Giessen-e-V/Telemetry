"""Unit tests for SerialService packet→bus derivation (no serial hardware)."""

import unittest

from ui.core import topics
from ui.core.bus import Sample, TelemetryBus
from ui.core.mission_clock import MissionClock
from ui.core.serial_service import SerialService


class FakeTime:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _packet(**over):
    base = {
        "timestamp": "t",
        "temperature": 20,
        "flight_mode": 0,
        "acceleration": 1.5,
        "height_pressure": 100.0,
        "battery_voltage": 7.4,
        "lat_gnss": 50.5,
        "lon_gnss": 8.7,
    }
    base.update(over)
    return base


class TestSerialService(unittest.TestCase):
    def setUp(self):
        self.bus = TelemetryBus()
        self.time = FakeTime()
        self.clock = MissionClock(time_fn=self.time)
        self.svc = SerialService(self.bus, self.clock)
        self.received = {}

    def _capture(self, *topic_names):
        for t in topic_names:
            self.received.setdefault(t, [])
            self.bus.subscribe(t, (lambda tt: (lambda p: self.received[tt].append(p)))(t))

    def test_fields_published_as_samples_with_mission_time(self):
        self._capture(topics.tele("temperature"), topics.tele("battery_voltage"))
        self.time.now = 1005.0  # 5 s into the mission
        self.svc._on_packet(_packet())
        self.bus.pump()
        temp = self.received[topics.tele("temperature")][0]
        self.assertIsInstance(temp, Sample)
        self.assertEqual(temp.value, 20)
        self.assertAlmostEqual(temp.mission_t, 5.0)

    def test_timestamp_field_is_not_fanned_out(self):
        self._capture(topics.tele("timestamp"))
        self.svc._on_packet(_packet())
        self.bus.pump()
        self.assertEqual(self.received[topics.tele("timestamp")], [])

    def test_gps_fix_only_when_both_present(self):
        self._capture(topics.GPS_FIX)
        self.svc._on_packet(_packet(lat_gnss=None, lon_gnss=None))
        self.bus.pump()
        self.assertEqual(self.received[topics.GPS_FIX], [])
        self.svc._on_packet(_packet(lat_gnss=1.0, lon_gnss=2.0))
        self.bus.pump()
        self.assertEqual(self.received[topics.GPS_FIX], [(1.0, 2.0)])

    def test_flight_armed_only_on_edges(self):
        self._capture(topics.FLIGHT_ARMED)
        self.svc._on_packet(_packet(flight_mode=0))  # no edge
        self.svc._on_packet(_packet(flight_mode=1))  # arm edge -> True
        self.svc._on_packet(_packet(flight_mode=1))  # no edge
        self.svc._on_packet(_packet(flight_mode=0))  # disarm edge -> False
        self.bus.pump()
        self.assertEqual(self.received[topics.FLIGHT_ARMED], [True, False])

    def test_arm_resets_mission_clock_and_publishes_plot_reset(self):
        self._capture(topics.PLOT_RESET)
        self.time.now = 1010.0
        self.svc._on_packet(_packet(flight_mode=1))  # arm at t=1010
        self.bus.pump()
        self.assertEqual(len(self.received[topics.PLOT_RESET]), 1)
        # clock rebased at arm, so elapsed is ~0 right after
        self.assertAlmostEqual(self.clock.elapsed(), 0.0)

    def test_user_plot_reset_rebases_clock(self):
        self.time.now = 1000.0
        self.svc  # constructed; subscribed to PLOT_RESET
        self.time.now = 1050.0
        self.bus.publish(topics.PLOT_RESET, None)
        self.bus.pump()
        self.assertAlmostEqual(self.clock.elapsed(), 0.0)


if __name__ == "__main__":
    unittest.main()

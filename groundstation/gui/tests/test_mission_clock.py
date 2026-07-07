"""Unit tests for the mission clock (using a fake time source)."""

import unittest

from ui.core.mission_clock import MissionClock


class FakeTime:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class TestMissionClock(unittest.TestCase):
    def test_elapsed_advances_with_time(self):
        t = FakeTime()
        clock = MissionClock(time_fn=t)
        self.assertEqual(clock.elapsed(), 0.0)
        t.now = 105.5
        self.assertAlmostEqual(clock.elapsed(), 5.5)

    def test_reset_rebases_to_now(self):
        t = FakeTime()
        clock = MissionClock(time_fn=t)
        t.now = 130.0
        clock.reset()
        self.assertEqual(clock.elapsed(), 0.0)
        t.now = 132.0
        self.assertAlmostEqual(clock.elapsed(), 2.0)


if __name__ == "__main__":
    unittest.main()

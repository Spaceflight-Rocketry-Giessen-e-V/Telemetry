"""Unit tests for the telemetry bus (pub/sub + framed delivery)."""

import threading
import unittest

from ui.core.bus import Sample, TelemetryBus


class TestTelemetryBus(unittest.TestCase):
    def setUp(self):
        self.bus = TelemetryBus()

    def test_publish_is_deferred_until_pump(self):
        got = []
        self.bus.subscribe("t", got.append)
        self.bus.publish("t", 1)
        self.assertEqual(got, [], "callback must not run before pump")
        n = self.bus.pump()
        self.assertEqual(got, [1])
        self.assertEqual(n, 1)

    def test_multiple_subscribers_all_receive(self):
        a, b = [], []
        self.bus.subscribe("t", a.append)
        self.bus.subscribe("t", b.append)
        self.bus.publish("t", "x")
        self.bus.pump()
        self.assertEqual((a, b), (["x"], ["x"]))

    def test_unsubscribe_stops_delivery(self):
        got = []
        tok = self.bus.subscribe("t", got.append)
        self.bus.unsubscribe(tok)
        self.bus.publish("t", 1)
        self.bus.pump()
        self.assertEqual(got, [])
        self.assertEqual(self.bus.subscriber_count("t"), 0)

    def test_unsubscribe_unknown_token_is_safe(self):
        self.bus.unsubscribe(9999)  # must not raise

    def test_topics_are_isolated(self):
        got = []
        self.bus.subscribe("a", got.append)
        self.bus.publish("b", 1)
        self.bus.pump()
        self.assertEqual(got, [])

    def test_subscriber_exception_does_not_break_siblings(self):
        good = []

        def boom(_):
            raise RuntimeError("bad handler")

        self.bus.subscribe("t", boom)
        self.bus.subscribe("t", good.append)
        self.bus.publish("t", 42)
        self.bus.pump()  # must not raise
        self.assertEqual(good, [42])

    def test_callback_publish_is_deferred_to_next_pump(self):
        seen = []

        def relay(v):
            seen.append(v)
            if v == 1:
                self.bus.publish("t", 2)  # published during pump

        self.bus.subscribe("t", relay)
        self.bus.publish("t", 1)
        first = self.bus.pump()
        self.assertEqual((seen, first), ([1], 1), "re-publish must not be delivered same pump")
        self.bus.pump()
        self.assertEqual(seen, [1, 2])

    def test_cross_thread_publish_delivered_on_pump_thread(self):
        thread_ids = []
        main_id = threading.get_ident()
        self.bus.subscribe("t", lambda _: thread_ids.append(threading.get_ident()))

        t = threading.Thread(target=lambda: self.bus.publish("t", 1))
        t.start()
        t.join()
        self.bus.pump()  # runs on the main thread
        self.assertEqual(thread_ids, [main_id])

    def test_sample_factory_sets_mission_t(self):
        s = self.bus.sample(3.14, mission_t=12.0)
        self.assertIsInstance(s, Sample)
        self.assertEqual((s.value, s.mission_t), (3.14, 12.0))


if __name__ == "__main__":
    unittest.main()

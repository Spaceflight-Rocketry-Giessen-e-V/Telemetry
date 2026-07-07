"""
Headless end-to-end test: load the real flight-default dashboard through the grid
engine and confirm every widget mounts, then tear it all down.
"""

import unittest

import dearpygui.dearpygui as dpg

from ui.catalog import build_registry
from ui.core.bus import TelemetryBus
from ui.core.mission_clock import MissionClock
from ui.core.serial_service import SerialService
from ui.core.services import ServiceHub
from ui.layout import layout_store
from ui.layout.grid_engine import GridLayoutEngine
from ui.settings_manager import settings


class TestDashboardSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dpg.create_context()

    @classmethod
    def tearDownClass(cls):
        dpg.destroy_context()

    def _make_engine(self):
        bus = TelemetryBus()
        clock = MissionClock()
        ctx = ServiceHub(bus=bus, settings=settings, clock=clock, serial=SerialService(bus, clock))
        return GridLayoutEngine(build_registry(), ctx)

    def test_flight_default_loads_all_widgets(self):
        doc = layout_store.load_dashboard(layout_store.dashboard_path("flight-default"))
        expected = len(doc["widgets"])
        self.assertGreater(expected, 0)

        engine = self._make_engine()
        win = dpg.add_window()
        try:
            engine.load(doc, parent=win, canvas_tag="test_canvas_1")
            self.assertEqual(len(engine.widgets), expected, "not every widget mounted")
            for w in engine.widgets:
                self.assertTrue(dpg.does_item_exist(w._root), f"{w.TYPE_ID}[{w.iid}] root missing")
            # No two placed widgets overlap in the shipped layout.
            from ui.layout import grid_math
            rects = [tuple(e["cell"]) for e in doc["widgets"]]
            self.assertEqual(grid_math.find_overlaps(rects), [], "shipped dashboard has overlaps")
        finally:
            engine.teardown_all()
            self.assertFalse(dpg.does_item_exist("test_canvas_1"))
            dpg.delete_item(win)

    def test_unknown_type_is_skipped_not_fatal(self):
        engine = self._make_engine()
        win = dpg.add_window()
        doc = {
            "schema": 1, "name": "x",
            "grid": {"cols": 12, "cell_h": 80, "gutter": 8, "margin": 12},
            "widgets": [
                {"type": "battery", "iid": "a", "cell": [0, 0, 3, 3], "config": {}},
                {"type": "does_not_exist", "iid": "b", "cell": [3, 0, 3, 3], "config": {}},
            ],
        }
        try:
            engine.load(doc, parent=win, canvas_tag="test_canvas_2")
            self.assertEqual(len(engine.widgets), 1, "unknown type should be skipped, known kept")
        finally:
            engine.teardown_all()
            dpg.delete_item(win)


if __name__ == "__main__":
    unittest.main()

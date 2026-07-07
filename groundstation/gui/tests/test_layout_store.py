"""Unit tests for dashboard load/save + validation."""

import os
import tempfile
import unittest

from ui.layout.layout_store import DashboardError, load_dashboard, save_dashboard, validate


def _good_doc():
    return {
        "schema": 1,
        "name": "t",
        "grid": {"cols": 12, "cell_h": 80, "gutter": 8, "margin": 12},
        "widgets": [
            {"type": "battery", "iid": "a", "cell": [0, 0, 3, 3], "config": {"title": "Main"}},
            {"type": "battery", "iid": "b", "cell": [3, 0, 3, 3]},
        ],
    }


class TestLayoutStore(unittest.TestCase):
    def test_validate_accepts_good_doc(self):
        doc = validate(_good_doc())
        # config defaulted for the second widget
        self.assertEqual(doc["widgets"][1]["config"], {})

    def test_reject_wrong_schema(self):
        d = _good_doc()
        d["schema"] = 99
        with self.assertRaises(DashboardError):
            validate(d)

    def test_reject_missing_grid(self):
        d = _good_doc()
        del d["grid"]
        with self.assertRaises(DashboardError):
            validate(d)

    def test_reject_bad_cell(self):
        d = _good_doc()
        d["widgets"][0]["cell"] = [0, 0, 3]  # too short
        with self.assertRaises(DashboardError):
            validate(d)

    def test_duplicate_type_iid_allowed_by_validate(self):
        # Duplicates are handled (skipped) by the engine, not rejected here, so
        # one bad entry never discards the whole dashboard.
        d = _good_doc()
        d["widgets"][1]["iid"] = "a"  # now two (battery, a)
        validate(d)  # must not raise

    def test_reject_unknown_grid_key(self):
        d = _good_doc()
        d["grid"]["row_gap"] = 4
        with self.assertRaises(DashboardError):
            validate(d)

    def test_reject_noninteger_grid_value(self):
        d = _good_doc()
        d["grid"]["cols"] = "12"
        with self.assertRaises(DashboardError):
            validate(d)

    def test_reject_zero_or_negative_span(self):
        for bad in ([0, 0, 0, 3], [0, 0, 3, 0], [0, 0, -1, 3]):
            d = _good_doc()
            d["widgets"][0]["cell"] = bad
            with self.assertRaises(DashboardError):
                validate(d)

    def test_reject_negative_position(self):
        d = _good_doc()
        d["widgets"][0]["cell"] = [-1, 0, 3, 3]
        with self.assertRaises(DashboardError):
            validate(d)

    def test_reject_missing_type(self):
        d = _good_doc()
        del d["widgets"][0]["type"]
        with self.assertRaises(DashboardError):
            validate(d)

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "d.json")
            save_dashboard(path, _good_doc())
            back = load_dashboard(path)
            self.assertEqual(back["name"], "t")
            self.assertEqual(len(back["widgets"]), 2)


if __name__ == "__main__":
    unittest.main()

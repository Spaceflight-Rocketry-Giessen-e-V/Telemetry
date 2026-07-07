"""Unit tests for the widget registry (no DPG context needed to construct)."""

import unittest

from ui.core.registry import WidgetRegistry
from ui.core.widget_base import Widget


class FakeWidget(Widget):
    TYPE_ID = "fake"
    DISPLAY_NAME = "Fake"
    DEFAULT_CELLS = (2, 2)

    def build(self, width, height):  # pragma: no cover - not exercised here
        pass


class OtherWidget(Widget):
    TYPE_ID = "other"
    DISPLAY_NAME = "Other"
    SINGLETON = True

    def build(self, width, height):  # pragma: no cover
        pass


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = WidgetRegistry()
        self.reg.register(FakeWidget)
        self.reg.register(OtherWidget)

    def test_is_registered(self):
        self.assertTrue(self.reg.is_registered("fake"))
        self.assertFalse(self.reg.is_registered("nope"))

    def test_create_builds_instance_with_iid_and_config(self):
        w = self.reg.create("fake", "abc", ctx=None, config={"k": 1})
        self.assertIsInstance(w, FakeWidget)
        self.assertEqual(w.iid, "abc")
        self.assertEqual(w.config, {"k": 1})
        # tag namespacing is per-instance
        self.assertEqual(w.tag("bar"), "fake__abc__bar")

    def test_two_instances_have_distinct_tags(self):
        w1 = self.reg.create("fake", "one", ctx=None)
        w2 = self.reg.create("fake", "two", ctx=None)
        self.assertNotEqual(w1.tag("bar"), w2.tag("bar"))
        self.assertEqual(w1._root, "fake__one__root")

    def test_create_unknown_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.reg.create("ghost", "x", ctx=None)

    def test_register_without_type_id_raises(self):
        class NoId(Widget):
            def build(self, width, height):
                pass

        with self.assertRaises(ValueError):
            self.reg.register(NoId)

    def test_meta_lists_types(self):
        meta = {m["type_id"]: m for m in self.reg.meta()}
        self.assertEqual(meta["fake"]["default_cells"], (2, 2))
        self.assertTrue(meta["other"]["singleton"])


if __name__ == "__main__":
    unittest.main()

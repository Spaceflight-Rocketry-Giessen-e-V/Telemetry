"""Unit tests for pure grid geometry."""

import unittest

from ui.layout.grid_math import (
    GridSpec,
    canvas_height,
    cell_to_px,
    cell_w,
    find_overlaps,
    overlaps,
    total_rows,
)


class TestGridMath(unittest.TestCase):
    def test_cell_w_formula(self):
        spec = GridSpec(cols=12, gutter=8, margin=12)
        # usable = 1000 - 24 - 11*8 = 888; /12 = 74.0
        self.assertAlmostEqual(cell_w(spec, 1000), 74.0)

    def test_cell_w_floor_on_tiny_viewport(self):
        self.assertEqual(cell_w(GridSpec(), 5), 1.0)

    def test_cell_to_px_top_left_single_cell(self):
        spec = GridSpec(cols=12, cell_h=80, gutter=8, margin=12)
        x, y, w, h = cell_to_px(spec, (0, 0, 1, 1), 1000)
        self.assertEqual((x, y), (12, 12))
        self.assertEqual((w, h), (74, 80))

    def test_cell_to_px_span_and_offset(self):
        spec = GridSpec(cols=12, cell_h=80, gutter=8, margin=12)
        # cell_w=74. col=2 -> x = 12 + 2*(74+8) = 176. colspan=3 -> w = 3*74 + 2*8 = 238.
        # row=1 -> y = 12 + 1*(80+8) = 100. rowspan=2 -> h = 2*80 + 1*8 = 168.
        self.assertEqual(cell_to_px(spec, (2, 1, 3, 2), 1000), (176, 100, 238, 168))

    def test_total_rows_and_canvas_height(self):
        rects = [(0, 0, 6, 5), (6, 0, 3, 3), (0, 5, 6, 8)]
        self.assertEqual(total_rows(rects), 13)  # 5 + 8
        spec = GridSpec(cell_h=80, gutter=8, margin=12)
        # 24 + 13*80 + 12*8 = 24 + 1040 + 96 = 1160
        self.assertEqual(canvas_height(spec, rects), 1160)

    def test_total_rows_empty(self):
        self.assertEqual(total_rows([]), 0)
        self.assertEqual(canvas_height(GridSpec(margin=12), []), 24)

    def test_overlaps_true_when_sharing_cells(self):
        self.assertTrue(overlaps((0, 0, 2, 2), (1, 1, 2, 2)))

    def test_overlaps_false_when_adjacent(self):
        self.assertFalse(overlaps((0, 0, 2, 2), (2, 0, 2, 2)))  # side by side
        self.assertFalse(overlaps((0, 0, 2, 2), (0, 2, 2, 2)))  # stacked

    def test_find_overlaps_reports_pairs(self):
        rects = [(0, 0, 6, 5), (6, 0, 3, 3), (5, 4, 3, 3)]  # 0 and 2 overlap
        self.assertEqual(find_overlaps(rects), [(0, 2)])

    def test_find_overlaps_clean_layout(self):
        rects = [(0, 0, 6, 5), (6, 0, 6, 5), (0, 5, 12, 3)]
        self.assertEqual(find_overlaps(rects), [])

    def test_invalid_spec_rejected(self):
        with self.assertRaises(ValueError):
            GridSpec(cols=0)
        with self.assertRaises(ValueError):
            GridSpec(cell_h=0)


if __name__ == "__main__":
    unittest.main()

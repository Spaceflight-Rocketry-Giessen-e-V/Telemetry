"""
grid_math.py
------------
Pure grid geometry — no DearPyGui, no side effects, fully unit-testable.

A dashboard is an ``N``-column grid with a fixed pixel row height. Widgets are
placed at ``(col, row)`` and span ``(colspan, rowspan)`` cells. Column width is
*fluid*: it is derived from the live viewport width so the layout reflows when
the window resizes (fixing the old hardcoded 1920×1080 assumption). Row height
is fixed, so tall widgets (e.g. the map) span several rows.

All coordinates are in whole grid cells; :func:`cell_to_px` converts a cell rect
to a pixel rect ``(x, y, w, h)`` relative to the grid canvas origin.
"""

from dataclasses import dataclass

# A placed cell rect: (col, row, colspan, rowspan).
CellRect = tuple[int, int, int, int]


@dataclass(frozen=True)
class GridSpec:
    """Immutable grid geometry parameters."""

    cols: int = 12
    cell_h: int = 80      # fixed pixel height of one grid row
    gutter: int = 8       # pixel gap between cells
    margin: int = 12      # pixel margin around the whole grid

    def __post_init__(self) -> None:
        if self.cols < 1:
            raise ValueError("GridSpec.cols must be >= 1")
        if self.cell_h < 1:
            raise ValueError("GridSpec.cell_h must be >= 1")


def cell_w(spec: GridSpec, viewport_w: float) -> float:
    """
    Fluid column width for the given viewport width.

    ``viewport_w`` is the usable canvas width in pixels. Width is distributed
    across ``cols`` columns after removing the outer margins and inter-column
    gutters. Clamped to a small positive floor so a tiny viewport never yields a
    zero/negative width.
    """
    usable = viewport_w - 2 * spec.margin - (spec.cols - 1) * spec.gutter
    return max(1.0, usable / spec.cols)


def cell_to_px(spec: GridSpec, rect: CellRect, viewport_w: float) -> tuple[int, int, int, int]:
    """
    Convert a cell rect ``(col, row, colspan, rowspan)`` to a pixel rect
    ``(x, y, w, h)`` relative to the canvas origin.
    """
    col, row, colspan, rowspan = rect
    cw = cell_w(spec, viewport_w)
    x = spec.margin + col * (cw + spec.gutter)
    y = spec.margin + row * (spec.cell_h + spec.gutter)
    w = colspan * cw + (colspan - 1) * spec.gutter
    h = rowspan * spec.cell_h + (rowspan - 1) * spec.gutter
    return (round(x), round(y), round(w), round(h))


def total_rows(rects: list[CellRect]) -> int:
    """Highest occupied row + span — used to size the scrollable canvas height."""
    return max((row + rowspan for _, row, _, rowspan in rects), default=0)


def canvas_height(spec: GridSpec, rects: list[CellRect]) -> int:
    """Virtual pixel height needed to contain every placed widget."""
    rows = total_rows(rects)
    if rows == 0:
        return 2 * spec.margin
    return spec.margin * 2 + rows * spec.cell_h + (rows - 1) * spec.gutter


def overlaps(a: CellRect, b: CellRect) -> bool:
    """True if two cell rects share any cell (both half-open in col/row)."""
    ac, ar, acs, ars = a
    bc, br, bcs, brs = b
    sep_x = ac + acs <= bc or bc + bcs <= ac
    sep_y = ar + ars <= br or br + brs <= ar
    return not (sep_x or sep_y)


def find_overlaps(rects: list[CellRect]) -> list[tuple[int, int]]:
    """Return index pairs of overlapping rects (for validating a dashboard)."""
    clashes: list[tuple[int, int]] = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            if overlaps(rects[i], rects[j]):
                clashes.append((i, j))
    return clashes

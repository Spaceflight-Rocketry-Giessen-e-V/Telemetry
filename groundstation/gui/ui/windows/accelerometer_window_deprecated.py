"""
accelerometer_window_deprecated.py
------------------------------------
Deprecated arrow-based accelerometer visualiser.

Replaced by AccelerationWindow (acceleration_window.py). Kept for reference
only; do not use in new code.
"""

import math

import dearpygui.dearpygui as dpg


class AccelerometerWindow:
    # Maximum g value at which the color gradient reaches full purple.
    max_g = 8.0
    # Pixels per g, clamped by max_length.
    scale_factor = 15.0
    max_length = 80

    window_tag = "accel_window"
    draw_tag = "accel_draw"
    arrow_tag = "accel_arrow"
    value_label_tag = "accel_value_label"

    _center = (120, 120)
    _radius = 100
    _draw_width = 240
    _draw_height = 240

    @staticmethod
    def lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def lerp_color(c1, c2, t):
        return (
            int(AccelerometerWindow.lerp(c1[0], c2[0], t)),
            int(AccelerometerWindow.lerp(c1[1], c2[1], t)),
            int(AccelerometerWindow.lerp(c1[2], c2[2], t)),
        )

    @classmethod
    def smooth_color(cls, g):
        """Return an RGB color along the green → yellow → red → purple gradient."""
        t = min(abs(g) / cls.max_g, 1.0)
        green = (0, 255, 0)
        yellow = (255, 255, 0)
        red = (255, 0, 0)
        purple = (180, 0, 255)

        if t <= 0.33:
            return cls.lerp_color(green, yellow, t / 0.33)
        elif t <= 0.66:
            return cls.lerp_color(yellow, red, (t - 0.33) / 0.33)
        else:
            return cls.lerp_color(red, purple, (t - 0.66) / 0.34)

    @classmethod
    def draw_ui(cls, width=250, height=250):
        """
        Create the child window and drawlist.

        Saves centre and radius for use in subsequent :py:meth:`update_accel`
        calls. Space below the drawlist is reserved for the numeric label.
        """
        with dpg.child_window(label="Accelerometer", width=width, height=height, tag=cls.window_tag):
            dw = width - 10
            dh = height - 40
            cls._draw_width = dw
            cls._draw_height = dh
            cls._center = (dw // 2, dh // 2)
            cls._radius = min(dw, dh) // 2 - 12

            with dpg.drawlist(width=dw, height=dh, tag=cls.draw_tag):
                dpg.draw_circle(center=cls._center, radius=cls._radius, color=(180, 180, 180), thickness=2)

                # Scale ticks every 45°
                for deg in range(0, 360, 45):
                    a = math.radians(deg)
                    outer = (cls._center[0] + math.cos(a) * cls._radius,
                             cls._center[1] - math.sin(a) * cls._radius)
                    inner = (cls._center[0] + math.cos(a) * (cls._radius - 8),
                             cls._center[1] - math.sin(a) * (cls._radius - 8))
                    dpg.draw_line(p1=inner, p2=outer, thickness=2)

                # Cardinal direction labels
                label_offset = 18
                labels = {90: "Up", 0: "R", 270: "Down", 180: "L"}
                for deg, txt in labels.items():
                    a = math.radians(deg)
                    pos = (cls._center[0] + math.cos(a) * (cls._radius + label_offset) - 6,
                           cls._center[1] - math.sin(a) * (cls._radius + label_offset) - 6)
                    dpg.draw_text(pos=pos, text=txt, size=12)

                tail = cls._center
                head = (cls._center[0], cls._center[1] - cls._radius + 20)
                dpg.draw_arrow(p1=head, p2=tail, color=(0, 255, 0), thickness=3, size=15, tag=cls.arrow_tag)

            dpg.add_spacer(height=6)
            dpg.add_text(f"g: 0.00", tag=cls.value_label_tag)

    @classmethod
    def update_accel(cls, g_value, direction_deg=90):
        """
        Update the arrow length, direction, and colour.

        Parameters
        ----------
        g_value:
            Acceleration magnitude in g. Negative values flip the arrow direction.
        direction_deg:
            Arrow heading in degrees (0° = right, 90° = up).
        """
        color = cls.smooth_color(g_value)
        length = min(cls.max_length, abs(g_value) * cls.scale_factor)

        angle = math.radians(direction_deg)
        dx = math.cos(angle)
        dy = -math.sin(angle)
        sign = 1 if g_value >= 0 else -1

        head = (cls._center[0] + sign * dx * length, cls._center[1] + sign * dy * length)
        tail = cls._center

        dpg.configure_item(cls.arrow_tag, p1=head, p2=tail, color=color)
        dpg.set_value(cls.value_label_tag, f"g: {g_value:.2f}")

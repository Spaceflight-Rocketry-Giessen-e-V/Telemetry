import dearpygui.dearpygui as dpg
import math
import time


class AccelerometerWindow:
    # configuration
    max_g = 8.0  # g where color becomes full purple
    scale_factor = 15.0  # pixels per g (clamped by max_length)
    max_length = 80  # max arrow length in pixels

    # tags (class-level so other code can access)
    window_tag = "accel_window"
    draw_tag = "accel_draw"
    arrow_tag = "accel_arrow"
    value_label_tag = "accel_value_label"

    # stored geometry set during draw_ui
    _center = (120, 120)
    _radius = 100
    _draw_width = 240
    _draw_height = 240

    # -------------------------
    # Helpers
    # -------------------------
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
        """Smooth gradient: green -> yellow -> red -> purple"""
        t = min(abs(g) / cls.max_g, 1.0)  # use magnitude for color
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

    # -------------------------
    # UI Creation
    # -------------------------
    @classmethod
    def draw_ui(cls, width=250, height=250):
        """
        Create the child window and drawlist. Saves center/radius for updates.
        The drawlist area will be slightly inset to leave room for label.
        """
        with dpg.child_window(label="Accelerometer", width=width, height=height, tag=cls.window_tag):
            dw = width - 10
            dh = height - 40  # leave space for numeric label
            cls._draw_width = dw
            cls._draw_height = dh
            cls._center = (dw // 2, dh // 2)
            cls._radius = min(dw, dh) // 2 - 12

            with dpg.drawlist(width=dw, height=dh, tag=cls.draw_tag):
                # background circle
                dpg.draw_circle(center=cls._center, radius=cls._radius, color=(180, 180, 180), thickness=2)

                # scale ticks (every 45°) and small labels for cardinal directions
                for deg in range(0, 360, 45):
                    a = math.radians(deg)
                    outer = (cls._center[0] + math.cos(a) * (cls._radius),
                             cls._center[1] - math.sin(a) * (cls._radius))
                    inner = (cls._center[0] + math.cos(a) * (cls._radius - 8),
                             cls._center[1] - math.sin(a) * (cls._radius - 8))
                    dpg.draw_line(p1=inner, p2=outer, thickness=2)

                # small cardinal labels (Up, Right, Down, Left) - optional text near ticks
                # use tiny offset outward from outer tick
                label_offset = 18
                labels = {
                    90: "Up",
                    0: "R",
                    270: "Down",
                    180: "L"
                }
                for deg, txt in labels.items():
                    a = math.radians(deg)
                    pos = (cls._center[0] + math.cos(a) * (cls._radius + label_offset) - 6,
                           cls._center[1] - math.sin(a) * (cls._radius + label_offset) - 6)
                    # draw_text in drawlist uses draw_text
                    dpg.draw_text(pos=pos, text=txt, size=12)

                # initial arrow (pointing up by default when direction_deg = 90)
                tail = cls._center
                head = (cls._center[0], cls._center[1] - cls._radius + 20)
                dpg.draw_arrow(p1=tail, p2=head, color=(0, 255, 0), thickness=3, size=15, tag=cls.arrow_tag)

            # numeric g label under the drawlist
            dpg.add_spacer(height=6)
            dpg.add_text(f"g: 0.00", tag=cls.value_label_tag)

    # -------------------------
    # Update
    # -------------------------
    @classmethod
    def update_accel(cls, g_value, direction_deg=90):
        """
        Update arrow length, direction and color.
        - direction_deg uses same convention: 0° = right, 90° = up
        - negative g_value flips the arrow (points opposite direction)
        """
        # compute color based on magnitude
        color = cls.smooth_color(g_value)

        # length based on magnitude, clamp to max_length
        length = min(cls.max_length, abs(g_value) * cls.scale_factor)

        # direction (0°=right, 90°=up). angle in radians.
        angle = math.radians(direction_deg)

        # unit vector for the direction (dx, dy) where dy is screen-positive down, so subtract sin
        dx = math.cos(angle)
        dy = -math.sin(angle)

        # if negative g, invert direction (point opposite)
        sign = 1 if g_value >= 0 else -1

        head = (cls._center[0] + sign * dx * length, cls._center[1] + sign * dy * length)
        tail = cls._center

        # update arrow
        dpg.configure_item(cls.arrow_tag, p1=head, p2=tail, color=color)

        # update numeric label
        dpg.set_value(cls.value_label_tag, f"g: {g_value:.2f}")

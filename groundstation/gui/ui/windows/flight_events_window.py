import dearpygui.dearpygui as dpg

class FlightEventMonitor:
    events = [
        "Pad Idle",
        "Main Chute Altitude Set",
        "Armed",
        "Pyros Continuity Check",
        "Liftoff",
        "Booster Burnout",
        "Apogee detected",
        "Pyro 1 signal sent (drogue)",
        "Pyro2 signal sent (drogue)",
        "Drogue deployment detected",
        "Pyro3 signal sent (main)",
        "Pyro4 signal sent (main)",
        "Main deployment detected",
        "Landed",
        "ABORT - Failed to initialize",
        "ABORT - No Continuity"
    ]

    current_event = -1  # No event yet

    @classmethod
    def draw_ui(cls, window_width=400, window_height=400):
        with dpg.child_window(label="Flight Events", width=window_width, height=window_height):
            dpg.add_text("Flight Event Status")
            for i, event_name in enumerate(cls.events):
                # Add the text with a unique tag
                dpg.add_text(f"{i:02d} - {event_name}", tag=f"event_{i}", color=(200, 200, 200, 255))

    @classmethod
    def update_event(cls, event_number):
        cls.current_event = event_number
        for i in range(len(cls.events)):
            if i <= cls.current_event:
                # Completed events: green (or red if ABORT)
                color = (255, 0, 0, 255) if i >= 14 else (0, 255, 0, 255)
            else:
                color = (200, 200, 200, 255)  # Future events: grey
            # Update the color using configure_item
            dpg.configure_item(f"event_{i}", color=color)

"""
ui_manager.py
-------------
Bootstrap for the modular Ground Station GUI.

Responsibilities (deliberately small):
  - Configure logging (once, at import).
  - Create the DearPyGui context, font, viewport, and top-level tabs.
  - Wire up the service layer: telemetry bus, mission clock, serial service.
  - Hand the Flight-Data tab to the grid layout engine, which builds the widgets
    from a dashboard JSON document.
  - Run the manual render loop (draining the bus each frame) and shut down cleanly.

All the old per-window instantiation, the hardcoded 4-column layout, and the
``update_all`` telemetry dispatch table are gone: widgets are placed from
``dashboards/<name>.json`` and fed by the bus. The Settings editor remains a
plain (non-grid) tab.
"""

import logging
import logging.handlers
import os
import sys

import dearpygui.dearpygui as dpg

from ui.catalog import build_registry
from ui.core import topics
from ui.core.bus import TelemetryBus
from ui.core.mission_clock import MissionClock
from ui.core.pump import run_render_loop
from ui.core.serial_service import SerialService
from ui.core.services import ServiceHub
from ui.layout import layout_store
from ui.layout.grid_engine import GridLayoutEngine
from ui.settings_manager import settings
from ui.windows.settings_window import SettingsWindow


def _configure_logging(
        log_dir: str = "logs",
        log_file: str = "ground_station.log",
        max_bytes: int = 5 * 1024 * 1024,
        backups: int = 5,
        level: int = logging.DEBUG,
) -> None:
    """Configure the root logger: INFO to stdout, DEBUG to a rotating file."""
    os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Windows stdout defaults to a legacy code page that cannot encode the
    # arrows/dashes in log messages; make it UTF-8 and lenient.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=max_bytes,
        backupCount=backups,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    root.addHandler(console_handler)
    root.addHandler(file_handler)


_configure_logging()
log = logging.getLogger(__name__)


def get_screen_resolution() -> tuple[int, int]:
    """Return the primary monitor's resolution as ``(width, height)`` in pixels."""
    if sys.platform.startswith("win"):
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h


class UIManager:
    """Owns the service layer and drives the modular dashboard."""

    def __init__(self) -> None:
        log.info("UIManager: initialising services")
        self._shutdown_done = False

        self.bus = TelemetryBus()
        self.clock = MissionClock()
        self.serial = SerialService(self.bus, self.clock)
        self.ctx = ServiceHub(bus=self.bus, settings=settings, clock=self.clock, serial=self.serial)

        self.registry = build_registry()
        self.engine = GridLayoutEngine(self.registry, self.ctx)
        self.settings_window = SettingsWindow(on_saved=self._on_settings_saved)

        self._dashboard_name = settings.get("dashboard.current", "flight-default")
        log.info("UIManager: services ready (dashboard=%s)", self._dashboard_name)

    # -- settings → bus -------------------------------------------------------

    def _on_settings_saved(self) -> None:
        """Announce a settings save so widgets self-refresh (replaces reload() wiring)."""
        for section in ("battery", "connection", "flight_events", "commands"):
            self.bus.publish(topics.settings_changed(section), None)
        log.info("UIManager: settings saved — published settings/*/changed")

    # -- lifecycle ------------------------------------------------------------

    def shutdown(self) -> None:
        """Stop the serial receiver and tear down every widget. Idempotent."""
        if self._shutdown_done:
            return
        self._shutdown_done = True
        log.info("UIManager: shutdown — stopping services")
        try:
            self.serial.stop()
        except Exception:  # noqa: BLE001
            log.error("UIManager: error stopping serial service", exc_info=True)
        try:
            self.engine.teardown_all()
        except Exception:  # noqa: BLE001
            log.error("UIManager: error tearing down widgets", exc_info=True)

    def _load_dashboard(self) -> dict:
        """Load the active dashboard document, falling back to an empty grid."""
        path = layout_store.dashboard_path(self._dashboard_name)
        try:
            return layout_store.load_dashboard(path)
        except (OSError, layout_store.DashboardError) as exc:
            log.error("UIManager: failed to load dashboard '%s' (%s); using empty grid",
                      self._dashboard_name, exc)
            return {"schema": layout_store.SCHEMA_VERSION, "name": "empty",
                    "grid": {"cols": 12, "cell_h": 80, "gutter": 8, "margin": 12}, "widgets": []}

    def build_ui(self) -> None:
        """Create the UI, load the dashboard, and run the render loop until exit."""
        log.info("UIManager: building UI")
        dpg.create_context()

        # GNU Unifont covers the whole BMP so every glyph the widgets use renders.
        with dpg.font_registry():
            default_font = dpg.add_font("assets/fonts/Unifont/unifont.ttf", 16)
            dpg.add_font_range(0x0020, 0xFFFF, parent=default_font)
        dpg.bind_font(default_font)

        width, height = (1920, 1080)
        log.info("UIManager: creating viewport %dx%d", width, height)
        dpg.create_viewport(
            title="Ground Station GUI",
            width=width, height=height, x_pos=0, y_pos=0, decorated=False,
        )

        dpg.set_exit_callback(lambda: self.shutdown())
        with dpg.handler_registry():
            # Escape stops the loop; teardown runs after run_render_loop returns.
            dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=lambda: dpg.stop_dearpygui())

        with dpg.window(label="Ground Station UI", width=width, height=height,
                        no_move=True, no_resize=True):
            with dpg.tab_bar():
                flight_tab = dpg.add_tab(label="Flight Data")
                with dpg.tab(label="Settings"):
                    self.settings_window.draw_ui()

        # Build the dashboard into the Flight-Data tab, then keep it responsive.
        self.engine.load(self._load_dashboard(), parent=flight_tab)
        dpg.set_viewport_resize_callback(lambda *_: self.engine.on_viewport_resize())

        log.info("UIManager: entering render loop")
        dpg.setup_dearpygui()
        dpg.show_viewport()
        run_render_loop(self.bus)

        log.info("UIManager: render loop exited — cleaning up")
        self.shutdown()
        dpg.destroy_context()

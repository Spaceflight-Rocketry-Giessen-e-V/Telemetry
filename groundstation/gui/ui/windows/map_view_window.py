"""
map_view_window.py
------------------
Interactive slippy-map widget powered by OpenStreetMap tiles.

Tiles are fetched in a background ThreadPoolExecutor so the UI never blocks;
finished tiles are queued and swapped in on the next visible-handler tick. An
optional aircraft overlay polls the OpenSky Network REST API every 15 s.

Modular widget: subscribes to ``gps/fix`` for rocket position, namespaces every
DPG tag/registry per instance (so two maps can coexist), scopes the arrow-key
pan handler to when the map is hovered (it used to pan globally), and stops its
threads + deletes its registries in :py:meth:`destroy`.

Controls: +/- zoom · arrow keys pan (disengages Follow) · Centre · Follow ·
Traffic · Satellite (disabled pending licensing).
"""

import io
import logging
import math
import os
import queue
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import dearpygui.dearpygui as dpg
import requests
from PIL import Image

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)

# Minimum seconds between OpenSky API polls. Stay conservative to respect rate limits.
_TRAFFIC_POLL_INTERVAL = 15
# Degrees of padding added to each side of the viewport bounding box for the query.
_TRAFFIC_BOX_PAD = 1.0
_OPENSKY_URL = "https://opensky-network.org/api/states/all"


class MapViewWindow(Widget):
    """Tile-based interactive map with threaded tile loading and aircraft overlay."""

    TYPE_ID = "map"
    DISPLAY_NAME = "Map"
    DEFAULT_CELLS = (6, 7)
    MIN_CELLS = (4, 4)

    TILE_OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    _TILE_SAT = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )

    CACHE_FOLDER = "cache/map_coords"
    TILE_SIZE = 256
    PAN_FRACTION = 0.25
    _THREAD_POOL_SIZE = 6

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)

        self.zoom = int(self.config.get("zoom", 14))
        self.lat = float(self.config.get("lat", 50.591600181525635))
        self.lon = float(self.config.get("lon", 8.704157213218798))
        self.view_lat = self.lat
        self.view_lon = self.lon

        self.auto_centre = True
        self.satellite_mode = bool(self.config.get("satellite_mode", False))
        self.traffic_enabled = bool(self.config.get("traffic_enabled", False))

        self.map_width = self.TILE_SIZE * 3
        self.map_height = self.TILE_SIZE * 3

        self.tex_ids: list[tuple[tuple[int, int], int]] = []
        self.track: list[tuple[float, float]] = []

        # Set by background threads to request a redraw the main-thread visible
        # handler then performs; all DPG mutation stays on the main thread.
        self._needs_redraw = False
        self._state_lock = threading.Lock()
        self._counter_lock = threading.Lock()

        self._session_web_requests = 0
        self._total_cache_count = 0

        self._tile_ready_queue: queue.Queue = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=self._THREAD_POOL_SIZE, thread_name_prefix="tile-fetch")
        self._last_tile_origin: tuple[int, int] | None = None

        self._aircraft: list[dict] = []
        self._traffic_thread: threading.Thread | None = None
        self._traffic_stop = threading.Event()
        self._last_traffic_fetch: float = 0.0

        # Per-instance DPG tags/registries.
        self.tex_registry_tag = self.tag("tex_registry")
        self.drawlist_tag = self.tag("drawlist")
        self.key_handler_tag = self.tag("key_handler")
        self.satellite_btn_tag = self.tag("sat_btn")
        self.follow_btn_tag = self.tag("follow_btn")
        self.traffic_btn_tag = self.tag("traffic_btn")
        self.diag_cache_tag = self.tag("diag_cache")
        self.diag_web_tag = self.tag("diag_web")
        self._visible_handler: int | None = None
        self._themes: list[int] = []

        self._follow_theme_on = self._follow_theme_off = None
        self._traffic_theme_on = self._traffic_theme_off = None

        log.debug("MapViewWindow[%s]: init at (%.4f, %.4f) zoom=%d", self.iid, self.lat, self.lon, self.zoom)

    # -- coordinate helpers ---------------------------------------------------

    def latlon_to_pixel(self, lat: float, lon: float, zoom: int) -> tuple[float, float]:
        # Web Mercator is undefined at the poles; clamp to the ±85.0511° limit.
        lat = max(-85.0511287798066, min(85.0511287798066, lat))
        lat_rad = math.radians(lat)
        n = 2 ** zoom
        px = (lon + 180.0) / 360.0 * n * self.TILE_SIZE
        py = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n * self.TILE_SIZE
        return px, py

    def pixel_to_latlon(self, px: float, py: float, zoom: int) -> tuple[float, float]:
        n = 2 ** zoom
        lon = px / (n * self.TILE_SIZE) * 360.0 - 180.0
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / (n * self.TILE_SIZE)))))
        return lat, lon

    def _grid_origin_pixel(self) -> tuple[float, float]:
        cx, cy = self.latlon_to_pixel(self.view_lat, self.view_lon, self.zoom)
        return cx - self.map_width / 2.0, cy - self.map_height / 2.0

    def _grid_top_left_tile(self) -> tuple[int, int]:
        ox, oy = self._grid_origin_pixel()
        return int(math.floor(ox / self.TILE_SIZE)), int(math.floor(oy / self.TILE_SIZE))

    def _tile_counts(self) -> tuple[int, int]:
        cols = math.ceil(self.map_width / self.TILE_SIZE) + 2
        rows = math.ceil(self.map_height / self.TILE_SIZE) + 2
        if cols % 2 == 0: cols += 1
        if rows % 2 == 0: rows += 1
        return cols, rows

    def _world_to_screen(self, lat: float, lon: float) -> tuple[float, float]:
        px, py = self.latlon_to_pixel(lat, lon, self.zoom)
        ox, oy = self._grid_origin_pixel()
        return px - ox, py - oy

    def _viewport_bounds(self) -> tuple[float, float, float, float]:
        ox, oy = self._grid_origin_pixel()
        lat_max, lon_min = self.pixel_to_latlon(ox, oy, self.zoom)
        lat_min, lon_max = self.pixel_to_latlon(ox + self.map_width, oy + self.map_height, self.zoom)
        return lat_min, lon_min, lat_max, lon_max

    # -- diagnostics ----------------------------------------------------------

    def _count_cache_files(self) -> int:
        total = 0
        for sub in ("osm", "sat"):
            folder = os.path.join(self.CACHE_FOLDER, sub)
            if os.path.isdir(folder):
                total += sum(1 for f in os.listdir(folder) if f.endswith(".png"))
        return total

    def _update_diag(self) -> None:
        if dpg.does_item_exist(self.diag_cache_tag):
            dpg.set_value(self.diag_cache_tag, f"Cache: {self._total_cache_count} tiles")
        if dpg.does_item_exist(self.diag_web_tag):
            dpg.set_value(self.diag_web_tag, f"Web req: {self._session_web_requests}")

    def _make_button_theme(self, base: tuple, hovered: tuple) -> int:
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, base)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hovered)
        self._themes.append(theme)
        return theme

    def _update_follow_button(self) -> None:
        if not dpg.does_item_exist(self.follow_btn_tag):
            return
        if self.auto_centre:
            dpg.set_item_label(self.follow_btn_tag, "Follow: ON")
            dpg.bind_item_theme(self.follow_btn_tag, self._follow_theme_on)
        else:
            dpg.set_item_label(self.follow_btn_tag, "Follow: OFF")
            dpg.bind_item_theme(self.follow_btn_tag, self._follow_theme_off)

    def _update_traffic_button(self) -> None:
        if not dpg.does_item_exist(self.traffic_btn_tag):
            return
        if self.traffic_enabled:
            dpg.set_item_label(self.traffic_btn_tag, "Traffic: ON")
            dpg.bind_item_theme(self.traffic_btn_tag, self._traffic_theme_on)
        else:
            dpg.set_item_label(self.traffic_btn_tag, "Traffic: OFF")
            dpg.bind_item_theme(self.traffic_btn_tag, self._traffic_theme_off)

    # -- traffic / OpenSky ----------------------------------------------------

    def _fetch_traffic(self) -> None:
        """Background thread: poll OpenSky, derive the bbox from the viewport."""
        log.info("MapViewWindow[%s]: traffic thread started", self.iid)
        while not self._traffic_stop.is_set():
            elapsed = time.time() - self._last_traffic_fetch
            if elapsed < _TRAFFIC_POLL_INTERVAL:
                self._traffic_stop.wait(timeout=_TRAFFIC_POLL_INTERVAL - elapsed)
                continue
            try:
                lat_min, lon_min, lat_max, lon_max = self._viewport_bounds()
                params = {
                    "lamin": round(lat_min - _TRAFFIC_BOX_PAD, 4),
                    "lomin": round(lon_min - _TRAFFIC_BOX_PAD, 4),
                    "lamax": round(lat_max + _TRAFFIC_BOX_PAD, 4),
                    "lomax": round(lon_max + _TRAFFIC_BOX_PAD, 4),
                }
                resp = requests.get(_OPENSKY_URL, params=params, timeout=10,
                                    headers={"User-Agent": "SRPOG/Telemetry Ground Station"})
                resp.raise_for_status()
                data = resp.json()
                aircraft = []
                for sv in (data.get("states") or []):
                    if sv[5] is None or sv[6] is None:
                        continue
                    if sv[8] is True:
                        continue
                    aircraft.append({
                        "callsign": (sv[1] or "").strip() or sv[0],
                        "lon": sv[5], "lat": sv[6], "altitude": sv[7],
                        "velocity": sv[9], "heading": sv[10],
                    })
                self._aircraft = aircraft
                self._last_traffic_fetch = time.time()
                log.info("MapViewWindow[%s]: traffic updated — %d aircraft", self.iid, len(aircraft))
                self._needs_redraw = True
            except requests.RequestException as exc:
                log.warning("MapViewWindow[%s]: traffic fetch failed: %s", self.iid, exc)
                self._last_traffic_fetch = time.time()
        log.info("MapViewWindow[%s]: traffic thread stopped", self.iid)

    def _start_traffic(self) -> None:
        self._traffic_stop.clear()
        self._last_traffic_fetch = 0.0
        self._traffic_thread = threading.Thread(target=self._fetch_traffic, daemon=True,
                                                name=f"traffic-{self.iid}")
        self._traffic_thread.start()

    def _stop_traffic(self) -> None:
        self._traffic_stop.set()
        self._aircraft = []

    def _toggle_traffic(self) -> None:
        self.traffic_enabled = not self.traffic_enabled
        self._update_traffic_button()
        if self.traffic_enabled:
            self._start_traffic()
        else:
            self._stop_traffic()
            self._redraw_all(refetch=False)

    # -- tile fetching (blocking — runs in thread pool) -----------------------

    def _tile_cache_path(self, x: int, y: int, z: int, satellite: bool) -> str:
        folder = os.path.join(self.CACHE_FOLDER, "sat" if satellite else "osm")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{z}_{x}_{y}.png")

    def _fetch_tile_sync(self, x: int, y: int, z: int) -> Image.Image:
        satellite = self.satellite_mode
        path = self._tile_cache_path(x, y, z, satellite)
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as exc:  # noqa: BLE001
                log.warning("MapViewWindow: corrupt cache tile (%d,%d) z=%d: %s", x, y, z, exc)
        url = (self._TILE_SAT if satellite else self.TILE_OSM).format(z=z, x=x, y=y)
        r = requests.get(url, headers={
            "User-Agent": ("SRPOG/Telemetry Ground Station"
                           " (raketenbau@fb07.uni-giessen.de)"
                           " - github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry")
        }, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        img.save(path)
        with self._counter_lock:
            self._session_web_requests += 1
            self._total_cache_count += 1
        return img

    @staticmethod
    def _img_to_dpg_data(img: Image.Image) -> list[float]:
        return [c / 255.0 for px in img.getdata() for c in px]

    # -- tile management ------------------------------------------------------

    def draw_map_tiles(self) -> None:
        new_origin = self._grid_top_left_tile()
        if new_origin == self._last_tile_origin:
            return
        self._last_tile_origin = new_origin

        for _, tex_id in self.tex_ids:
            if dpg.does_item_exist(tex_id):
                dpg.delete_item(tex_id)
        self.tex_ids.clear()

        cols, rows = self._tile_counts()
        tx0, ty0 = new_origin
        n = 2 ** self.zoom
        for dx in range(cols):
            for dy in range(rows):
                tx, ty = tx0 + dx, ty0 + dy
                if ty < 0 or ty >= n:
                    continue
                fx = tx % n

                def _on_done(future, _dx=dx, _dy=dy, _fx=fx, _ty=ty, _origin=new_origin):
                    try:
                        data = self._img_to_dpg_data(future.result())
                        self._tile_ready_queue.put((_origin, _dx, _dy, data))
                    except Exception as exc:  # noqa: BLE001
                        log.warning("MapViewWindow: tile (%d,%d) z=%d failed: %s", _fx, _ty, self.zoom, exc)

                self._executor.submit(self._fetch_tile_sync, fx, ty, self.zoom).add_done_callback(_on_done)

    def _pump_tile_queue(self) -> None:
        if self._tile_ready_queue.empty():
            return
        slot_index: dict[tuple[int, int], int] = {pos: tid for pos, tid in self.tex_ids}
        current_origin = self._last_tile_origin
        changed = False
        while not self._tile_ready_queue.empty():
            try:
                origin, dx, dy, data = self._tile_ready_queue.get_nowait()
            except queue.Empty:
                break
            if origin != current_origin:
                continue
            if not dpg.does_item_exist(self.tex_registry_tag):
                return  # widget torn down mid-drain
            tex_id = dpg.add_static_texture(self.TILE_SIZE, self.TILE_SIZE, data, parent=self.tex_registry_tag)
            old = slot_index.get((dx, dy))
            if old and dpg.does_item_exist(old):
                dpg.delete_item(old)
            slot_index[(dx, dy)] = tex_id
            changed = True
        if changed:
            self.tex_ids = list(slot_index.items())
            self._redraw_all(refetch=False)
            self._update_diag()

    def _on_frame(self) -> None:
        """Main-thread per-frame tick (bound as the drawlist's visible handler)."""
        self._pump_tile_queue()
        if self._needs_redraw:
            self._needs_redraw = False
            self._redraw_all(refetch=True)

    # -- drawing --------------------------------------------------------------

    def redraw_tiles(self) -> None:
        ox, oy = self._grid_origin_pixel()
        tx0, ty0 = self._grid_top_left_tile()
        for (dx, dy), tex_id in self.tex_ids:
            x0 = (tx0 + dx) * self.TILE_SIZE - ox
            y0 = (ty0 + dy) * self.TILE_SIZE - oy
            dpg.draw_image(tex_id, (x0, y0), (x0 + self.TILE_SIZE, y0 + self.TILE_SIZE), parent=self.drawlist_tag)

    def draw_marker(self) -> None:
        if not dpg.does_item_exist(self.drawlist_tag):
            return
        sx, sy = self._world_to_screen(self.lat, self.lon)
        r, arm = 7, 12
        dpg.draw_circle((sx, sy), r, fill=(255, 60, 60, 200), color=(220, 0, 0, 255), thickness=2, parent=self.drawlist_tag)
        dpg.draw_line((sx - arm, sy), (sx + arm, sy), color=(220, 0, 0, 255), thickness=1, parent=self.drawlist_tag)
        dpg.draw_line((sx, sy - arm), (sx, sy + arm), color=(220, 0, 0, 255), thickness=1, parent=self.drawlist_tag)

    def draw_track_polyline(self) -> None:
        if not dpg.does_item_exist(self.drawlist_tag):
            return
        with self._state_lock:
            track = list(self.track)
        if len(track) < 2:
            return
        margin = self.TILE_SIZE
        points = []
        for lat, lon in track:
            sx, sy = self._world_to_screen(lat, lon)
            if math.isnan(sx) or math.isnan(sy) or math.isinf(sx) or math.isinf(sy):
                continue
            if -margin <= sx <= self.map_width + margin and -margin <= sy <= self.map_height + margin:
                points.append([sx, sy])
        if len(points) >= 2:
            dpg.draw_polyline(points, color=(0, 220, 80, 255), thickness=2, parent=self.drawlist_tag)

    def draw_aircraft(self) -> None:
        if not self.traffic_enabled or not self._aircraft:
            return
        margin = self.TILE_SIZE
        color = (0, 0, 0, 255)
        for ac in self._aircraft:
            sx, sy = self._world_to_screen(ac["lat"], ac["lon"])
            if not (-margin <= sx <= self.map_width + margin and -margin <= sy <= self.map_height + margin):
                continue
            heading = ac.get("heading")
            if heading is not None:
                angle = math.radians(heading)
                length = 10
                tip_x = sx + length * math.sin(angle)
                tip_y = sy - length * math.cos(angle)
                dpg.draw_line((sx, sy), (tip_x, tip_y), color=color, thickness=2, parent=self.drawlist_tag)
                for side in (-1, 1):
                    wing_angle = angle + side * math.radians(140)
                    wx = tip_x + 5 * math.sin(wing_angle)
                    wy = tip_y - 5 * math.cos(wing_angle)
                    dpg.draw_line((tip_x, tip_y), (wx, wy), color=color, thickness=2, parent=self.drawlist_tag)
            else:
                dpg.draw_circle((sx, sy), 4, fill=color, color=color, parent=self.drawlist_tag)
            dpg.draw_text((sx + 8, sy - 8), ac["callsign"], color=color, size=11, parent=self.drawlist_tag)

    def _draw_diag_overlay(self) -> None:
        pad, lh = 6, 13
        x = pad
        y = self.map_height - pad - lh * 2
        dpg.draw_rectangle((x - 2, y - 2), (x + 160, y + lh * 2 + 2), fill=(0, 0, 0, 120), color=(0, 0, 0, 0), parent=self.drawlist_tag)
        dpg.draw_text((x, y), f"Cache: {self._total_cache_count} tiles", color=(220, 220, 220, 220), size=12, parent=self.drawlist_tag, tag=self.diag_cache_tag)
        dpg.draw_text((x, y + lh), f"Web req: {self._session_web_requests}", color=(220, 220, 220, 220), size=12, parent=self.drawlist_tag, tag=self.diag_web_tag)

    def _redraw_all(self, refetch: bool = True) -> None:
        if not dpg.does_item_exist(self.drawlist_tag):
            return
        if refetch:
            self.draw_map_tiles()
        dpg.delete_item(self.drawlist_tag, children_only=True)
        self.redraw_tiles()
        self.draw_track_polyline()
        self.draw_marker()
        self.draw_aircraft()
        self._draw_diag_overlay()

    # -- build ----------------------------------------------------------------

    def build(self, width: int, height: int) -> None:
        # Leave room under the map for the control button row.
        self.map_width = max(self.TILE_SIZE, width - 4)
        self.map_height = max(self.TILE_SIZE, height - 60)
        self.view_lat, self.view_lon = self.lat, self.lon
        self._total_cache_count = self._count_cache_files()
        self._session_web_requests = 0

        dpg.add_texture_registry(tag=self.tex_registry_tag)

        # Arrow-key pan is a global handler, but each callback ignores the key
        # unless THIS map is hovered — so keys don't pan a map the user isn't on.
        with dpg.handler_registry(tag=self.key_handler_tag):
            dpg.add_key_press_handler(dpg.mvKey_Up, callback=lambda: self._pan(0, -1))
            dpg.add_key_press_handler(dpg.mvKey_Down, callback=lambda: self._pan(0, 1))
            dpg.add_key_press_handler(dpg.mvKey_Left, callback=lambda: self._pan(-1, 0))
            dpg.add_key_press_handler(dpg.mvKey_Right, callback=lambda: self._pan(1, 0))

        with dpg.drawlist(width=self.map_width - 15, height=self.map_height, tag=self.drawlist_tag):
            self._draw_diag_overlay()
        self.draw_map_tiles()
        dpg.add_spacer(height=2)

        with dpg.group(horizontal=True):
            dpg.add_button(label=" + ", width=36, callback=lambda: self.update_zoom(self.zoom + 1))
            dpg.add_button(label=" - ", width=36, callback=lambda: self.update_zoom(self.zoom - 1))
            dpg.add_spacer(width=6)
            dpg.add_button(label="Centre", width=60, callback=self._centre_once)
            dpg.add_button(label="Follow: ON", width=90, tag=self.follow_btn_tag, callback=self._toggle_follow)
            dpg.add_button(label="Traffic: OFF", width=90, tag=self.traffic_btn_tag, callback=self._toggle_traffic)
            dpg.add_spacer(width=6)
            dpg.add_button(label="Satellite", width=80, tag=self.satellite_btn_tag,
                           callback=self._toggle_satellite, enabled=False)
            dpg.add_spacer(width=6)
            dpg.add_text("Map data ©")
            dpg.add_button(label="OpenStreetMap",
                           callback=lambda: webbrowser.open("https://www.openstreetmap.org/copyright"))

        self._follow_theme_on = self._make_button_theme((40, 140, 40, 255), (60, 170, 60, 255))
        self._follow_theme_off = self._make_button_theme((80, 80, 80, 255), (110, 110, 110, 255))
        self._traffic_theme_on = self._make_button_theme((40, 100, 180, 255), (60, 130, 210, 255))
        self._traffic_theme_off = self._make_button_theme((80, 80, 80, 255), (110, 110, 110, 255))
        self._update_follow_button()
        self._update_traffic_button()

        with dpg.item_handler_registry() as self._visible_handler:
            dpg.add_item_visible_handler(callback=self._on_frame)
        dpg.bind_item_handler_registry(self.drawlist_tag, self._visible_handler)

        self.subscribe(topics.GPS_FIX, lambda fix: self.update_location(fix[0], fix[1]))
        if self.traffic_enabled:
            self._start_traffic()

    # -- user interaction -----------------------------------------------------

    def _hovered(self) -> bool:
        return dpg.does_item_exist(self.drawlist_tag) and dpg.is_item_hovered(self.drawlist_tag)

    def _centre_once(self) -> None:
        self.view_lat, self.view_lon = self.lat, self.lon
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

    def _toggle_follow(self) -> None:
        self.auto_centre = not self.auto_centre
        self._update_follow_button()
        if self.auto_centre:
            self.view_lat, self.view_lon = self.lat, self.lon
            self._last_tile_origin = None
            self._redraw_all(refetch=True)

    def _toggle_satellite(self) -> None:
        self.satellite_mode = not self.satellite_mode
        dpg.set_item_label(self.satellite_btn_tag, "Map view" if self.satellite_mode else "Satellite")
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

    def _pan(self, dx: int, dy: int) -> None:
        # Global key handler: only act when the pointer is over THIS map.
        if not self._hovered():
            return
        if self.auto_centre:
            self.auto_centre = False
            self._update_follow_button()
        pan_px = self.map_width * self.PAN_FRACTION * dx
        pan_py = self.map_height * self.PAN_FRACTION * dy
        cx, cy = self.latlon_to_pixel(self.view_lat, self.view_lon, self.zoom)
        new_lat, new_lon = self.pixel_to_latlon(cx + pan_px, cy + pan_py, self.zoom)
        self.view_lat = max(-85.0511, min(85.0511, new_lat))
        self.view_lon = (new_lon + 180.0) % 360.0 - 180.0
        self._redraw_all(refetch=True)
        self._update_diag()

    # -- external update ------------------------------------------------------

    def update_location(self, lat: float, lon: float) -> None:
        """Update the rocket position and append a track point (from ``gps/fix``)."""
        if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
            return
        if lat == 0.0 and lon == 0.0:
            return
        self.lat, self.lon = lat, lon
        with self._state_lock:
            self.track.append((lat, lon))
        if self.auto_centre:
            self.view_lat, self.view_lon = lat, lon
        self._needs_redraw = True

    def update_zoom(self, new_zoom: int) -> None:
        new_zoom = max(1, min(19, new_zoom))
        if new_zoom == self.zoom:
            return
        self.zoom = new_zoom
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

    def get_config(self) -> dict:
        cfg = dict(self.config)
        cfg.update(lat=self.lat, lon=self.lon, zoom=self.zoom,
                   satellite_mode=self.satellite_mode, traffic_enabled=self.traffic_enabled)
        return cfg

    # -- teardown -------------------------------------------------------------

    def _shutdown_threads(self) -> None:
        self._stop_traffic()
        if self._traffic_thread and self._traffic_thread.is_alive():
            self._traffic_thread.join(timeout=2)
        self._executor.shutdown(wait=False)

    def destroy(self) -> None:
        self._shutdown_threads()
        for reg in (self.key_handler_tag, self.tex_registry_tag):
            if dpg.does_item_exist(reg):
                dpg.delete_item(reg)
        if self._visible_handler is not None and dpg.does_item_exist(self._visible_handler):
            dpg.delete_item(self._visible_handler)
        for theme in self._themes:
            if dpg.does_item_exist(theme):
                dpg.delete_item(theme)
        self._themes.clear()
        super().destroy()

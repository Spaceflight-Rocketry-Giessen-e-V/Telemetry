"""
map_view_window.py
------------------
Interactive slippy-map widget powered by OpenStreetMap tiles.

Tiles are fetched in a background ThreadPoolExecutor so the UI never blocks.
Finished tiles are queued and swapped in on the next visible-handler tick.

The optional aircraft overlay polls the OpenSky Network REST API (no key
required) every 15 seconds and renders nearby airborne traffic as directional
arrows with callsign labels.

Controls:
  - +  /  - buttons   — zoom in/out
  - Arrow keys         — pan (disengages Follow mode)
  - Centre button      — snap the viewport to the rocket once
  - Follow button      — toggle continuous auto-centre on/off
  - Traffic button     — toggle the OpenSky aircraft overlay on/off
  - Satellite button   — switch tile source (disabled until licencing confirmed)
"""

import io
import itertools
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

log = logging.getLogger(__name__)

# Minimum seconds between OpenSky API polls. Stay conservative to respect rate limits.
_TRAFFIC_POLL_INTERVAL = 15

# Degrees of padding added to each side of the viewport bounding box for the query.
# A 1.0° box is roughly 100 km at mid-latitudes.
_TRAFFIC_BOX_PAD = 1.0

_OPENSKY_URL = "https://opensky-network.org/api/states/all"


class MapViewWindow:
    """Tile-based interactive map with threaded tile loading and aircraft overlay."""

    _id_counter = itertools.count()

    TILE_OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    _TILE_SAT = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )

    CACHE_FOLDER = "cache/map_coords"
    TILE_SIZE = 256
    PAN_FRACTION = 0.25
    _THREAD_POOL_SIZE = 6

    def __init__(
            self,
            instance_id: str | None = None,
            lat: float = 50.591600181525635,
            lon: float = 8.704157213218798,
            zoom: int = 14,
    ):
        uid = instance_id if instance_id is not None else str(next(self._id_counter))
        self._uid = uid

        self.zoom = zoom
        self.lat = lat
        self.lon = lon
        self.view_lat = lat
        self.view_lon = lon

        self.auto_centre = True
        self.satellite_mode = False

        self.map_width = self.TILE_SIZE * 3
        self.map_height = self.TILE_SIZE * 3

        # List of (grid_position, texture_id) pairs for currently loaded tiles.
        self.tex_ids: list[tuple[tuple[int, int], int]] = []
        # Flight-path track points as (lat, lon) tuples.
        self.track: list[tuple[float, float]] = []

        self._session_web_requests = 0
        self._total_cache_count = 0

        self._tile_ready_queue: queue.Queue = queue.Queue()
        self._executor = ThreadPoolExecutor(
            max_workers=self._THREAD_POOL_SIZE,
            thread_name_prefix="tile-fetch",
        )
        self._last_tile_origin: tuple[int, int] | None = None

        self.traffic_enabled = False
        # Each entry: {callsign, lat, lon, heading, altitude, velocity}
        self._aircraft: list[dict] = []
        self._traffic_thread: threading.Thread | None = None
        self._traffic_stop = threading.Event()
        self._last_traffic_fetch: float = 0.0

        self.tex_registry_tag = f"map_tex_registry_{uid}"
        self.drawlist_tag = f"map_drawlist_{uid}"
        self.key_handler_tag = f"map_key_handler_{uid}"
        self.satellite_btn_tag = f"map_sat_btn_{uid}"
        self.follow_btn_tag = f"map_follow_btn_{uid}"
        self.traffic_btn_tag = f"map_traffic_btn_{uid}"
        self.diag_cache_tag = f"map_diag_cache_{uid}"
        self.diag_web_tag = f"map_diag_web_{uid}"

        log.debug("MapViewWindow[%s]: init at (%.4f, %.4f) zoom=%d", uid, lat, lon, zoom)

    # -------------------------------------------------------------------------
    # Coordinate helpers
    # -------------------------------------------------------------------------

    def latlon_to_pixel(self, lat: float, lon: float, zoom: int) -> tuple[float, float]:
        """Convert a geographic coordinate to pixel coordinates at *zoom*."""
        lat_rad = math.radians(lat)
        n = 2 ** zoom
        px = (lon + 180.0) / 360.0 * n * self.TILE_SIZE
        py = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n * self.TILE_SIZE
        return px, py

    def pixel_to_latlon(self, px: float, py: float, zoom: int) -> tuple[float, float]:
        """Convert pixel coordinates at *zoom* back to a geographic coordinate."""
        n = 2 ** zoom
        lon = px / (n * self.TILE_SIZE) * 360.0 - 180.0
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / (n * self.TILE_SIZE)))))
        return lat, lon

    def _grid_origin_pixel(self) -> tuple[float, float]:
        """Return the pixel coordinate of the top-left corner of the tile grid."""
        cx, cy = self.latlon_to_pixel(self.view_lat, self.view_lon, self.zoom)
        return cx - self.map_width / 2.0, cy - self.map_height / 2.0

    def _grid_top_left_tile(self) -> tuple[int, int]:
        """Return the tile index of the top-left tile in the current viewport."""
        ox, oy = self._grid_origin_pixel()
        return int(math.floor(ox / self.TILE_SIZE)), int(math.floor(oy / self.TILE_SIZE))

    def _tile_counts(self) -> tuple[int, int]:
        """Return the number of tile columns and rows needed to fill the viewport."""
        cols = math.ceil(self.map_width / self.TILE_SIZE) + 2
        rows = math.ceil(self.map_height / self.TILE_SIZE) + 2
        if cols % 2 == 0: cols += 1
        if rows % 2 == 0: rows += 1
        return cols, rows

    def _world_to_screen(self, lat: float, lon: float) -> tuple[float, float]:
        """Project a geographic coordinate to screen (drawlist) coordinates."""
        px, py = self.latlon_to_pixel(lat, lon, self.zoom)
        ox, oy = self._grid_origin_pixel()
        return px - ox, py - oy

    def _viewport_bounds(self) -> tuple[float, float, float, float]:
        """Return ``(lat_min, lon_min, lat_max, lon_max)`` of the current viewport."""
        ox, oy = self._grid_origin_pixel()
        lat_max, lon_min = self.pixel_to_latlon(ox, oy, self.zoom)
        lat_min, lon_max = self.pixel_to_latlon(ox + self.map_width, oy + self.map_height, self.zoom)
        return lat_min, lon_min, lat_max, lon_max

    # -------------------------------------------------------------------------
    # Diagnostics overlay
    # -------------------------------------------------------------------------

    def _count_cache_files(self) -> int:
        """Return the total number of cached tile images on disk."""
        total = 0
        for sub in ("osm", "sat"):
            folder = os.path.join(self.CACHE_FOLDER, sub)
            if os.path.isdir(folder):
                total += sum(1 for f in os.listdir(folder) if f.endswith(".png"))
        return total

    def _update_diag(self) -> None:
        """Refresh the diagnostics overlay text items."""
        if dpg.does_item_exist(self.diag_cache_tag):
            dpg.set_value(self.diag_cache_tag, f"Cache: {self._total_cache_count} tiles")
        if dpg.does_item_exist(self.diag_web_tag):
            dpg.set_value(self.diag_web_tag, f"Web req: {self._session_web_requests}")

    def _update_follow_button(self) -> None:
        """Recolour the Follow button to reflect the current auto-centre state."""
        if not dpg.does_item_exist(self.follow_btn_tag):
            return
        if self.auto_centre:
            dpg.set_item_label(self.follow_btn_tag, "Follow: ON")
            with dpg.theme() as t:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 140, 40, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 170, 60, 255))
            dpg.bind_item_theme(self.follow_btn_tag, t)
        else:
            dpg.set_item_label(self.follow_btn_tag, "Follow: OFF")
            with dpg.theme() as t:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (80, 80, 80, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (110, 110, 110, 255))
            dpg.bind_item_theme(self.follow_btn_tag, t)

    def _update_traffic_button(self) -> None:
        """Recolour the Traffic button to reflect the current overlay state."""
        if not dpg.does_item_exist(self.traffic_btn_tag):
            return
        if self.traffic_enabled:
            dpg.set_item_label(self.traffic_btn_tag, "Traffic: ON")
            with dpg.theme() as t:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 100, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 130, 210, 255))
            dpg.bind_item_theme(self.traffic_btn_tag, t)
        else:
            dpg.set_item_label(self.traffic_btn_tag, "Traffic: OFF")
            with dpg.theme() as t:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (80, 80, 80, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (110, 110, 110, 255))
            dpg.bind_item_theme(self.traffic_btn_tag, t)

    # -------------------------------------------------------------------------
    # Traffic / OpenSky
    # -------------------------------------------------------------------------

    def _fetch_traffic(self) -> None:
        """
        Background thread: poll OpenSky every ``_TRAFFIC_POLL_INTERVAL`` seconds.

        Derives the bounding box from the current viewport so only nearby
        aircraft are fetched. Results are stored in ``self._aircraft``; the
        main thread reads this on the next redraw tick. Sleeps in short
        intervals so the stop event is checked promptly.
        """
        log.info("MapViewWindow[%s]: traffic thread started", self._uid)

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
                log.debug("MapViewWindow[%s]: fetching traffic bbox=%s", self._uid, params)

                resp = requests.get(
                    _OPENSKY_URL, params=params,
                    timeout=10,
                    headers={"User-Agent": "SRPOG/Telemetry Ground Station"},
                )
                resp.raise_for_status()
                data = resp.json()

                aircraft = []
                for sv in (data.get("states") or []):
                    # OpenSky state vector field indices:
                    # 0=icao24, 1=callsign, 5=lon, 6=lat, 7=baro_alt,
                    # 9=velocity, 10=heading, 13=on_ground
                    if sv[5] is None or sv[6] is None:
                        continue  # no position fix
                    if sv[8] is True:
                        continue  # on ground — skip ground traffic
                    aircraft.append({
                        "callsign": (sv[1] or "").strip() or sv[0],
                        "lon": sv[5],
                        "lat": sv[6],
                        "altitude": sv[7],  # metres, may be None
                        "velocity": sv[9],  # m/s, may be None
                        "heading": sv[10],  # degrees true, may be None
                    })

                self._aircraft = aircraft
                self._last_traffic_fetch = time.time()
                log.info("MapViewWindow[%s]: traffic updated — %d aircraft", self._uid, len(aircraft))

                self._redraw_all(refetch=False)

            except requests.RequestException as exc:
                log.warning("MapViewWindow[%s]: traffic fetch failed: %s", self._uid, exc)
                self._last_traffic_fetch = time.time()  # back off even on error

        log.info("MapViewWindow[%s]: traffic thread stopped", self._uid)

    def _start_traffic(self) -> None:
        """Start the background OpenSky polling thread."""
        self._traffic_stop.clear()
        self._last_traffic_fetch = 0.0  # trigger an immediate fetch on first iteration
        self._traffic_thread = threading.Thread(
            target=self._fetch_traffic,
            daemon=True,
            name=f"traffic-{self._uid}",
        )
        self._traffic_thread.start()

    def _stop_traffic(self) -> None:
        """Signal the polling thread to stop and clear the aircraft list."""
        self._traffic_stop.set()
        self._aircraft = []

    def _toggle_traffic(self) -> None:
        """Toggle the aircraft overlay on or off."""
        self.traffic_enabled = not self.traffic_enabled
        self._update_traffic_button()
        if self.traffic_enabled:
            log.info("MapViewWindow[%s]: traffic overlay enabled", self._uid)
            self._start_traffic()
        else:
            log.info("MapViewWindow[%s]: traffic overlay disabled", self._uid)
            self._stop_traffic()
            self._redraw_all(refetch=False)

    # -------------------------------------------------------------------------
    # Tile fetching (blocking — runs in thread pool)
    # -------------------------------------------------------------------------

    def _tile_cache_path(self, x: int, y: int, z: int, satellite: bool) -> str:
        """Return the filesystem path for the cached version of a tile."""
        folder = os.path.join(self.CACHE_FOLDER, "sat" if satellite else "osm")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{z}_{x}_{y}.png")

    def _fetch_tile_sync(self, x: int, y: int, z: int) -> Image.Image:
        """
        Fetch tile ``(x, y)`` at zoom *z*, using the disk cache when available.

        Falls back to an HTTP request if the tile is not cached. Saves the
        downloaded image to disk for subsequent calls.
        """
        satellite = self.satellite_mode
        path = self._tile_cache_path(x, y, z, satellite)

        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as exc:
                log.warning("MapViewWindow: corrupt cache tile (%d,%d) z=%d: %s", x, y, z, exc)

        url = (self._TILE_SAT if satellite else self.TILE_OSM).format(z=z, x=x, y=y)
        r = requests.get(url, headers={
            "User-Agent": (
                "SRPOG/Telemetry Ground Station"
                " (raketenbau@fb07.uni-giessen.de)"
                " - github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry"
            )
        }, timeout=10)
        r.raise_for_status()

        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        img.save(path)
        self._session_web_requests += 1
        self._total_cache_count += 1
        return img

    @staticmethod
    def _img_to_dpg_data(img: Image.Image) -> list[float]:
        """Flatten an RGBA image into the normalised float list expected by DPG."""
        return [c / 255.0 for px in img.getdata() for c in px]

    # -------------------------------------------------------------------------
    # Tile management
    # -------------------------------------------------------------------------

    def draw_map_tiles(self) -> None:
        """
        Submit tile-fetch tasks to the thread pool for the current viewport.

        Each finished tile is placed on ``_tile_ready_queue``; the main
        thread swaps textures in via :py:meth:`_pump_tile_queue`. Does nothing
        if the tile origin has not changed since the last call.
        """
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

        for dx in range(cols):
            for dy in range(rows):
                tx, ty = tx0 + dx, ty0 + dy

                def _on_done(future, _dx=dx, _dy=dy, _tx=tx, _ty=ty):
                    try:
                        data = self._img_to_dpg_data(future.result())
                        self._tile_ready_queue.put((_dx, _dy, data))
                    except Exception as exc:
                        log.warning("MapViewWindow: tile (%d,%d) z=%d failed: %s",
                                    _tx, _ty, self.zoom, exc)

                self._executor.submit(self._fetch_tile_sync, tx, ty, self.zoom).add_done_callback(_on_done)

    def _pump_tile_queue(self) -> None:
        """
        Drain finished tile data from the queue and swap in new textures.

        Called every visible frame via the item handler. Triggers a full
        redraw when at least one texture has been updated.
        """
        if self._tile_ready_queue.empty():
            return

        slot_index: dict[tuple[int, int], int] = {pos: tid for pos, tid in self.tex_ids}
        changed = False

        while not self._tile_ready_queue.empty():
            try:
                dx, dy, data = self._tile_ready_queue.get_nowait()
            except queue.Empty:
                break

            tex_id = dpg.add_static_texture(
                self.TILE_SIZE, self.TILE_SIZE, data,
                parent=self.tex_registry_tag,
            )
            old = slot_index.get((dx, dy))
            if old and dpg.does_item_exist(old):
                dpg.delete_item(old)
            slot_index[(dx, dy)] = tex_id
            changed = True

        if changed:
            self.tex_ids = list(slot_index.items())
            self._redraw_all(refetch=False)
            self._update_diag()

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def redraw_tiles(self) -> None:
        """Blit all currently loaded tile textures to the drawlist."""
        ox, oy = self._grid_origin_pixel()
        tx0, ty0 = self._grid_top_left_tile()
        for (dx, dy), tex_id in self.tex_ids:
            x0 = (tx0 + dx) * self.TILE_SIZE - ox
            y0 = (ty0 + dy) * self.TILE_SIZE - oy
            dpg.draw_image(tex_id, (x0, y0), (x0 + self.TILE_SIZE, y0 + self.TILE_SIZE),
                           parent=self.drawlist_tag)

    def draw_marker(self) -> None:
        """Draw the rocket position marker (circle + crosshair) on the drawlist."""
        if not dpg.does_item_exist(self.drawlist_tag):
            return
        sx, sy = self._world_to_screen(self.lat, self.lon)
        r, arm = 7, 12
        dpg.draw_circle((sx, sy), r, fill=(255, 60, 60, 200), color=(220, 0, 0, 255),
                        thickness=2, parent=self.drawlist_tag)
        dpg.draw_line((sx - arm, sy), (sx + arm, sy), color=(220, 0, 0, 255),
                      thickness=1, parent=self.drawlist_tag)
        dpg.draw_line((sx, sy - arm), (sx, sy + arm), color=(220, 0, 0, 255),
                      thickness=1, parent=self.drawlist_tag)

    def draw_track_polyline(self) -> None:
        """Draw the flight-path polyline from the accumulated track points."""
        if len(self.track) < 2 or not dpg.does_item_exist(self.drawlist_tag):
            return
        margin = self.TILE_SIZE
        points = []
        for lat, lon in self.track:
            sx, sy = self._world_to_screen(lat, lon)
            if math.isnan(sx) or math.isnan(sy) or math.isinf(sx) or math.isinf(sy):
                continue
            if -margin <= sx <= self.map_width + margin and -margin <= sy <= self.map_height + margin:
                points.append([sx, sy])
        if len(points) >= 2:
            dpg.draw_polyline(points, color=(0, 220, 80, 255), thickness=2,
                              parent=self.drawlist_tag)

    def draw_aircraft(self) -> None:
        """
        Draw each airborne aircraft as a directional arrow with its callsign.

        Aircraft outside the viewport are culled. When heading data is
        available a rotated arrow is drawn; otherwise a plain circle is used.
        """
        if not self.traffic_enabled or not self._aircraft:
            return

        margin = self.TILE_SIZE
        color = (0, 0, 0, 255)

        for ac in self._aircraft:
            sx, sy = self._world_to_screen(ac["lat"], ac["lon"])

            if not (-margin <= sx <= self.map_width + margin
                    and -margin <= sy <= self.map_height + margin):
                continue

            heading = ac.get("heading")

            if heading is not None:
                # Heading 0° = north = up on screen (screen-y decreases upward).
                angle = math.radians(heading)
                length = 10
                tip_x = sx + length * math.sin(angle)
                tip_y = sy - length * math.cos(angle)

                dpg.draw_line((sx, sy), (tip_x, tip_y), color=color,
                              thickness=2, parent=self.drawlist_tag)

                # Two short winglets at ~140° from the tip to form an arrowhead.
                for side in (-1, 1):
                    wing_angle = angle + side * math.radians(140)
                    wx = tip_x + 5 * math.sin(wing_angle)
                    wy = tip_y - 5 * math.cos(wing_angle)
                    dpg.draw_line((tip_x, tip_y), (wx, wy), color=color,
                                  thickness=2, parent=self.drawlist_tag)
            else:
                dpg.draw_circle((sx, sy), 4, fill=color, color=color,
                                parent=self.drawlist_tag)

            dpg.draw_text((sx + 8, sy - 8), ac["callsign"],
                          color=color, size=11, parent=self.drawlist_tag)

    def _draw_diag_overlay(self) -> None:
        """Render the tile-cache and web-request counters in the bottom-left corner."""
        pad, lh = 6, 13
        x = pad
        y = self.map_height - pad - lh * 2
        dpg.draw_rectangle((x - 2, y - 2), (x + 160, y + lh * 2 + 2),
                           fill=(0, 0, 0, 120), color=(0, 0, 0, 0),
                           parent=self.drawlist_tag)
        dpg.draw_text((x, y), f"Cache: {self._total_cache_count} tiles",
                      color=(220, 220, 220, 220), size=12,
                      parent=self.drawlist_tag, tag=self.diag_cache_tag)
        dpg.draw_text((x, y + lh), f"Web req: {self._session_web_requests}",
                      color=(220, 220, 220, 220), size=12,
                      parent=self.drawlist_tag, tag=self.diag_web_tag)

    def _redraw_all(self, refetch: bool = True) -> None:
        """
        Clear and repaint the drawlist in layer order: tiles, track, marker, aircraft, diagnostics.

        Parameters
        ----------
        refetch:
            When ``True``, :py:meth:`draw_map_tiles` is called first to
            submit new tile requests for the current viewport.
        """
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

    # -------------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------------

    def draw_ui(self, window_width: int | None = None, window_height: int | None = None) -> None:
        """
        Create the map child-window, drawlist, and control buttons.

        Call once during UI construction.
        """
        self.map_width = window_width or self.TILE_SIZE * 3
        self.map_height = window_height or self.TILE_SIZE * 3
        self.view_lat = self.lat
        self.view_lon = self.lon

        self._total_cache_count = self._count_cache_files()
        self._session_web_requests = 0

        dpg.add_texture_registry(tag=self.tex_registry_tag)

        with dpg.handler_registry(tag=self.key_handler_tag):
            dpg.add_key_press_handler(dpg.mvKey_Up, callback=lambda: self._pan(0, -1))
            dpg.add_key_press_handler(dpg.mvKey_Down, callback=lambda: self._pan(0, 1))
            dpg.add_key_press_handler(dpg.mvKey_Left, callback=lambda: self._pan(-1, 0))
            dpg.add_key_press_handler(dpg.mvKey_Right, callback=lambda: self._pan(1, 0))

        with dpg.child_window(label="Map", width=self.map_width, height=self.map_height + 60):
            with dpg.drawlist(width=self.map_width - 15, height=self.map_height,
                              tag=self.drawlist_tag):
                self._draw_diag_overlay()

            self.draw_map_tiles()
            dpg.add_spacer(height=2)

            with dpg.group(horizontal=True):
                dpg.add_button(label=" + ", width=36, callback=lambda: self.update_zoom(self.zoom + 1))
                dpg.add_button(label=" - ", width=36, callback=lambda: self.update_zoom(self.zoom - 1))
                dpg.add_spacer(width=6)
                dpg.add_button(label="Centre", width=60, callback=self._centre_once)
                dpg.add_button(label="Follow: ON", width=90,
                               tag=self.follow_btn_tag, callback=self._toggle_follow)
                dpg.add_button(label="Traffic: OFF", width=90,
                               tag=self.traffic_btn_tag, callback=self._toggle_traffic)
                dpg.add_spacer(width=6)
                dpg.add_button(label="Satellite", width=80,
                               tag=self.satellite_btn_tag,
                               callback=self._toggle_satellite, enabled=False)
                dpg.add_spacer(width=6)
                dpg.add_text("Map data ©")
                dpg.add_button(label="OpenStreetMap",
                               callback=lambda: webbrowser.open("https://www.openstreetmap.org/copyright"))

        self._update_follow_button()
        self._update_traffic_button()

        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(callback=self._pump_tile_queue)
        dpg.bind_item_handler_registry(self.drawlist_tag, handler)

    # -------------------------------------------------------------------------
    # User-interaction callbacks
    # -------------------------------------------------------------------------

    def _centre_once(self) -> None:
        """Snap the viewport to the current rocket position without enabling Follow."""
        self.view_lat = self.lat
        self.view_lon = self.lon
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

    def _toggle_follow(self) -> None:
        """Toggle continuous auto-centre on or off."""
        self.auto_centre = not self.auto_centre
        self._update_follow_button()
        log.info("MapViewWindow[%s]: follow %s", self._uid, "ON" if self.auto_centre else "OFF")
        if self.auto_centre:
            self.view_lat = self.lat
            self.view_lon = self.lon
            self._last_tile_origin = None
            self._redraw_all(refetch=True)

    def _toggle_satellite(self) -> None:
        """Switch between OSM and satellite tile sources."""
        self.satellite_mode = not self.satellite_mode
        dpg.set_item_label(self.satellite_btn_tag,
                           "Map view" if self.satellite_mode else "Satellite")
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

    def _pan(self, dx: int, dy: int) -> None:
        """
        Pan the viewport by a fraction of its size.

        Disengages Follow mode on the first call.
        """
        if self.auto_centre:
            self.auto_centre = False
            self._update_follow_button()
            log.info("MapViewWindow[%s]: follow disengaged by pan", self._uid)
        pan_px = self.map_width * self.PAN_FRACTION * dx
        pan_py = self.map_height * self.PAN_FRACTION * dy
        cx, cy = self.latlon_to_pixel(self.view_lat, self.view_lon, self.zoom)
        new_lat, new_lon = self.pixel_to_latlon(cx + pan_px, cy + pan_py, self.zoom)
        self.view_lat = max(-85.0511, min(85.0511, new_lat))
        self.view_lon = new_lon
        self._redraw_all(refetch=True)
        self._update_diag()

    # -------------------------------------------------------------------------
    # External update API
    # -------------------------------------------------------------------------

    def update_location(self, lat: float, lon: float) -> None:
        """
        Update the rocket position and append a track point.

        Called by UIManager on every GPS fix. If Follow is enabled the
        viewport re-centres automatically.
        """
        # If GPS is invalid, return
        if lat == 0.0 or lon == 0.0:
            return

        self.lat = lat
        self.lon = lon
        self.track.append((lat, lon))
        if self.auto_centre:
            self.view_lat = lat
            self.view_lon = lon
            self.draw_map_tiles()
        self._redraw_all(refetch=False)

    def update_zoom(self, new_zoom: int) -> None:
        """Set the zoom level, clamped to [1, 19], and trigger a full redraw."""
        new_zoom = max(1, min(19, new_zoom))
        if new_zoom == self.zoom:
            return
        log.info("MapViewWindow[%s]: zoom %d → %d", self._uid, self.zoom, new_zoom)
        self.zoom = new_zoom
        self._last_tile_origin = None
        self._redraw_all(refetch=True)

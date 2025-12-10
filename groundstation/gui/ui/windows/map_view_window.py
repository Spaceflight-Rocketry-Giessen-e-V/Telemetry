import math
import webbrowser

import requests
import io
import os
from PIL import Image
import dearpygui.dearpygui as dpg


class MapViewWindow:
    zoom = 14
    #lat = 49.81099177491784
    #lon = 8.854836956089711
    lat = 50.591600181525635
    lon = 8.704157213218798
    tile_size = 256

    tex_ids = []                 # ((dx,dy), tex_id)
    drawlist_tag = "map_drawlist"
    marker_tag = "map_marker"
    polyline_tag = "track_polyline"

    track = []                   # list of (lat, lon)

    cache_folder = "cache/map_coords"

    # Helper ---------------------------------------------------------
    @classmethod
    def latlon_to_tile(cls, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
        return xtile, ytile

    @classmethod
    def latlon_to_pixel(cls, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2 ** zoom
        x = (lon + 180.0) / 360.0 * n * cls.tile_size
        y = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n * cls.tile_size
        return int(x), int(y)

    # Tile caching ---------------------------------------------------
    @classmethod
    def get_cached_tile_path(cls, x, y, z):
        folder = cls.cache_folder
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{z}_{x}_{y}.png")

    @classmethod
    def fetch_tile(cls, x, y, z):
        """Loads tile from cache or downloads it."""
        path = cls.get_cached_tile_path(x, y, z)

        # Load from cache
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception:
                pass  # corrupted? then re-download

        # Download
        url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        headers = {
            "User-Agent": "SRPOG/Meerkat Ground Station (raketenbau@fb07.uni-giessen.de)"
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        img.save(path)
        return img

    # UI -------------------------------------------------------------
    @classmethod
    def draw_ui(cls):
        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)
        map_size = cls.tile_size * 3
        contributor_height = 50

        with dpg.group(horizontal=True):

            # ----------------------------
            # LEFT SIDE: MAP
            # ----------------------------
            with dpg.child_window(
                label="Map",
                width=map_size,
                height=map_size + contributor_height
            ):
                cls.draw_map_tiles()

                with dpg.drawlist(
                    width=map_size,
                    height=map_size,
                    tag=cls.drawlist_tag
                ):
                    cls.redraw_tiles()
                    cls.draw_marker()
                    cls.draw_track_polyline()

                # OSM attribution as real hyperlink
                dpg.add_text("Map data ©")
                dpg.add_button(label="OpenStreetMap contributors", callback=lambda: webbrowser.open("https://www"
                                                                                                    ".openstreetmap.org/copyright"))

            # ----------------------------
            # RIGHT SIDE: Controls
            # ----------------------------
            with dpg.group():
                dpg.add_button(label="Zoom In", width=80, callback=lambda: cls.update_zoom(cls.zoom + 1))
                dpg.add_button(label="Zoom Out", width=80, callback=lambda: cls.update_zoom(cls.zoom - 1))

    # Draw and utilities -----------------------------------------------------
    @classmethod
    def draw_map_tiles(cls):
        """Creates textures for current center tiles"""
        cls.tex_ids.clear()

        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)
        x_start, y_start = xtile - 1, ytile - 1

        with dpg.texture_registry():
            for dx in range(3):
                for dy in range(3):
                    tx, ty = x_start + dx, y_start + dy
                    img = cls.fetch_tile(tx, ty, cls.zoom)

                    data = [c / 255 for px in img.getdata() for c in px]
                    tex_id = dpg.add_static_texture(cls.tile_size, cls.tile_size, data)
                    cls.tex_ids.append(((dx, dy), tex_id))

    @classmethod
    def redraw_tiles(cls):
        for (dx, dy), tex_id in cls.tex_ids:
            x0 = dx * cls.tile_size
            y0 = dy * cls.tile_size
            dpg.draw_image(
                tex_id,
                (x0, y0),
                (x0 + cls.tile_size, y0 + cls.tile_size),
                parent=cls.drawlist_tag
            )

    @classmethod
    def draw_marker(cls):
        abs_x, abs_y = cls.latlon_to_pixel(cls.lat, cls.lon, cls.zoom)
        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)

        center_x = xtile * cls.tile_size
        center_y = ytile * cls.tile_size
        offset_x = abs_x - (center_x - cls.tile_size)
        offset_y = abs_y - (center_y - cls.tile_size)

        dpg.draw_circle(
            (offset_x, offset_y),
            5,
            fill=(255, 0, 0, 255),
            color=(255, 0, 0, 255),
            parent=cls.drawlist_tag,
            tag=cls.marker_tag
        )

    @classmethod
    def draw_track_polyline(cls):
        if len(cls.track) < 2:
            return

        if not dpg.does_item_exist(cls.drawlist_tag):
            return

        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)
        cx = xtile * cls.tile_size
        cy = ytile * cls.tile_size

        points = []
        for lat, lon in cls.track:
            px, py = cls.latlon_to_pixel(lat, lon, cls.zoom)
            ox = float(px - (cx - cls.tile_size))
            oy = float(py - (cy - cls.tile_size))

            # Skip invalid points
            if math.isnan(ox) or math.isnan(oy) or math.isinf(ox) or math.isinf(oy):
                continue

            # Skip points outside visible map (optional but safer)
            if ox < 0 or oy < 0 or ox > cls.tile_size * 3 or oy > cls.tile_size * 3:
                continue

            points.append([ox, oy])  # <-- must be list[float], not tuple[int,int]

        if len(points) < 2:
            return

        dpg.draw_polyline(
            points,
            color=(0, 255, 0, 255),
            thickness=2,
            parent=cls.drawlist_tag
        )

    # Update Functions -------------------------------------------------------
    @classmethod
    def update_location(cls, lat, lon):
        cls.lat = lat
        cls.lon = lon
        cls.track.append((lat, lon))

        # Ensure drawlist exists
        if not dpg.does_item_exist(cls.drawlist_tag):
            return

        # Clear old drawings (tiles, marker, track)
        dpg.delete_item(cls.drawlist_tag, children_only=True)

        # Re-draw tiles
        cls.redraw_tiles()  # <-- already draws directly into drawlist

        # Re-draw track
        cls.draw_track_polyline()

        # Re-draw marker
        cls.draw_marker()

    @classmethod
    def update_zoom(cls, new_zoom):
        new_zoom = max(1, min(19, new_zoom))
        if new_zoom == cls.zoom:
            return

        cls.zoom = new_zoom

        # rebuild tile textures (cached if possible)
        cls.draw_map_tiles()

        # re-render map contents
        cls.update_location(cls.lat, cls.lon)



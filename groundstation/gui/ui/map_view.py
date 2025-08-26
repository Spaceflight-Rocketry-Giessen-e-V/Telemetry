import math
import requests
import io
from PIL import Image
import dearpygui.dearpygui as dpg

import ui.location


class Map:
    zoom = 12
    lat = 49.878708
    lon = 8.646927
    tile_size = 256
    tex_ids = []  # Stores map textures
    drawlist_tag = "map_drawlist"
    marker_tag = "map_marker"

    # Coordinate helper funcs
    @classmethod
    def latlon_to_tile(cls, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
        return xtile, ytile

    @classmethod
    def latlon_to_pixel(cls, lat, lon, zoom, tile_size=256):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = (lon + 180.0) / 360.0 * n * tile_size
        y = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n * tile_size
        return int(x), int(y)  # absolute pixel coords

    @classmethod
    def fetch_tile(cls, x, y, z):
        url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        headers = {
            "User-Agent": "SRPOG/Meerkat Ground Station (raketenbau@fb07.uni-giessen.de)"
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        return img

    @classmethod
    def draw_ui(cls):
        # Compute tile coords
        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)

        # Compute top-left corner of the 3x3 matrix
        x_start = xtile - 1
        y_start = ytile - 1

        map_size = cls.tile_size * 3
        map_size_contributors_offset = 50
        with dpg.group(horizontal=True):
            with dpg.child_window(label="Map", width=map_size, height=map_size + map_size_contributors_offset):
                # Map view
                cls.tex_ids.clear()
                with dpg.texture_registry():
                    for dx in range(3):
                        for dy in range(3):
                            tx = x_start + dx
                            ty = y_start + dy
                            img = cls.fetch_tile(tx, ty, cls.zoom)
                            width, height = img.size
                            data = [c / 255.0 for px in img.getdata() for c in px]
                            tex_id = dpg.add_static_texture(width, height, data)
                            cls.tex_ids.append(((dx, dy), tex_id))

                # Draw everything from drawlist
                with dpg.drawlist(width=map_size, height=map_size, tag=cls.drawlist_tag):
                    for (dx, dy), tex_id in cls.tex_ids:
                        x0 = dx * cls.tile_size
                        y0 = dy * cls.tile_size
                        dpg.draw_image(tex_id, (x0, y0), (x0 + cls.tile_size, y0 + cls.tile_size))

                    # Marker position
                    abs_x, abs_y = cls.latlon_to_pixel(cls.lat, cls.lon, cls.zoom)
                    center_x = xtile * cls.tile_size
                    center_y = ytile * cls.tile_size
                    offset_x = abs_x - (center_x - cls.tile_size)
                    offset_y = abs_y - (center_y - cls.tile_size)

                    dpg.draw_circle(
                        (offset_x, offset_y), 5,
                        color=(255, 0, 0, 255),
                        fill=(255, 0, 0, 255),
                        tag=cls.marker_tag
                    )

                # Attribution text outside the drawlist
                dpg.add_text("© OpenStreetMap contributors", color=(100, 100, 100, 255))

            # Location data
            ui.location.Location.draw_ui(100, map_size + map_size_contributors_offset)


    @classmethod
    def update_location(cls, lat, lon):
        # Update marker postion
        cls.lat = lat
        cls.lon = lon
        xtile, ytile = cls.latlon_to_tile(cls.lat, cls.lon, cls.zoom)

        abs_x, abs_y = cls.latlon_to_pixel(cls.lat, cls.lon, cls.zoom)
        center_x = xtile * cls.tile_size
        center_y = ytile * cls.tile_size
        offset_x = abs_x - (center_x - cls.tile_size)
        offset_y = abs_y - (center_y - cls.tile_size)

        dpg.configure_item(cls.marker_tag, center=(offset_x, offset_y))

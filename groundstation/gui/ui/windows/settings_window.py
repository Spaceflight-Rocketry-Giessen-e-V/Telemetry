"""
settings_window.py
------------------
Interactive settings panel rendered as a tab inside the main window.

Users can edit all configurable values (battery thresholds, RSSI thresholds,
flight event labels, and command groups/codes) through this panel. Every
change is written to ``settings.json`` immediately via SettingsManager when
the user clicks "Save All Settings".
"""

import logging

import dearpygui.dearpygui as dpg

from ui.settings_manager import settings

log = logging.getLogger(__name__)


class SettingsWindow:
    """Draws and manages the interactive Settings tab."""

    def __init__(self):
        self._bat_min_tag = "cfg_bat_min"
        self._bat_max_tag = "cfg_bat_max"
        self._bat_crit_tag = "cfg_bat_crit"

        self._rssi_min_tag = "cfg_rssi_min"
        self._rssi_max_tag = "cfg_rssi_max"
        self._rssi_warn_tag = "cfg_rssi_warn"

        # Built lazily in draw_ui once the event and command lists are known.
        self._event_tags: list[str] = []
        self._abort_tags: list[str] = []
        self._cmd_tags: list[dict] = []

    def draw_ui(self) -> None:
        """Draw the full settings panel inside the current DPG container."""
        log.debug("Drawing settings UI")

        with dpg.child_window(label="Settings", horizontal_scrollbar=False):
            dpg.add_text("⚙  Ground Station Settings", color=(255, 215, 0, 255))
            dpg.add_separator()
            dpg.add_spacer(height=6)

            self._draw_battery_section()
            dpg.add_spacer(height=10)
            self._draw_connection_section()
            dpg.add_spacer(height=10)
            self._draw_flight_events_section()
            dpg.add_spacer(height=10)
            self._draw_commands_section()
            dpg.add_spacer(height=14)

            dpg.add_button(
                label="Save All Settings",
                callback=self._save_all,
                height=36,
            )
            with dpg.theme() as save_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 120, 200, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 150, 230, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 90, 170, 255))
            dpg.bind_item_theme(dpg.last_item(), save_theme)

            dpg.add_spacer(height=6)
            dpg.add_text("", tag="settings_status_label")

    def _draw_battery_section(self) -> None:
        """Render battery voltage threshold inputs."""
        dpg.add_text("Battery Thresholds", color=(180, 220, 180, 255))
        dpg.add_separator()

        bat = settings.data.get("battery", {})

        with dpg.group(horizontal=True):
            dpg.add_text("Min Voltage (V):")
            dpg.add_input_float(
                tag=self._bat_min_tag,
                default_value=float(bat.get("voltage_min", 5.4)),
                width=100, step=0.1, format="%.2f",
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Max Voltage (V):")
            dpg.add_input_float(
                tag=self._bat_max_tag,
                default_value=float(bat.get("voltage_max", 8.4)),
                width=100, step=0.1, format="%.2f",
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Critical Voltage (V):")
            dpg.add_input_float(
                tag=self._bat_crit_tag,
                default_value=float(bat.get("voltage_critical", 5.6)),
                width=100, step=0.1, format="%.2f",
            )

    def _draw_connection_section(self) -> None:
        """Render RSSI / connection quality threshold inputs."""
        dpg.add_text("Connection / RSSI Thresholds", color=(180, 220, 180, 255))
        dpg.add_separator()

        conn = settings.data.get("connection", {})

        with dpg.group(horizontal=True):
            dpg.add_text("Min RSSI (dBm):")
            dpg.add_input_int(
                tag=self._rssi_min_tag,
                default_value=int(conn.get("rssi_min", -110)),
                width=100,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Max RSSI (dBm):")
            dpg.add_input_int(
                tag=self._rssi_max_tag,
                default_value=int(conn.get("rssi_max", -30)),
                width=100,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Warn RSSI (dBm):")
            dpg.add_input_int(
                tag=self._rssi_warn_tag,
                default_value=int(conn.get("rssi_warn", -90)),
                width=100,
            )

    def _draw_flight_events_section(self) -> None:
        """
        Render the editable flight-event list.

        Each event gets a text input for its label and a checkbox to mark it
        as an abort-level event. The ``abort_threshold`` index is derived
        automatically from the checkboxes when settings are saved.
        """
        dpg.add_text("Flight Events", color=(180, 220, 180, 255))
        dpg.add_separator()
        dpg.add_text(
            "Check 'Abort' to mark an event as an abort-level event (shown in red).",
            color=(180, 180, 180, 255),
        )
        dpg.add_spacer(height=4)

        fe_data = settings.data.get("flight_events", {})
        events = fe_data.get("events", [])
        abort_threshold = fe_data.get("abort_threshold", 14)

        self._event_tags.clear()
        self._abort_tags.clear()

        with dpg.table(
                header_row=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
                row_background=True,
        ):
            dpg.add_table_column(label="#", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="Label", width_stretch=True)
            dpg.add_table_column(label="Abort", width_fixed=True, init_width_or_weight=50)

            for i, evt in enumerate(events):
                label_tag = f"cfg_event_label_{i}"
                abort_tag = f"cfg_event_abort_{i}"
                # Derive abort state from threshold for backwards compatibility.
                is_abort = evt.get("is_abort", i >= abort_threshold)

                with dpg.table_row():
                    dpg.add_text(f"{i:02d}")
                    dpg.add_input_text(
                        tag=label_tag,
                        default_value=evt.get("label", ""),
                        width=-1,
                    )
                    dpg.add_checkbox(tag=abort_tag, default_value=is_abort)

                self._event_tags.append(label_tag)
                self._abort_tags.append(abort_tag)

    def _draw_commands_section(self) -> None:
        """
        Render the editable command groups.

        Each group has a name, and each command within has a display label and
        a single-character code sent over the serial link.
        """
        dpg.add_text("Commands", color=(180, 220, 180, 255))
        dpg.add_separator()
        dpg.add_spacer(height=4)

        cmd_data = settings.data.get("commands", {})
        groups = cmd_data.get("groups", [])

        self._cmd_tags.clear()

        for gi, grp in enumerate(groups):
            dpg.add_text(f"Group: {grp.get('group', '')}", color=(200, 200, 200, 255))

            with dpg.table(
                    header_row=True,
                    borders_innerH=True, borders_outerH=True,
                    borders_innerV=True, borders_outerV=True,
                    row_background=True,
            ):
                dpg.add_table_column(label="Label", width_stretch=True)
                dpg.add_table_column(label="Code", width_fixed=True, init_width_or_weight=60)

                for ci, cmd in enumerate(grp.get("commands", [])):
                    lbl_tag = f"cfg_cmd_{gi}_{ci}_label"
                    code_tag = f"cfg_cmd_{gi}_{ci}_code"

                    with dpg.table_row():
                        dpg.add_input_text(
                            tag=lbl_tag,
                            default_value=cmd.get("label", ""),
                            width=-1,
                        )
                        dpg.add_input_text(
                            tag=code_tag,
                            default_value=cmd.get("code", ""),
                            width=-1,
                        )

                    self._cmd_tags.append({
                        "group_idx": gi,
                        "cmd_idx": ci,
                        "label_tag": lbl_tag,
                        "code_tag": code_tag,
                    })

            dpg.add_spacer(height=6)

    def _save_all(self) -> None:
        """Collect all widget values and persist them through SettingsManager."""
        log.info("User triggered 'Save All Settings'")

        try:
            self._save_battery()
            self._save_connection()
            self._save_flight_events()
            self._save_commands()

            dpg.set_value("settings_status_label", "✓  Settings saved successfully.")
            log.info("All settings saved successfully")

        except Exception as exc:  # noqa: BLE001
            msg = f"Error saving settings: {exc}"
            dpg.set_value("settings_status_label", f"✗  {msg}")
            log.error(msg, exc_info=True)

    def _save_battery(self) -> None:
        bat_min = dpg.get_value(self._bat_min_tag)
        bat_max = dpg.get_value(self._bat_max_tag)
        bat_crit = dpg.get_value(self._bat_crit_tag)

        if not (bat_min < bat_crit < bat_max):
            raise ValueError(
                f"Battery voltages must satisfy min({bat_min}) < critical({bat_crit}) < max({bat_max})"
            )

        settings.set_section("battery", {
            "voltage_min": bat_min,
            "voltage_max": bat_max,
            "voltage_critical": bat_crit,
        })
        log.debug("Battery settings saved: min=%.2f, max=%.2f, critical=%.2f", bat_min, bat_max, bat_crit)

    def _save_connection(self) -> None:
        rssi_min = dpg.get_value(self._rssi_min_tag)
        rssi_max = dpg.get_value(self._rssi_max_tag)
        rssi_warn = dpg.get_value(self._rssi_warn_tag)

        if not (rssi_min < rssi_warn < rssi_max):
            raise ValueError(
                f"RSSI values must satisfy min({rssi_min}) < warn({rssi_warn}) < max({rssi_max})"
            )

        settings.set_section("connection", {
            "rssi_min": rssi_min,
            "rssi_max": rssi_max,
            "rssi_warn": rssi_warn,
        })
        log.debug("Connection settings saved: min=%d, max=%d, warn=%d", rssi_min, rssi_max, rssi_warn)

    def _save_flight_events(self) -> None:
        events = []
        first_abort_idx = None

        for i, (lbl_tag, abort_tag) in enumerate(zip(self._event_tags, self._abort_tags)):
            label = dpg.get_value(lbl_tag).strip()
            is_abort = dpg.get_value(abort_tag)
            events.append({"label": label, "is_abort": is_abort})

            if is_abort and first_abort_idx is None:
                first_abort_idx = i

        # abort_threshold is the index of the first abort event, or len(events) if none.
        abort_threshold = first_abort_idx if first_abort_idx is not None else len(events)

        settings.set_section("flight_events", {
            "abort_threshold": abort_threshold,
            "events": events,
        })
        log.debug("Flight events saved: %d events, abort_threshold=%d", len(events), abort_threshold)

    def _save_commands(self) -> None:
        """Rebuild the groups list from the tagged widgets and persist it."""
        groups_raw = settings.data.get("commands", {}).get("groups", [])
        groups_out: list[dict] = [
            {"group": g.get("group", ""), "commands": [None] * len(g.get("commands", []))}
            for g in groups_raw
        ]

        for tag_info in self._cmd_tags:
            gi = tag_info["group_idx"]
            ci = tag_info["cmd_idx"]
            label = dpg.get_value(tag_info["label_tag"]).strip()
            code = dpg.get_value(tag_info["code_tag"]).strip()
            groups_out[gi]["commands"][ci] = {"label": label, "code": code}

        settings.set_section("commands", {"groups": groups_out})
        log.debug("Command settings saved: %d groups", len(groups_out))

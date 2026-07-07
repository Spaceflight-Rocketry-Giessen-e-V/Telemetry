"""
commands_window.py
------------------
Command-dispatch panel with a two-step confirm/abort flow.

Command groups and their serial codes come from SettingsManager, so they can be
reconfigured from the Settings tab. Modular widget: sends via ``ctx.serial``
(the SerialService) instead of holding a controller reference, rebuilds its
buttons on ``settings/commands/changed``, and namespaces all tags per instance.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.core import topics
from ui.core.services import ServiceHub
from ui.core.widget_base import Widget

log = logging.getLogger(__name__)


class CommandsWindow(Widget):
    """Commands panel with a two-step confirm/abort flow, driven by SerialService."""

    TYPE_ID = "commands"
    DISPLAY_NAME = "Commands"
    DEFAULT_CELLS = (3, 6)
    MIN_CELLS = (3, 4)

    def __init__(self, iid: str, ctx: ServiceHub, config: dict | None = None):
        super().__init__(iid, ctx, config)
        self._selected_cmd: str | None = None
        self._selected_label: str | None = None
        self._themes: list[int] = []

    def build(self, width: int, height: int) -> None:
        dpg.add_text(self.config.get("title", "Commands"), color=(255, 255, 0))
        dpg.add_separator()
        dpg.add_spacer(height=4)

        dpg.add_group(tag=self.tag("groups"))
        self._render_buttons()

        dpg.add_separator()
        dpg.add_spacer(height=4)
        dpg.add_text("Selected: -", tag=self.tag("pending"))
        dpg.add_spacer(height=4)

        with dpg.group(horizontal=True):
            dpg.add_button(label="✓ Send", width=100, show=False, tag=self.tag("confirm"),
                           callback=self._confirm)
            self._bind_theme(self.tag("confirm"), (40, 160, 40, 255), (60, 200, 60, 255), (20, 120, 20, 255))
            dpg.add_button(label="✗ Abort", width=100, show=False, tag=self.tag("abort"),
                           callback=self._abort)
            self._bind_theme(self.tag("abort"), (180, 40, 40, 255), (220, 60, 60, 255), (140, 20, 20, 255))

        dpg.add_spacer(height=6)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text("Status:")
            dpg.add_text("idle", tag=self.tag("status"))

        self.subscribe(topics.settings_changed("commands"), lambda _=None: self._render_buttons())

    def _bind_theme(self, item, base, hover, active) -> None:
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, base)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active)
        self._themes.append(theme)
        dpg.bind_item_theme(item, theme)

    def _render_buttons(self) -> None:
        holder = self.tag("groups")
        dpg.delete_item(holder, children_only=True)
        groups = self.ctx.settings.data.get("commands", {}).get("groups", [])
        for grp in groups:
            dpg.add_text(grp.get("group", ""), color=(180, 180, 180, 255), parent=holder)
            row = dpg.add_group(horizontal=True, parent=holder)
            commands = grp.get("commands", [])
            for cmd in commands:
                label = cmd.get("label", "?")
                code = cmd.get("code", "")
                dpg.add_button(
                    label=f"{label} ({code})",
                    width=-1 if len(commands) == 1 else 0,
                    height=30,
                    parent=row,
                    callback=lambda s, a, u: self._preselect(u[0], u[1]),
                    user_data=(label, code),
                )
            dpg.add_spacer(height=4, parent=holder)

    def _preselect(self, label: str, command: str) -> None:
        self._selected_cmd = command
        self._selected_label = label
        dpg.set_value(self.tag("pending"), f"Selected: {label} ({command!r})")
        dpg.configure_item(self.tag("confirm"), show=True)
        dpg.configure_item(self.tag("abort"), show=True)
        dpg.set_value(self.tag("status"), "pending confirmation")

    def _confirm(self) -> None:
        if self._selected_cmd is not None:
            self._send(self._selected_label, self._selected_cmd)
        self._clear_selection()

    def _abort(self) -> None:
        self._clear_selection()
        dpg.set_value(self.tag("status"), "aborted")

    def _clear_selection(self) -> None:
        self._selected_cmd = None
        self._selected_label = None
        dpg.set_value(self.tag("pending"), "Selected: -")
        dpg.configure_item(self.tag("confirm"), show=False)
        dpg.configure_item(self.tag("abort"), show=False)

    def _send(self, label: str, command: str) -> None:
        serial = self.ctx.serial
        if serial is None or not serial.is_connected():
            dpg.set_value(self.tag("status"), "not connected")
            log.warning("CommandsWindow[%s]: cannot send '%s' — not connected", self.iid, label)
            return
        try:
            serial.send_command(command)
            dpg.set_value(self.tag("status"), f"sent '{label}' ({command!r})")
            log.info("CommandsWindow[%s]: sent '%s' (%r)", self.iid, label, command)
        except Exception as exc:  # noqa: BLE001
            dpg.set_value(self.tag("status"), f"Error: {exc}")
            log.error("CommandsWindow[%s]: error sending '%s': %s", self.iid, label, exc, exc_info=True)

    def destroy(self) -> None:
        for theme in self._themes:
            if dpg.does_item_exist(theme):
                dpg.delete_item(theme)
        self._themes.clear()
        super().destroy()

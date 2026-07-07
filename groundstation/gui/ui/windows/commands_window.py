"""
commands_window.py
------------------
Command-dispatch panel with a two-step confirm/abort flow.

Command groups and their serial codes are loaded from SettingsManager so
they can be reconfigured from the Settings tab without modifying source code.

Flow: user clicks a command button → the selection is previewed → user
confirms (Send) or cancels (Abort) → the command is dispatched via the
ComMonitorController's serial link.
"""

import logging

import dearpygui.dearpygui as dpg

from ui.settings_manager import settings

log = logging.getLogger(__name__)


class CommandsWindow:
    """Renders the commands panel and manages the two-step confirm/abort flow."""

    def __init__(self, receiver):
        """
        Parameters
        ----------
        receiver:
            A :class:`ComMonitorController` instance whose ``controller``
            attribute exposes ``is_connected()`` and ``send_command()``.
        """
        self.receiver_controller = receiver

        self.status_label: int | None = None
        self._pending_label: int | None = None
        self._confirm_btn: int | None = None
        self._abort_btn: int | None = None

        self._selected_cmd: str | None = None
        self._selected_label: str | None = None

        log.debug("%s: initialised", self.__class__.__name__)

    def _preselect(self, label: str, command: str) -> None:
        """Store the chosen command and reveal the confirm/abort buttons."""
        self._selected_cmd = command
        self._selected_label = label
        log.debug("CommandsWindow: pre-selected '%s' (%r)", label, command)

        dpg.configure_item(self._pending_label, default_value=f"Selected: {label} ({repr(command)})")
        dpg.configure_item(self._confirm_btn, show=True)
        dpg.configure_item(self._abort_btn, show=True)
        dpg.configure_item(self.status_label, default_value="pending confirmation")

    def _confirm(self) -> None:
        """Dispatch the pre-selected command and reset the selection state."""
        if self._selected_cmd is not None:
            self.send(self._selected_label, self._selected_cmd)
        self._clear_selection()

    def _abort(self) -> None:
        """Cancel the pending selection without sending."""
        log.info("CommandsWindow: send aborted for '%s'", self._selected_label)
        self._clear_selection()
        dpg.configure_item(self.status_label, default_value="aborted")

    def _clear_selection(self) -> None:
        """Reset internal state and hide the confirm/abort buttons."""
        self._selected_cmd = None
        self._selected_label = None
        dpg.configure_item(self._pending_label, default_value="Selected: -")
        dpg.configure_item(self._confirm_btn, show=False)
        dpg.configure_item(self._abort_btn, show=False)

    def send(self, label: str, command: str) -> None:
        """
        Dispatch *command* over the serial link.

        Checks that a controller is present and connected before attempting
        the send. Updates the status label with the outcome.
        """
        controller = self.receiver_controller.controller
        if not controller or not controller.is_connected():
            log.warning("CommandsWindow: cannot send '%s' — not connected", label)
            dpg.configure_item(self.status_label, default_value="not connected")
            return

        try:
            controller.send_command(command)
            msg = f"sent '{label}' ({repr(command)})"
            dpg.configure_item(self.status_label, default_value=msg)
            log.info("CommandsWindow: sent command '%s' (%r)", label, command)
        except Exception as exc:  # noqa: BLE001
            err = f"Error: {exc}"
            dpg.configure_item(self.status_label, default_value=err)
            log.error("CommandsWindow: error sending '%s': %s", label, exc, exc_info=True)

    def draw_ui(
            self,
            window_width: int = 300,
            window_height: int = 600,
            button_height: int = 30,
    ) -> None:
        """
        Build the commands child-window.

        Command groups are loaded from settings, so this reflects any changes
        saved in the Settings tab (requires a UI rebuild or restart to apply).
        """
        log.debug("CommandsWindow: drawing UI (%dx%d)", window_width, window_height)

        cmd_data = settings.data.get("commands", {})
        groups = cmd_data.get("groups", [])
        log.debug("CommandsWindow: loaded %d command groups from settings", len(groups))

        with dpg.child_window(label="Commands", width=window_width, height=window_height):
            dpg.add_text("Commands", color=(255, 255, 0))
            dpg.add_separator()
            dpg.add_spacer(height=4)

            for grp in groups:
                group_label = grp.get("group", "")
                commands = grp.get("commands", [])

                dpg.add_text(group_label, color=(180, 180, 180, 255))

                with dpg.group(horizontal=True):
                    for cmd in commands:
                        btn_label = cmd.get("label", "?")
                        code = cmd.get("code", "")
                        dpg.add_button(
                            label=f"{btn_label} ({code})",
                            # Stretch to full width when the group contains only one button.
                            width=-1 if len(commands) == 1 else 0,
                            height=button_height,
                            callback=lambda s, a, u: self._preselect(u[0], u[1]),
                            user_data=(btn_label, code),
                        )

                dpg.add_spacer(height=4)

            dpg.add_separator()
            dpg.add_spacer(height=4)

            self._pending_label = dpg.add_text("Selected: -")
            dpg.add_spacer(height=4)

            with dpg.group(horizontal=True):
                self._confirm_btn = dpg.add_button(
                    label="✓ Send",
                    width=100,
                    callback=self._confirm,
                    show=False,
                )
                with dpg.theme() as confirm_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 160, 40, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 200, 60, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 120, 20, 255))
                dpg.bind_item_theme(self._confirm_btn, confirm_theme)

                self._abort_btn = dpg.add_button(
                    label="✗ Abort",
                    width=100,
                    callback=self._abort,
                    show=False,
                )
                with dpg.theme() as abort_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 40, 40, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (220, 60, 60, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (140, 20, 20, 255))
                dpg.bind_item_theme(self._abort_btn, abort_theme)

            dpg.add_spacer(height=6)
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_text("Status:")
                self.status_label = dpg.add_text("idle")

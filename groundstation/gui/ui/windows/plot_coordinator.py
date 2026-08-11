"""
plot_coordinator.py
-------------------
Central Stop / Resume / Reset control for all live plots at once.

The plot windows (AltitudeWindow, AccelerationWindow) register their class
objects here, and every plot's Stop/Reset button routes through this
coordinator. A single click therefore freezes, resumes, or clears **all**
plots together and keeps their button labels in sync.

Reset hooks let the owner reset extra state on a reset — e.g. UIManager
registers a hook that restarts the mission clock so the plot time axis
returns to zero.
"""

import logging

log = logging.getLogger(__name__)


class PlotCoordinator:
    """Fan Stop/Resume/Reset out to every registered plot class at once."""

    _plots: list = []
    _reset_hooks: list = []
    active: bool = True

    @classmethod
    def register(cls, plot_cls) -> None:
        """Register a plot class exposing ``stop_plot``/``resume_plot``/``reset_plot``."""
        if plot_cls not in cls._plots:
            cls._plots.append(plot_cls)

    @classmethod
    def add_reset_hook(cls, hook) -> None:
        """Register a callable to run after every :py:meth:`reset_all`."""
        if hook not in cls._reset_hooks:
            cls._reset_hooks.append(hook)

    @classmethod
    def toggle(cls) -> None:
        """Stop all plots if currently running, resume all if stopped."""
        if cls.active:
            cls.stop_all()
        else:
            cls.resume_all()

    @classmethod
    def stop_all(cls) -> None:
        """Freeze every registered plot."""
        cls.active = False
        for plot in cls._plots:
            plot.stop_plot()
        log.info("PlotCoordinator: all plots stopped")

    @classmethod
    def resume_all(cls) -> None:
        """Resume every registered plot."""
        cls.active = True
        for plot in cls._plots:
            plot.resume_plot()
        log.info("PlotCoordinator: all plots resumed")

    @classmethod
    def reset_all(cls) -> None:
        """Clear every registered plot and run the reset hooks (e.g. mission clock)."""
        cls.active = True
        for plot in cls._plots:
            plot.reset_plot()
        for hook in cls._reset_hooks:
            try:
                hook()
            except Exception:  # noqa: BLE001
                log.error("PlotCoordinator: reset hook failed", exc_info=True)
        log.info("PlotCoordinator: all plots reset")

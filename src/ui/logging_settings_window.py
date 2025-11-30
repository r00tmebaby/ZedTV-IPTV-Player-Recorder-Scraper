"""PySimpleGUI window for logging settings."""

from __future__ import annotations

import logging

from core.config import ICON
from core.logging_settings import DEFAULT_LOGGING_CONFIG, LoggingSettings

from . import PySimpleGUI as sg

_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

log = logging.getLogger("ui.logging_settings_window")


def _show_logging_settings_window(current: LoggingSettings) -> bool:
    """Show the logging settings dialog.
    Returns True if settings were changed and saved, False otherwise.
    Never raises; on error it logs and shows a popup, then returns False.
    """
    try:
        if current is None:
            log.warning("LoggingSettings instance is None; creating a new one")
            current = LoggingSettings()
        cfg = current.settings
        layout = [
            [
                sg.Text(
                    "Logging Settings",
                    font=("Arial", 16, "bold"),
                    pad=((0, 0), (10, 15)),
                )
            ],
            [sg.HorizontalSeparator()],
            # Log Level
            [
                sg.Text(
                    "Log Configuration",
                    font=("Arial", 12, "bold"),
                    pad=((0, 0), (15, 10)),
                )
            ],
            [
                sg.Text("Log Level:", size=(22, 1), pad=((10, 10), (5, 5))),
                sg.Combo(
                    _LEVELS,
                    default_value=cfg.level,
                    key="_level_",
                    readonly=True,
                    size=(18, 1),
                ),
            ],
            [
                sg.Text(
                    "Controls verbosity (DEBUG is most verbose)",
                    text_color="gray",
                    font=("Arial", 9),
                    pad=((10, 10), (0, 10)),
                )
            ],
            [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
            # File Management
            [
                sg.Text(
                    "File Management",
                    font=("Arial", 12, "bold"),
                    pad=((0, 0), (10, 10)),
                )
            ],
            [
                sg.Text(
                    "Max File Size (MB):", size=(22, 1), pad=((10, 10), (5, 5))
                ),
                sg.Spin(
                    [i for i in range(1, 101)],
                    initial_value=cfg.max_file_size_mb,
                    key="_max_file_size_",
                    size=(10, 1),
                ),
            ],
            [
                sg.Text(
                    "Rotate when a log reaches this size",
                    text_color="gray",
                    font=("Arial", 9),
                    pad=((10, 10), (0, 10)),
                )
            ],
            [
                sg.Text(
                    "Backup Files Count:", size=(22, 1), pad=((10, 10), (5, 5))
                ),
                sg.Spin(
                    [i for i in range(1, 51)],
                    initial_value=cfg.backup_count,
                    key="_backup_count_",
                    size=(10, 1),
                ),
            ],
            [
                sg.Text(
                    "Number of rotated log files kept",
                    text_color="gray",
                    font=("Arial", 9),
                    pad=((10, 10), (0, 10)),
                )
            ],
            [
                sg.Text(
                    "Retention (days):", size=(22, 1), pad=((10, 10), (5, 5))
                ),
                sg.Spin(
                    [i for i in range(0, 366)],
                    initial_value=cfg.retention_days,
                    key="_retention_days_",
                    size=(10, 1),
                ),
            ],
            [
                sg.Text(
                    "Delete log files older than N days (0 = keep all)",
                    text_color="gray",
                    font=("Arial", 9),
                    pad=((10, 10), (0, 10)),
                )
            ],
            [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
            # Output Options
            [
                sg.Text(
                    "Output Options",
                    font=("Arial", 12, "bold"),
                    pad=((0, 0), (10, 10)),
                )
            ],
            [
                sg.Checkbox(
                    "Mirror to Console",
                    default=cfg.console_enabled,
                    key="_console_enabled_",
                    pad=((10, 10), (5, 5)),
                ),
            ],
            [
                sg.Text(
                    "Also print logs to stdout",
                    text_color="gray",
                    font=("Arial", 9),
                    pad=((10, 10), (0, 10)),
                )
            ],
            [sg.HorizontalSeparator(pad=((0, 0), (15, 15)))],
            # Action Buttons - Right aligned with proper spacing
            [
                sg.Button(
                    "Restore Defaults",
                    key="_restore_",
                    size=(15, 1),
                    pad=((10, 5), (5, 10)),
                ),
                sg.Push(),
                sg.Button(
                    "Cancel",
                    key="_cancel_",
                    size=(10, 1),
                    pad=((5, 5), (5, 10)),
                ),
                sg.Button(
                    "Save",
                    key="_save_",
                    button_color=("white", "green"),
                    size=(10, 1),
                    pad=((5, 10), (5, 10)),
                ),
            ],
            [
                sg.Text(
                    "Note: Settings apply on next application startup",
                    font=("Arial", 9, "italic"),
                    text_color="orange",
                    pad=((10, 10), (0, 15)),
                )
            ],
        ]

        win = sg.Window(
            "Logging Settings",
            layout,
            icon=ICON,
            modal=True,
            finalize=True,
            keep_on_top=True,
        )
        changed = False
        while True:
            ev, vals = win.read()
            if ev in (sg.WIN_CLOSED, "_cancel_"):
                log.debug("Logging settings dialog cancelled")
                break
            if ev == "_restore_":
                log.info("Restoring default logging settings")
                try:
                    win["_level_"].update(DEFAULT_LOGGING_CONFIG.level)
                    win["_max_file_size_"].update(
                        DEFAULT_LOGGING_CONFIG.max_file_size_mb
                    )
                    win["_backup_count_"].update(
                        DEFAULT_LOGGING_CONFIG.backup_count
                    )
                    win["_retention_days_"].update(
                        DEFAULT_LOGGING_CONFIG.retention_days
                    )
                    win["_console_enabled_"].update(
                        DEFAULT_LOGGING_CONFIG.console_enabled
                    )
                    sg.popup(
                        "Defaults restored (remember to Save)",
                        keep_on_top=True,
                    )
                except Exception as e:
                    log.exception("Failed to restore defaults: %s", e)
                    sg.popup_error(
                        f"Failed to restore defaults: {e}", keep_on_top=True
                    )
            if ev == "_save_":
                try:
                    log.info("Saving logging settings")
                    current.update(
                        level=str(vals.get("_level_", cfg.level)),
                        max_file_size_mb=int(
                            vals.get("_max_file_size_", cfg.max_file_size_mb)
                            or cfg.max_file_size_mb
                        ),
                        backup_count=int(
                            vals.get("_backup_count_", cfg.backup_count)
                            or cfg.backup_count
                        ),
                        retention_days=int(
                            vals.get("_retention_days_", cfg.retention_days)
                            or cfg.retention_days
                        ),
                        console_enabled=bool(
                            vals.get("_console_enabled_", cfg.console_enabled)
                        ),
                    )
                    changed = True
                    sg.popup(
                        "Logging settings saved. They apply on next startup.",
                        keep_on_top=True,
                    )
                    break
                except Exception as e:
                    log.exception("Failed to save logging settings: %s", e)
                    sg.popup_error(
                        f"Failed to save logging settings: {e}",
                        keep_on_top=True,
                    )
        win.close()
        return changed
    except Exception as e:
        log.exception("Unexpected error in logging settings window: %s", e)
        try:
            sg.popup_error(f"Logging Settings error: {e}", keep_on_top=True)
        except Exception:
            pass
        return False

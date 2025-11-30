"""
Splash screen module for application initialization feedback.

This module manages the display of a loading splash screen during app startup.
"""

import logging
from typing import Any, Optional

from ui.layout import sg

# Module logger
log = logging.getLogger(__name__)


class SplashScreen:
    """
    Manages the application splash screen during initialization.

    Attributes:
        window: Splash screen window reference
    """

    def __init__(self):
        """Initialize the splash screen."""
        log.debug("Initializing splash screen")
        self.window: Optional[Any] = None

    def show(self) -> bool:
        """
        Display the splash screen.

        Returns:
            True if splash screen was created successfully, False otherwise
        """
        log.info("Showing splash screen")
        try:
            self.window = sg.Window(
                "Loading",
                [
                    [
                        sg.Text(
                            "ZedTV IPTV Player",
                            font=("Arial", 16, "bold"),
                            justification="center",
                        )
                    ],
                    [
                        sg.Text(
                            "Initializing...",
                            font=("Arial", 10),
                            justification="center",
                            key="_status_",
                            size=(40, 1),
                        )
                    ],
                    [
                        sg.ProgressBar(
                            100,
                            orientation="h",
                            size=(30, 10),
                            key="_progress_",
                            bar_color=("green", "white"),
                        )
                    ],
                ],
                no_titlebar=True,
                keep_on_top=True,
                grab_anywhere=True,
                finalize=True,
                modal=False,
                alpha_channel=0.95,
            )
            self.update_progress(20)
            self.window.refresh()
            log.info("Splash screen displayed")
            return True

        except Exception as e:
            log.error("Failed to create splash screen: %s", e)
            self.window = None
            return False

    def update_progress(
        self, value: int, status: Optional[str] = None
    ) -> None:
        """
        Update splash screen progress.

        Args:
            value: Progress value (0-100)
            status: Optional status message to display
        """
        if not self.window:
            return

        try:
            self.window["_progress_"].update(value)
            if status:
                self.window["_status_"].update(status)
            self.window.refresh()
            log.debug(
                "Splash progress updated: %d%% - %s", value, status or ""
            )
        except Exception as e:
            log.error("Failed to update splash screen: %s", e)

    def close(self) -> None:
        """Close the splash screen."""
        if not self.window:
            return

        try:
            import time

            self.update_progress(100)
            time.sleep(0.1)  # Brief pause to show 100%
            self.window.close()
            log.info("Splash screen closed")
        except Exception as e:
            log.error("Failed to close splash screen: %s", e)
        finally:
            self.window = None

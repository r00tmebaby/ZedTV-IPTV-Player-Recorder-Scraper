"""
Background image management for the video player canvas.

This module handles displaying and clearing background images on the video canvas.
"""

import logging
from pathlib import Path
from typing import Any, Optional
import sys

from PIL import Image, ImageTk

# Module logger
log = logging.getLogger(__name__)


class BackgroundManager:
    """
    Manages background image display on the video canvas.

    Attributes:
        bg_image_id: Canvas image ID reference
        bg_image_photo: PhotoImage reference (must be kept alive)
        canvas_element: Canvas element reference
    """

    def __init__(self, canvas_element: Any):
        """
        Initialize the background manager.

        Args:
            canvas_element: PySimpleGUI Canvas element
        """
        log.debug("Initializing BackgroundManager")
        self.bg_image_id: Optional[int] = None
        self.bg_image_photo: Optional[ImageTk.PhotoImage] = None
        self.canvas_element = canvas_element

    def get_background_path(self) -> Path:
        """
        Get the path to the background image file.

        Returns:
            Path to background.jpg file
        """
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent.parent
        path = base / "data" / "thumbnails" / "background.jpg"
        log.debug("Background image path: %s", path)
        return path

    def show_background(self, player_instance: Optional[Any] = None) -> None:
        """
        Display background image on the canvas.

        Args:
            player_instance: Optional player instance to check playback state
        """
        log.debug("Attempting to show background")

        # Don't show background if player is currently playing
        try:
            if player_instance and player_instance.players and player_instance.players.is_playing():
                log.debug("Player is playing, skipping background display")
                return
        except Exception as e:
            log.debug("Failed to check player state: %s", e)

        try:
            canvas_widget = self.canvas_element.Widget
        except Exception as e:
            log.error("Failed to get canvas widget: %s", e)
            return

        try:
            # Clear any existing canvas content
            canvas_widget.delete("all")
            log.debug("Cleared canvas")

            # Check if background image exists
            path = self.get_background_path()
            if not path.exists():
                log.warning("Background image not found at: %s", path)
                return

            # Get canvas dimensions
            cw = canvas_widget.winfo_width() or 690
            ch = canvas_widget.winfo_height() or 390
            if cw <= 5 or ch <= 5:
                cw, ch = 690, 390
            log.debug("Canvas dimensions: %dx%d", cw, ch)

            # Choose best available resampling filter
            Resampling = getattr(Image, "Resampling", None)
            _RES_LANCZOS = getattr(
                Image, "LANCZOS", getattr(Resampling, "LANCZOS", Image.BICUBIC) if Resampling else Image.BICUBIC
            )
            log.debug("Using resampling filter: %s", _RES_LANCZOS)

            # Load, convert, and resize image
            img = Image.open(path).convert("RGB").resize((cw, ch), _RES_LANCZOS)
            self.bg_image_photo = ImageTk.PhotoImage(img)

            # Display image on canvas
            self.bg_image_id = canvas_widget.create_image(cw // 2, ch // 2, image=self.bg_image_photo)
            log.info("Background image displayed successfully")

        except Exception as e:
            log.error("Failed to render background: %s", e, exc_info=True)

    def clear_background(self) -> None:
        """Clear the background image from the canvas."""
        log.debug("Clearing background")
        try:
            canvas_widget = self.canvas_element.Widget
            canvas_widget.delete("all")
            self.bg_image_id = None
            self.bg_image_photo = None
            log.debug("Background cleared successfully")
        except Exception as e:
            log.error("Failed to clear background: %s", e)

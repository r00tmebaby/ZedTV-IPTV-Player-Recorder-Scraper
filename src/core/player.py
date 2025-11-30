"""
Player module for VLC media player functionality.

This module handles all VLC player operations including initialization,
playback control, fullscreen management, and media handling.
"""

import logging
import tkinter as tk
from sys import platform as platform
from typing import Optional, Any, Callable
import shutil
import subprocess
import os

from .vlc_settings import VLCSettings
from src.media import player


log = logging.getLogger(__name__)


class _DummyMediaPlayer:
    """Dummy media player for fallback when VLC is not available."""

    def __getattr__(self, name: str) -> Any:
        """
        Return no-op function for any attribute access.

        Args:
            name: Attribute name

        Returns:
            No-op function that accepts any arguments
        """
        log.debug("DummyMediaPlayer: accessing attribute '%s' (no-op)", name)

        def _noop(*a, **k):
            return None

        return _noop


class _DummyInstance:
    """Dummy VLC instance for fallback when VLC is not available."""

    def media_player_new(self) -> _DummyMediaPlayer:
        """
        Create a new dummy media player.

        Returns:
            Dummy media player instance
        """
        log.debug("DummyInstance: creating dummy media player")
        return _DummyMediaPlayer()

    def media_new(self, m: str) -> str:
        """
        Create dummy media object.

        Args:
            m: Media URL or path

        Returns:
            The input media string
        """
        log.debug("DummyInstance: creating dummy media for '%s'", m)
        return m


def launch_vlc_external(url: str, vlc_path: str = None) -> None:
    """
    Launch VLC media player externally with the given URL.

    Falls back to system default handler if VLC is not found.

    Args:
        url: Media URL to play
        vlc_path: Optional custom path to VLC executable
    """
    log.info("Attempting to launch external VLC for URL: %s", url)
    try:
        # Check common installation directories if VLC is not in PATH
        exe = vlc_path or shutil.which("vlc")
        if not exe:
            common_paths = [
                r"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
                r"C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    exe = path
                    log.debug("Found VLC executable at common path: %s", exe)
                    break

        if exe:
            log.debug("Using VLC executable at: %s", exe)
            subprocess.Popen([exe, url], shell=False)
            log.info("Successfully launched external VLC")
            return
        else:
            log.warning("VLC executable not found in PATH or common directories")
    except Exception as e:
        log.error("Failed to launch VLC: %s", e)

    # Fallback: open via default system handler
    try:
        log.debug("Attempting fallback to system default handler")
        os.startfile(url)
        log.info("Opened URL with system default handler")
    except Exception as e:
        log.error("Failed to open URL with system handler: %s", e)


class Player:
    """
    VLC player wrapper class for managing media playback.

    Attributes:
        vlc_instance: VLC instance object
        players: VLC media player object
        settings: VLC settings object
        fullscreen_window: Fullscreen window reference
        is_fullscreen: Fullscreen state flag
        _channels_master: Master channel list
        _bg_photo: Background photo reference
    """

    vlc_instance: Any = None
    players: Any = None
    settings: Optional[VLCSettings] = None
    fullscreen_window: Optional[tk.Toplevel] = None
    is_fullscreen: bool = False
    _channels_master: Optional[list] = None
    _bg_photo: Any = None

    @classmethod
    def initialize(cls, vlc_settings: VLCSettings) -> None:
        """
        Initialize the VLC player with settings.

        Args:
            vlc_settings: VLC settings object
        """
        log.info("Initializing VLC player")
        cls.settings = vlc_settings
        vlc_args = vlc_settings.get_vlc_args()
        log.debug("VLC arguments: %s", vlc_args)

        # Diagnostic: show where player.find_lib() locates libvlc
        try:
            lib_info = player.find_lib()
            log.debug("VLC find_lib() returned: %s", lib_info)
            # Dump PATH prefix for diagnostics
            try:
                path_prefix = os.environ.get("PATH", "")[:400]
                log.debug("PATH (prefix): %s", path_prefix)
                vlc_lib_path = os.environ.get("PYTHON_VLC_LIB_PATH")
                vlc_module_path = os.environ.get("PYTHON_VLC_MODULE_PATH")
                log.debug("PYTHON_VLC_LIB_PATH=%s PYTHON_VLC_MODULE_PATH=%s", vlc_lib_path, vlc_module_path)
            except Exception as e:
                log.debug("Failed to log PATH diagnostics: %s", e)
        except Exception as e:
            log.debug("player.find_lib() diagnostic failed: %s", e)

        # Try to create VLC instance
        try:
            cls.vlc_instance = player.Instance(*vlc_args)
            log.info("VLC Instance created successfully")
        except Exception as e:
            log.warning("VLC Instance creation failed: %s - using dummy player", e)
            cls.vlc_instance = _DummyInstance()

        # Create media player
        cls.players = cls.vlc_instance.media_player_new()

        # Configure player settings
        try:
            cls.players.video_set_scale(0)
            cls.players.video_set_aspect_ratio("16:9")
            log.debug("Video settings configured: scale=0, aspect_ratio=16:9")
        except Exception as e:
            log.warning("Failed to set video settings: %s", e)

        # Set audio volume
        try:
            volume = vlc_settings.settings.get("audio_volume", 100)
            cls.players.audio_set_volume(volume)
            log.debug("Audio volume set to: %d", volume)
        except Exception as e:
            log.warning("Failed to set audio volume: %s", e)

    @classmethod
    def is_dummy_instance(cls) -> bool:
        """
        Check if using dummy VLC instance.

        Returns:
            True if using dummy instance, False otherwise
        """
        is_dummy = isinstance(cls.vlc_instance, _DummyInstance)
        log.debug("Checking if dummy instance: %s", is_dummy)
        return is_dummy

    @classmethod
    def enter_fullscreen_window(cls, main_window: Any) -> None:
        """
        Create a controlled fullscreen window for video playback.

        Args:
            main_window: Main application window reference
        """
        log.info("Entering fullscreen mode")
        if cls.is_fullscreen:
            log.debug("Already in fullscreen mode, skipping")
            return

        try:
            # Create fullscreen toplevel window
            top = tk.Toplevel(main_window.TKroot)
            top.configure(background="black")
            log.debug("Created fullscreen toplevel window")

            # Set fullscreen attributes
            try:
                top.attributes("-fullscreen", True)
                log.debug("Set fullscreen attribute")
            except Exception as e:
                log.warning("Failed to set fullscreen attribute: %s, trying zoomed", e)
                try:
                    top.state("zoomed")
                    log.debug("Set zoomed state as fallback")
                except Exception as e2:
                    log.error("Failed to set zoomed state: %s", e2)

            # Create video canvas
            video_canvas = tk.Canvas(top, bg="black", highlightthickness=0)
            video_canvas.pack(fill="both", expand=True)
            log.debug("Created video canvas in fullscreen window")

            # Bind escape key to exit fullscreen
            def _exit_fs(ev=None):
                log.debug("Escape key pressed in fullscreen")
                main_window.write_event_value("__EXIT_FULLSCREEN__", None)

            top.bind("<Escape>", _exit_fs)
            video_canvas.bind("<Escape>", _exit_fs)

            # Update and focus window
            top.update_idletasks()
            video_canvas.update_idletasks()

            try:
                top.lift()
                top.focus_force()
                top.attributes("-topmost", True)
                top.attributes("-topmost", False)
                log.debug("Fullscreen window focused and brought to front")
            except Exception as e:
                log.warning("Failed to focus fullscreen window: %s", e)

            # Attach VLC player to canvas
            hwnd = video_canvas.winfo_id()
            if platform.startswith("linux"):
                cls.players.set_xwindow(hwnd)
                log.debug("Set xwindow for Linux: %s", hwnd)
            else:
                cls.players.set_hwnd(hwnd)
                log.debug("Set hwnd for Windows: %s", hwnd)

            cls.fullscreen_window = top
            cls.is_fullscreen = True
            log.info("Successfully entered fullscreen mode")

        except Exception as e:
            log.error("Failed to enter fullscreen window: %s", e, exc_info=True)

    @classmethod
    def exit_fullscreen_window(cls, main_window: Any, canvas_element: Any, show_background_callback: Callable) -> None:
        """
        Exit controlled fullscreen and reattach to the small canvas.

        Args:
            main_window: Main application window reference
            canvas_element: Canvas element to reattach player to
            show_background_callback: Callback to show background image
        """
        log.info("Exiting fullscreen mode")
        if not cls.is_fullscreen:
            log.debug("Not in fullscreen mode, skipping")
            return

        # Check if player was playing
        try:
            was_playing = bool(cls.players.is_playing())
            log.debug("Player was playing: %s", was_playing)
        except Exception as e:
            log.warning("Failed to check playing state: %s", e)
            was_playing = False

        # Destroy fullscreen window
        try:
            if cls.fullscreen_window is not None:
                cls.fullscreen_window.destroy()
                log.debug("Fullscreen window destroyed")
        except Exception as e:
            log.error("Failed to destroy fullscreen window: %s", e)

        cls.fullscreen_window = None
        cls.is_fullscreen = False

        # Reattach to main canvas
        try:
            canvas_widget = canvas_element.Widget
            canvas_widget.update_idletasks()
            canvas_id = canvas_widget.winfo_id()

            if platform.startswith("linux"):
                cls.players.set_xwindow(canvas_id)
                log.debug("Reattached to xwindow: %s", canvas_id)
            else:
                cls.players.set_hwnd(canvas_id)
                log.debug("Reattached to hwnd: %s", canvas_id)
        except Exception as e:
            log.error("Failed to reattach player to canvas: %s", e)

        # Update main window
        try:
            main_window.TKroot.update_idletasks()
            main_window.refresh()

            if not was_playing:
                cls.players.stop()
                show_background_callback()
                log.debug("Stopped playback and showed background")
        except Exception as e:
            log.error("Failed to update main window: %s", e)
            show_background_callback()

        log.info("Successfully exited fullscreen mode")

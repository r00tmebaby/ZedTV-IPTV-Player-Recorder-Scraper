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
from media import player


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
                r"C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe",
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
            log.warning(
                "VLC executable not found in PATH or common directories"
            )
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
    fullscreen_overlay: Any = None  # Overlay controls for fullscreen
    is_fullscreen: bool = False
    _channels_master: Optional[list] = None
    _bg_photo: Any = None

    # Persistent state storage for user settings
    _saved_subtitle_track_id: int = -1
    _saved_subtitle_track_desc: Optional[str] = None
    _saved_audio_track_id: int = -1
    _saved_audio_track_desc: Optional[str] = None
    _saved_playback_rate: float = 1.0

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
                log.debug(
                    "PYTHON_VLC_LIB_PATH=%s PYTHON_VLC_MODULE_PATH=%s",
                    vlc_lib_path,
                    vlc_module_path,
                )
            except Exception as e:
                log.debug("Failed to log PATH diagnostics: %s", e)
        except Exception as e:
            log.debug("player.find_lib() diagnostic failed: %s", e)

        # Try to create VLC instance
        try:
            cls.vlc_instance = player.Instance(*vlc_args)
            log.info("VLC Instance created successfully")
        except Exception as e:
            log.warning(
                "VLC Instance creation failed: %s - using dummy player", e
            )
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
    def save_player_state(cls) -> None:
        """Save current player settings to class-level persistent storage."""
        try:
            if not cls.players:
                return

            # Save subtitle track
            try:
                cls._saved_subtitle_track_id = cls.players.video_get_spu()
                cls._saved_subtitle_track_desc = None

                log.debug("Current subtitle track ID: %d", cls._saved_subtitle_track_id)

                if cls._saved_subtitle_track_id != -1:
                    spu_tracks = cls.players.video_get_spu_description()
                    log.debug("Available subtitle tracks: %s", [(t[0], t[1]) for t in (spu_tracks or [])])

                    if spu_tracks:
                        for track_id, track_desc in spu_tracks:
                            if track_id == cls._saved_subtitle_track_id:
                                cls._saved_subtitle_track_desc = track_desc.decode('utf-8') if isinstance(track_desc, bytes) else str(track_desc)
                                log.info("★ SAVED SUBTITLE: ID=%d, Description='%s'", cls._saved_subtitle_track_id, cls._saved_subtitle_track_desc)
                                break

                        if cls._saved_subtitle_track_desc is None:
                            log.warning("Could not find description for subtitle track ID %d", cls._saved_subtitle_track_id)
                else:
                    log.debug("Subtitles are disabled (ID=-1)")
            except Exception as e:
                log.error("Could not save subtitle track: %s", e, exc_info=True)

            # Save audio track
            try:
                cls._saved_audio_track_id = cls.players.audio_get_track()
                cls._saved_audio_track_desc = None

                if cls._saved_audio_track_id != -1:
                    audio_tracks = cls.players.audio_get_track_description()
                    if audio_tracks:
                        for track_id, track_desc in audio_tracks:
                            if track_id == cls._saved_audio_track_id:
                                cls._saved_audio_track_desc = track_desc.decode('utf-8') if isinstance(track_desc, bytes) else str(track_desc)
                                break
                log.debug("Saved audio state: ID=%d, Desc='%s'", cls._saved_audio_track_id, cls._saved_audio_track_desc)
            except Exception as e:
                log.debug("Could not save audio track: %s", e)

            # Save playback rate
            try:
                cls._saved_playback_rate = cls.players.get_rate()
                log.debug("Saved playback rate: %.2f", cls._saved_playback_rate)
            except Exception as e:
                log.debug("Could not save playback rate: %s", e)

        except Exception as e:
            log.warning("Failed to save player state: %s", e)

    @classmethod
    def restore_player_state(cls) -> None:
        """Restore player settings from class-level persistent storage."""
        try:
            if not cls.players:
                return

            # Try to restore subtitle track by matching description
            # We do this with retries since tracks may not be immediately available
            log.info("★ RESTORING SUBTITLE: Looking for Description='%s' (was ID=%d)", cls._saved_subtitle_track_desc, cls._saved_subtitle_track_id)

            if cls._saved_subtitle_track_desc is not None:
                # Try multiple times with minimal delays to avoid freezing
                import time
                max_attempts = 6
                for attempt in range(max_attempts):
                    try:
                        # Wait only on retries, keep delays very short
                        if attempt > 0:
                            wait_time = 0.05 * attempt  # 0.05, 0.1, 0.15, 0.2, 0.25s (max 0.75s total)
                            time.sleep(wait_time)

                        spu_tracks = cls.players.video_get_spu_description()
                        log.info("★ Got %d subtitle tracks on attempt %d", len(spu_tracks) if spu_tracks else 0, attempt + 1)

                        if spu_tracks and len(spu_tracks) > 1:  # More than just "Disable"
                            log.info("★ Available subtitle tracks (attempt %d): %s", attempt + 1, [(t[0], t[1]) for t in spu_tracks])
                            matched_id = None
                            all_descriptions = []

                            for track_id, track_desc in spu_tracks:
                                desc_str = track_desc.decode('utf-8') if isinstance(track_desc, bytes) else str(track_desc)
                                all_descriptions.append(f"ID={track_id}: '{desc_str}'")

                                log.info("★ Comparing: '%s' == '%s' ? %s", desc_str, cls._saved_subtitle_track_desc, desc_str == cls._saved_subtitle_track_desc)

                                if desc_str == cls._saved_subtitle_track_desc:
                                    matched_id = track_id
                                    log.info("★ MATCH FOUND! Will restore subtitle track ID=%d", matched_id)
                                    break

                            if matched_id is not None:
                                cls.players.video_set_spu(matched_id)
                                log.info("✅ RESTORED SUBTITLE: '%s' (ID %d -> %d)", cls._saved_subtitle_track_desc, cls._saved_subtitle_track_id, matched_id)
                                break  # Success!
                            else:
                                log.error("❌ NO MATCH FOUND for subtitle '%s'. Available tracks: %s", cls._saved_subtitle_track_desc, ", ".join(all_descriptions))
                                break  # Tracks available but no match, don't retry
                        else:
                            # Tracks not available yet or only "Disable" track
                            if attempt < max_attempts - 1:
                                log.warning("⏳ spu_tracks not ready on attempt %d (got %d tracks), retrying...", attempt + 1, len(spu_tracks) if spu_tracks else 0)
                            else:
                                log.error("❌ spu_tracks still not ready after %d attempts! Tracks not loaded.", max_attempts)
                    except Exception as e:
                        log.error("Failed to restore subtitles on attempt %d: %s", attempt + 1, e, exc_info=True)
                        if attempt >= max_attempts - 1:
                            break
            elif cls._saved_subtitle_track_id == -1:
                try:
                    cls.players.video_set_spu(-1)
                    log.debug("Subtitles disabled as before")
                except Exception as e:
                    log.debug("Failed to disable subtitles: %s", e)
            else:
                log.info("★ No subtitle description to restore (subtitle_track_desc is None)")

            # Restore audio track by matching description
            if cls._saved_audio_track_desc is not None:
                try:
                    audio_tracks = cls.players.audio_get_track_description()
                    if audio_tracks:
                        matched_id = None
                        for track_id, track_desc in audio_tracks:
                            desc_str = track_desc.decode('utf-8') if isinstance(track_desc, bytes) else str(track_desc)
                            if desc_str == cls._saved_audio_track_desc:
                                matched_id = track_id
                                break

                        if matched_id is not None:
                            cls.players.audio_set_track(matched_id)
                            log.info("✓ Restored audio: '%s' (ID %d -> %d)", cls._saved_audio_track_desc, cls._saved_audio_track_id, matched_id)
                        else:
                            log.warning("Could not find matching audio for '%s'", cls._saved_audio_track_desc)
                except Exception as e:
                    log.debug("Failed to restore audio: %s", e)

            # Restore playback rate
            if cls._saved_playback_rate != 1.0:
                try:
                    cls.players.set_rate(cls._saved_playback_rate)
                    log.info("✓ Restored playback rate: %.2f", cls._saved_playback_rate)
                except Exception as e:
                    log.debug("Failed to restore rate: %s", e)

            log.info("Player state restoration complete")

        except Exception as e:
            log.warning("Failed to restore player state: %s", e)

    @classmethod
    def enter_fullscreen_window(cls, main_window: Any, playback_controls: Any = None) -> None:
        """
        Create a controlled fullscreen window for video playback with overlay controls.

        Args:
            main_window: Main application window reference
            playback_controls: PlaybackControls instance for overlay (optional)
        """
        log.info("Entering fullscreen mode")
        if cls.is_fullscreen:
            log.debug("Already in fullscreen mode, skipping")
            return

        try:
            # Get keyboard binding for exit fullscreen
            from core.ui_settings import UISettings
            ui_settings = UISettings()
            exit_key = ui_settings.get_key_binding("exit_fullscreen")
            log.debug("Using exit fullscreen key: <%s>", exit_key)

            # Create fullscreen toplevel window
            top = tk.Toplevel(main_window.TKroot)
            top.configure(background="black")
            log.debug("Created fullscreen toplevel window")

            # Set fullscreen attributes
            try:
                top.attributes("-fullscreen", True)
                log.debug("Set fullscreen attribute")
            except Exception as e:
                log.warning(
                    "Failed to set fullscreen attribute: %s, trying zoomed", e
                )
                try:
                    top.state("zoomed")
                    log.debug("Set zoomed state as fallback")
                except Exception as e2:
                    log.error("Failed to set zoomed state: %s", e2)

            # Create video canvas
            video_canvas = tk.Canvas(top, bg="black", highlightthickness=0)
            video_canvas.pack(fill="both", expand=True)
            log.debug("Created video canvas in fullscreen window")

            # Bind configurable key to exit fullscreen
            def _exit_fs(ev=None):
                log.debug("Exit fullscreen key <%s> pressed", exit_key)
                main_window.write_event_value("__EXIT_FULLSCREEN__", None)

            top.bind(f"<{exit_key}>", _exit_fs)
            video_canvas.bind(f"<{exit_key}>", _exit_fs)

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

            # Save playback state before window handle change
            was_playing = False
            current_time = 0
            current_media = None

            try:
                was_playing = cls.players.is_playing()
                if was_playing:
                    current_time = cls.players.get_time()
                    current_media = cls.players.get_media()
                    # Save all player settings to persistent storage
                    cls.save_player_state()
                    log.debug("Saved playback position: %d ms", current_time)
            except Exception as e:
                log.debug("Could not check playback state: %s", e)

            # Stop playback before handle change
            if was_playing:
                try:
                    cls.players.stop()
                    log.debug("Stopped playback for handle change")
                except Exception as e:
                    log.debug("Could not stop playback: %s", e)

            # Attach VLC player to canvas
            hwnd = video_canvas.winfo_id()
            if platform.startswith("linux"):
                cls.players.set_xwindow(hwnd)
                log.debug("Set xwindow for Linux: %s", hwnd)
            else:
                cls.players.set_hwnd(hwnd)
                log.debug("Set hwnd for Windows: %s", hwnd)

            # Restart playback if it was playing
            if was_playing and current_media:
                try:
                    cls.players.set_media(current_media)
                    cls.players.play()

                    # Restore position immediately
                    if current_time > 0:
                        cls.players.set_time(current_time)

                    # Restore all player settings from persistent storage
                    # This now has built-in retry logic with minimal blocking
                    cls.restore_player_state()

                    log.info("Restarted playback with all settings restored")
                except Exception as e:
                    log.warning("Failed to restart playback: %s", e)

            cls.fullscreen_window = top
            cls.is_fullscreen = True

            # Create overlay controls if playback_controls provided
            if playback_controls:
                try:
                    from ui.fullscreen_overlay import FullscreenOverlay

                    def exit_fullscreen_callback():
                        main_window.write_event_value("__EXIT_FULLSCREEN__", None)

                    cls.fullscreen_overlay = FullscreenOverlay(
                        top,
                        cls,
                        exit_fullscreen_callback,
                        playback_controls,
                        video_canvas  # Pass the video canvas for mouse event binding
                    )
                    log.info("Fullscreen overlay controls created")
                except Exception as e:
                    log.error("Failed to create fullscreen overlay: %s", e, exc_info=True)

            # Ensure window has focus for keyboard events
            try:
                top.update()
                top.focus_force()
                video_canvas.focus_set()
                log.debug("Set focus to fullscreen window and canvas")
            except Exception as e:
                log.warning("Failed to set focus: %s", e)

            log.info("Successfully entered fullscreen mode")

        except Exception as e:
            log.error(
                "Failed to enter fullscreen window: %s", e, exc_info=True
            )

    @classmethod
    def exit_fullscreen_window(
        cls,
        main_window: Any,
        canvas_element: Any,
        show_background_callback: Callable,
    ) -> None:
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

        # Save playback state before window handle change
        was_playing = False
        current_time = 0
        current_media = None

        try:
            was_playing = bool(cls.players.is_playing())
            log.debug("Player was playing: %s", was_playing)
            if was_playing:
                current_time = cls.players.get_time()
                current_media = cls.players.get_media()
                # Save all player settings to persistent storage
                cls.save_player_state()
                log.debug("Saved playback position: %d ms", current_time)
        except Exception as e:
            log.warning("Failed to check playing state: %s", e)

        # Stop playback before handle change
        if was_playing:
            try:
                cls.players.stop()
                log.debug("Stopped playback for handle change")
            except Exception as e:
                log.debug("Could not stop playback: %s", e)

        # Destroy overlay controls first
        try:
            if cls.fullscreen_overlay is not None:
                cls.fullscreen_overlay.destroy()
                cls.fullscreen_overlay = None
                log.debug("Fullscreen overlay destroyed")
        except Exception as e:
            log.error("Failed to destroy fullscreen overlay: %s", e)

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

            if was_playing and current_media:
                # Restart playback
                try:
                    cls.players.set_media(current_media)
                    cls.players.play()

                    # Restore position immediately
                    if current_time > 0:
                        cls.players.set_time(current_time)

                    # Restore all player settings from persistent storage
                    # This now has built-in retry logic with minimal blocking
                    cls.restore_player_state()

                    log.info("Restarted playback with all settings restored")
                except Exception as e:
                    log.warning("Failed to restart playback: %s", e)
            else:
                cls.players.stop()
                show_background_callback()
                log.debug("Stopped playback and showed background")
        except Exception as e:
            log.error("Failed to update main window: %s", e)
            show_background_callback()

        log.info("Successfully exited fullscreen mode")

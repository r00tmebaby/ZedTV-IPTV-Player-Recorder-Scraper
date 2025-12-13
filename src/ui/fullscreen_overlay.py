"""
Fullscreen overlay controls - keyboard-only interface.

This module provides keyboard shortcuts for fullscreen mode controls.
All controls are accessed via keyboard shortcuts only.
"""

import logging
import tkinter as tk
from typing import Any, Callable

log = logging.getLogger(__name__)


class FullscreenOverlay:
    """
    Manages overlay controls in fullscreen mode with keyboard shortcuts.

    Controls can be toggled with 'C' key and include:
    - Beautiful icon buttons at bottom of screen
    - Keyboard shortcuts for all functions
    - Click buttons or use keyboard shortcuts

    Keyboard shortcuts:
    - ESC: Exit fullscreen
    - C: Toggle controls display
    - S: Subtitle menu
    - A: Audio menu
    - D: Speed menu
    - Space: Pause/Play
    - Left: Seek backward 30s
    - Right: Seek forward 30s
    """

    def __init__(self, parent_window: tk.Toplevel, player_instance: Any,
                 exit_callback: Callable, playback_controls: Any, video_canvas: tk.Canvas = None):
        """
        Initialize fullscreen overlay.

        Args:
            parent_window: The fullscreen Toplevel window
            player_instance: Player class instance
            exit_callback: Callback to exit fullscreen
            playback_controls: PlaybackControls instance
            video_canvas: The video canvas to bind mouse events to
        """
        self.parent = parent_window
        self.player = player_instance
        self.exit_callback = exit_callback
        self.controls = playback_controls
        self.video_canvas = video_canvas
        self.visible = False
        self._exiting = False  # Flag to prevent multiple exit calls

        # Load keyboard bindings from UI settings
        from core.ui_settings import UISettings
        self.ui_settings = UISettings()
        self.key_toggle_controls = self.ui_settings.get_key_binding("toggle_controls")
        self.key_exit_fullscreen = self.ui_settings.get_key_binding("exit_fullscreen")
        self.key_subtitle_menu = self.ui_settings.get_key_binding("subtitle_menu")
        self.key_audio_menu = self.ui_settings.get_key_binding("audio_menu")
        self.key_speed_menu = self.ui_settings.get_key_binding("speed_menu")
        self.key_play_pause = self.ui_settings.get_key_binding("play_pause")
        self.key_seek_forward = self.ui_settings.get_key_binding("seek_forward_small")
        self.key_seek_backward = self.ui_settings.get_key_binding("seek_backward_small")

        log.info("Keyboard shortcuts loaded:")
        log.info("  Toggle controls: %s", self.key_toggle_controls)
        log.info("  Exit fullscreen: %s", self.key_exit_fullscreen)
        log.info("  Subtitle menu: %s", self.key_subtitle_menu)
        log.info("  Audio menu: %s", self.key_audio_menu)
        log.info("  Speed menu: %s", self.key_speed_menu)
        log.info("  Play/Pause: %s", self.key_play_pause)
        log.info("  Seek forward: %s", self.key_seek_forward)
        log.info("  Seek backward: %s", self.key_seek_backward)

        # Create overlay frame (hidden by default)
        self._create_overlay()

        # Bind keyboard events only
        self._bind_keyboard_events()

        log.info("Fullscreen overlay initialized (keyboard-only mode)")

    def _create_overlay(self):
        """Create the overlay control panel."""
        log.info("★ CREATING OVERLAY FRAME")

        # Control frame at bottom with semi-transparent black background
        self.overlay_frame = tk.Frame(
            self.parent,
            bg='#000000',
            height=70
        )

        # Position at bottom - will be shown/hidden with place/place_forget
        # Don't place it yet, will be done in show()

        # Create control buttons
        self._create_controls()

        log.info("✅ Overlay frame created: %s", self.overlay_frame)

    def _create_controls(self):
        """Create control buttons in the overlay - all in single horizontal row."""
        # Smaller button style
        btn_style = {
            'bg': '#2c3e50',
            'fg': 'white',
            'font': ('Arial', 9),
            'relief': tk.FLAT,
            'borderwidth': 0,
            'padx': 8,
            'pady': 6,
            'cursor': 'hand2'
        }

        # Create single row container for all buttons
        btn_row = tk.Frame(self.overlay_frame, bg='#000000')
        btn_row.pack(expand=True, pady=10)

        # Seek backward 30s
        self.btn_back30 = tk.Button(
            btn_row,
            text="⏮ -30s",
            command=lambda: self._seek(-30),
            **btn_style
        )
        self.btn_back30.pack(side=tk.LEFT, padx=2)

        # Seek backward 10s
        self.btn_back10 = tk.Button(
            btn_row,
            text="⏪ -10s",
            command=lambda: self._seek(-10),
            **btn_style
        )
        self.btn_back10.pack(side=tk.LEFT, padx=2)

        # Pause/Play
        self.btn_pause = tk.Button(
            btn_row,
            text="⏸ Pause",
            command=self._toggle_pause,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor='hand2'
        )
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        # Seek forward 10s
        self.btn_fwd10 = tk.Button(
            btn_row,
            text="⏩ +10s",
            command=lambda: self._seek(10),
            **btn_style
        )
        self.btn_fwd10.pack(side=tk.LEFT, padx=2)

        # Seek forward 30s
        self.btn_fwd30 = tk.Button(
            btn_row,
            text="⏭ +30s",
            command=lambda: self._seek(30),
            **btn_style
        )
        self.btn_fwd30.pack(side=tk.LEFT, padx=2)

        # Separator
        separator = tk.Frame(btn_row, bg='#555555', width=2, height=30)
        separator.pack(side=tk.LEFT, padx=8)

        # Subtitles (S key)
        self.btn_subs = tk.Button(
            btn_row,
            text="📝 Subs (S)",
            command=self._show_subtitles,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            cursor='hand2'
        )
        self.btn_subs.pack(side=tk.LEFT, padx=2)

        # Audio (A key)
        self.btn_audio = tk.Button(
            btn_row,
            text="🔊 Audio (A)",
            command=self._show_audio,
            bg='#e67e22',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            cursor='hand2'
        )
        self.btn_audio.pack(side=tk.LEFT, padx=2)

        # Speed (D key)
        self.btn_speed = tk.Button(
            btn_row,
            text="⚡ Speed (D)",
            command=self._show_speed,
            bg='#3498db',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            cursor='hand2'
        )
        self.btn_speed.pack(side=tk.LEFT, padx=2)

        # Separator
        separator2 = tk.Frame(btn_row, bg='#555555', width=2, height=30)
        separator2.pack(side=tk.LEFT, padx=8)

        # Timer display (left side of exit button)
        separator3 = tk.Frame(btn_row, bg='#555555', width=2, height=30)
        separator3.pack(side=tk.LEFT, padx=8)

        self.time_label = tk.Label(
            btn_row,
            text="00:00 / 00:00",
            bg='#000000',
            fg='#ecf0f1',
            font=('Arial', 10, 'bold'),
            padx=10
        )
        self.time_label.pack(side=tk.LEFT, padx=5)

        # Exit fullscreen (ESC key)
        self.btn_exit = tk.Button(
            btn_row,
            text="⛶ Exit (ESC)",
            command=self._exit_fullscreen,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor='hand2'
        )
        self.btn_exit.pack(side=tk.LEFT, padx=2)

        log.info("Control buttons created with keyboard shortcuts and timer")

    def _bind_keyboard_events(self):
        """Bind all keyboard shortcuts."""
        log.info("Binding keyboard events...")

        # Helper to bind key with both lowercase and uppercase variants
        def bind_key(key, callback, description):
            key_binding = f"<{key}>"
            self.parent.bind(key_binding, lambda e: (callback(), "break")[1], add='+')
            if len(key) == 1 and key.isalpha():
                key_upper = f"<{key.upper()}>"
                self.parent.bind(key_upper, lambda e: (callback(), "break")[1], add='+')
            log.info(f"  ✓ Bound '{key}' -> {description}")

            # Also bind to video canvas if provided
            if self.video_canvas:
                self.video_canvas.bind(key_binding, lambda e: (callback(), "break")[1], add='+')
                if len(key) == 1 and key.isalpha():
                    self.video_canvas.bind(key_upper, lambda e: (callback(), "break")[1], add='+')

        # Bind all shortcuts
        bind_key(self.key_exit_fullscreen, self._exit_fullscreen, "Exit fullscreen")
        bind_key(self.key_toggle_controls, self._toggle_controls, "Toggle controls display")
        bind_key(self.key_subtitle_menu, self._show_subtitles, "Subtitle menu")
        bind_key(self.key_audio_menu, self._show_audio, "Audio menu")
        bind_key(self.key_speed_menu, self._show_speed, "Speed menu")
        bind_key(self.key_play_pause, self._toggle_pause, "Play/Pause")
        bind_key(self.key_seek_forward, lambda: self._seek(30), "Seek forward 30s")
        bind_key(self.key_seek_backward, lambda: self._seek(-30), "Seek backward 30s")

        # Ensure ESC also works when focus is inside overlay buttons
        exit_sequence = f"<{self.key_exit_fullscreen}>"
        self._bind_widget_recursive(self.overlay_frame, exit_sequence, self._exit_fullscreen)

        # Make parent focusable
        self.parent.focus_set()

        log.info("All keyboard shortcuts bound successfully")

    def _bind_widget_recursive(self, widget, key_sequence, callback):
        """Bind a key sequence to a widget and all descendants."""
        widget.bind(key_sequence, lambda e: (callback(), "break")[1], add='+')
        for child in widget.winfo_children():
            self._bind_widget_recursive(child, key_sequence, callback)

    def _toggle_controls(self):
        """Toggle controls visibility (for keyboard shortcut)."""
        log.info("Toggle controls called (%s key pressed)", self.key_toggle_controls)
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self):
        """Show the overlay controls."""
        if not self.visible:
            try:
                self.overlay_frame.lift()
                self.overlay_frame.place(relx=0, rely=1.0, relwidth=1.0, anchor='sw')
                self.overlay_frame.update()
                self.visible = True
                # Start timer updates
                self._start_timer_updates()
                log.info("Controls displayed")
            except Exception as e:
                log.error("Failed to show overlay: %s", e, exc_info=True)

    def hide(self):
        """Hide the overlay controls."""
        if self.visible:
            try:
                # Stop timer updates
                self._stop_timer_updates()
                self.overlay_frame.place_forget()
                self.visible = False
                log.info("Controls hidden")
            except Exception as e:
                log.error("Failed to hide overlay: %s", e, exc_info=True)

    def _start_timer_updates(self):
        """Start periodic timer updates."""
        try:
            self._update_timer()
        except Exception as e:
            log.error("Failed to start timer updates: %s", e)

    def _stop_timer_updates(self):
        """Stop periodic timer updates."""
        try:
            if hasattr(self, '_timer_job'):
                self.parent.after_cancel(self._timer_job)
                delattr(self, '_timer_job')
        except Exception as e:
            log.debug("Failed to stop timer updates: %s", e)

    def _update_timer(self):
        """Update the timer display with current playback time."""
        try:
            if not self.visible or self._exiting:
                log.debug("Timer update skipped: visible=%s, exiting=%s", self.visible, self._exiting)
                return

            log.debug("Timer update starting...")

            # Get time info from playback controls
            try:
                time_info = self.controls.get_time_info()
                log.debug("Got time_info: %s", time_info)
            except Exception as e:
                log.error("Failed to get time info: %s", e, exc_info=True)
                raise

            # get_time_info() returns seconds as floats, not milliseconds!
            current_sec = time_info.get('current', 0)
            total_sec = time_info.get('total', 0)
            rate = time_info.get('rate', 1.0)

            log.debug("Time values - current_sec=%s (type=%s), total_sec=%s (type=%s), rate=%s (type=%s)",
                      current_sec, type(current_sec).__name__,
                      total_sec, type(total_sec).__name__,
                      rate, type(rate).__name__)

            # Format time strings (input is seconds, not milliseconds)
            def format_time(seconds_float):
                try:
                    log.debug("format_time called with seconds=%s (type=%s)",
                              seconds_float, type(seconds_float).__name__)
                    total_seconds = int(seconds_float)
                    log.debug("  total_seconds=%s", total_seconds)
                    mins = total_seconds // 60
                    log.debug("  mins=%s", mins)
                    secs = total_seconds % 60
                    log.debug("  secs=%s", secs)
                    hours = mins // 60
                    log.debug("  hours=%s", hours)
                    mins = mins % 60
                    log.debug("  final mins=%s", mins)

                    if hours > 0:
                        result = f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}"
                        log.debug("  formatted (with hours): %s", result)
                        return result
                    result = f"{int(mins):02d}:{int(secs):02d}"
                    log.debug("  formatted (no hours): %s", result)
                    return result
                except Exception as e:
                    log.error("format_time failed: %s", e, exc_info=True)
                    raise

            try:
                current_str = format_time(current_sec)
                log.debug("current_str=%s", current_str)
            except Exception as e:
                log.error("Failed to format current time: %s", e, exc_info=True)
                raise

            try:
                total_str = format_time(total_sec)
                log.debug("total_str=%s", total_str)
            except Exception as e:
                log.error("Failed to format total time: %s", e, exc_info=True)
                raise

            # Show playback speed if not normal
            try:
                if abs(rate - 1.0) > 0.01:
                    time_display = f"{current_str} / {total_str} ({rate}x)"
                else:
                    time_display = f"{current_str} / {total_str}"
                log.debug("time_display=%s", time_display)
            except Exception as e:
                log.error("Failed to build time display string: %s", e, exc_info=True)
                raise

            try:
                self.time_label.config(text=time_display)
                log.debug("Timer label updated successfully: %s", time_display)
            except Exception as e:
                log.error("Failed to update label widget: %s", e, exc_info=True)
                raise

            # Schedule next update (every 500ms)
            try:
                self._timer_job = self.parent.after(500, self._update_timer)
                log.debug("Next timer update scheduled")
            except Exception as e:
                log.error("Failed to schedule next timer update: %s", e, exc_info=True)
                raise

        except Exception as e:
            log.error("Timer update failed with exception: %s", e, exc_info=True)
            # Try again in 1 second
            try:
                self._timer_job = self.parent.after(1000, self._update_timer)
                log.debug("Scheduled retry timer update in 1 second")
            except Exception as retry_error:
                log.error("Failed to schedule retry: %s", retry_error, exc_info=True)

    def destroy(self):
        """Clean up the overlay."""
        try:
            self.overlay_frame.destroy()
            log.debug("Overlay destroyed")
        except Exception as e:
            log.error("Failed to destroy overlay: %s", e)

    # Control callbacks
    def _seek(self, seconds):
        """Seek forward or backward."""
        try:
            if seconds < 0:
                self.controls.seek_backward(abs(seconds))
            else:
                self.controls.seek_forward(seconds)
            log.debug("Seeked %d seconds", seconds)
        except Exception as e:
            log.error("Failed to seek: %s", e)

    def _toggle_pause(self):
        """Toggle pause/play."""
        try:
            if self.player.players and self.player.players.is_playing():
                self.player.players.pause()
                self.btn_pause.config(text="▶ Play")
                log.info("Playback paused")
            elif self.player.players:
                self.player.players.play()
                self.btn_pause.config(text="⏸ Pause")
                log.info("Playback resumed")
        except Exception as e:
            log.error("Failed to toggle pause: %s", e)

    def _show_subtitles(self):
        """Show subtitle selection menu."""
        try:
            self.controls.show_subtitle_menu()
            log.debug("Showing subtitle menu")
        except Exception as e:
            log.error("Failed to show subtitle menu: %s", e)

    def _show_audio(self):
        """Show audio track selection menu."""
        try:
            self.controls.show_audio_menu()
            log.debug("Showing audio menu")
        except Exception as e:
            log.error("Failed to show audio menu: %s", e)

    def _show_speed(self):
        """Show speed selection menu."""
        try:
            self.controls.show_speed_menu()
            log.debug("Showing speed menu")
        except Exception as e:
            log.error("Failed to show speed menu: %s", e)

    def _exit_fullscreen(self):
        """Exit fullscreen mode."""
        if self._exiting:
            log.debug("Already exiting fullscreen, ignoring duplicate call")
            return

        self._exiting = True
        log.info("Exiting fullscreen mode")
        try:
            # Stop timer updates before exiting
            if hasattr(self, '_timer_job'):
                try:
                    self.parent.after_cancel(self._timer_job)
                except Exception:
                    pass

            self.exit_callback()
            log.info("Fullscreen exited successfully")
            # Note: Don't reset _exiting here as the window will be destroyed
        except Exception as e:
            log.error("Failed to exit fullscreen: %s", e, exc_info=True)
            self._exiting = False  # Reset on error so user can try again

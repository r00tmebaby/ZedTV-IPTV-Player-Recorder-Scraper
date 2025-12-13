"""
Playback controls UI and functionality.

This module provides video playback controls including seeking,
subtitle/audio track selection, and playback speed control.
"""

import logging
from typing import Any
from . import PySimpleGUI as sg

log = logging.getLogger(__name__)


class PlaybackControls:
    """
    Manages playback controls for video player.

    Attributes:
        player_instance: Reference to Player instance
        window: Main window reference
        is_visible: Whether controls are currently shown
        seek_amount: Default seek amount in seconds
    """

    def __init__(self, player_instance: Any, window: Any):
        """
        Initialize playback controls.

        Args:
            player_instance: Player instance
            window: Main window reference
        """
        self.player_instance = player_instance
        self.window = window
        self.is_visible = False
        self.seek_amount = 10  # Default 10 seconds
        self._last_total_duration = 0.0
        log.debug("PlaybackControls initialized")

    def reset_time_tracking(self) -> None:
        """Reset cached duration info when a new stream starts."""
        self._last_total_duration = 0.0

    def seek_forward(self, seconds: int = None) -> None:
        """
        Seek forward in the media.

        Args:
            seconds: Number of seconds to seek forward (default: self.seek_amount)
        """
        if seconds is None:
            seconds = self.seek_amount

        try:
            if self.player_instance.players and self.player_instance.players.is_playing():
                current_time = self.player_instance.players.get_time()
                new_time = current_time + (seconds * 1000)  # Convert to milliseconds
                self.player_instance.players.set_time(new_time)
                log.info("Seeked forward %d seconds to %d ms", seconds, new_time)
            else:
                log.debug("Cannot seek: player not playing")
        except Exception as e:
            log.error("Failed to seek forward: %s", e, exc_info=True)

    def seek_backward(self, seconds: int = None) -> None:
        """
        Seek backward in the media.

        Args:
            seconds: Number of seconds to seek backward (default: self.seek_amount)
        """
        if seconds is None:
            seconds = self.seek_amount

        try:
            if self.player_instance.players and self.player_instance.players.is_playing():
                current_time = self.player_instance.players.get_time()
                new_time = max(0, current_time - (seconds * 1000))  # Convert to milliseconds
                self.player_instance.players.set_time(new_time)
                log.info("Seeked backward %d seconds to %d ms", seconds, new_time)
            else:
                log.debug("Cannot seek: player not playing")
        except Exception as e:
            log.error("Failed to seek backward: %s", e, exc_info=True)

    def set_position(self, position: float) -> None:
        """
        Set playback position as a percentage.

        Args:
            position: Position from 0.0 to 1.0
        """
        try:
            if self.player_instance.players:
                self.player_instance.players.set_position(position)
                log.info("Set position to %.2f%%", position * 100)
        except Exception as e:
            log.error("Failed to set position: %s", e, exc_info=True)

    def get_subtitle_tracks(self) -> list:
        """
        Get available subtitle tracks.

        Returns:
            List of subtitle track tuples (id, description)
        """
        try:
            if self.player_instance.players:
                tracks = self.player_instance.players.video_get_spu_description()
                if tracks:
                    result = [(t[0], t[1].decode('utf-8') if isinstance(t[1], bytes) else str(t[1]))
                             for t in tracks]
                    log.debug("Found %d subtitle tracks", len(result))
                    return result
        except Exception as e:
            log.error("Failed to get subtitle tracks: %s", e, exc_info=True)
        return []

    def set_subtitle_track(self, track_id: int) -> None:
        """
        Set active subtitle track.

        Args:
            track_id: Subtitle track ID (-1 to disable)
        """
        try:
            if self.player_instance.players:
                # Ensure track_id is an integer
                track_id = int(track_id)
                self.player_instance.players.video_set_spu(track_id)
                log.info("Set subtitle track to ID: %d", track_id)
                # Save state immediately after change
                self.player_instance.save_player_state()
        except Exception as e:
            log.error("Failed to set subtitle track: %s", e, exc_info=True)

    def get_audio_tracks(self) -> list:
        """
        Get available audio tracks.

        Returns:
            List of audio track tuples (id, description)
        """
        try:
            if self.player_instance.players:
                tracks = self.player_instance.players.audio_get_track_description()
                if tracks:
                    result = [(t[0], t[1].decode('utf-8') if isinstance(t[1], bytes) else str(t[1]))
                             for t in tracks]
                    log.debug("Found %d audio tracks", len(result))
                    return result
        except Exception as e:
            log.error("Failed to get audio tracks: %s", e, exc_info=True)
        return []

    def set_audio_track(self, track_id: int) -> None:
        """
        Set active audio track.

        Args:
            track_id: Audio track ID
        """
        try:
            if self.player_instance.players:
                # Ensure track_id is an integer
                track_id = int(track_id)
                self.player_instance.players.audio_set_track(track_id)
                log.info("Set audio track to ID: %d", track_id)
                # Save state immediately after change
                self.player_instance.save_player_state()
        except Exception as e:
            log.error("Failed to set audio track: %s", e, exc_info=True)

    def set_playback_rate(self, rate: float) -> None:
        """
        Set playback speed rate.

        Args:
            rate: Playback rate (0.5 = half speed, 1.0 = normal, 2.0 = double speed)
        """
        try:
            if self.player_instance.players:
                self.player_instance.players.set_rate(rate)
                log.info("Set playback rate to %.2fx", rate)
                # Save state immediately after change
                self.player_instance.save_player_state()
        except Exception as e:
            log.error("Failed to set playback rate: %s", e, exc_info=True)

    def get_playback_rate(self) -> float:
        """
        Get current playback speed rate.

        Returns:
            Current playback rate
        """
        try:
            if self.player_instance.players:
                return self.player_instance.players.get_rate()
        except Exception as e:
            log.error("Failed to get playback rate: %s", e, exc_info=True)
        return 1.0

    def get_time_info(self) -> dict:
        """
        Get current playback time information.

        Returns:
            Dictionary with 'current', 'total', 'position', and 'rate' keys
        """
        try:
            if self.player_instance.players:
                # Get state to check if media is loaded (playing or paused)
                state = self.player_instance.players.get_state()
                # NOTE: libvlc reports NothingSpecial (0) at the very start of playback even though time/length are valid.
                if state not in [5, 6, 7]:  # allow states 0-4
                    current = self.player_instance.players.get_time()  # milliseconds
                    total = self.player_instance.players.get_length()  # milliseconds
                    position = self.player_instance.players.get_position()  # 0.0 to 1.0
                    rate = self.player_instance.players.get_rate()  # playback speed

                    total_seconds = total / 1000.0 if total >= 0 else -1
                    if total_seconds > 0:
                        self._last_total_duration = total_seconds
                    elif self._last_total_duration > 0:
                        total_seconds = self._last_total_duration

                    return {
                        'current': current / 1000.0 if current >= 0 else 0,
                        'total': total_seconds if total_seconds > 0 else 0,
                        'position': position if position >= 0 else 0,
                        'rate': rate if rate > 0 else 1.0
                    }
        except Exception as e:
            log.debug("Failed to get time info: %s", e)

        return {'current': 0, 'total': self._last_total_duration if self._last_total_duration > 0 else 0, 'position': 0, 'rate': 1.0}

    def format_time(self, seconds: float) -> str:
        """
        Format time in seconds to HH:MM:SS or MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        if seconds <= 0:
            return "00:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def show_subtitle_menu(self) -> None:
        """Show popup menu for subtitle track selection."""
        tracks = self.get_subtitle_tracks()

        if not tracks:
            sg.popup("No subtitle tracks available", title="Subtitles", keep_on_top=True)
            return

        # Create clickable button layout
        layout = [
            [sg.Text("Select Subtitle Track:", font=("Arial", 11, "bold"))],
            [sg.Text("")],
        ]

        # Add disable button
        layout.append([sg.Button("Disable Subtitles", key=-1, size=(40, 1), button_color=("white", "#e74c3c"))])
        layout.append([sg.Text("")])

        # Add track buttons
        for track_id, desc in tracks:
            layout.append([sg.Button(desc, key=track_id, size=(40, 1))])

        layout.append([sg.Text("")])
        layout.append([sg.Button("Cancel", key="__CANCEL__", size=(40, 1))])

        window = sg.Window("Subtitle Tracks", layout, keep_on_top=True, modal=True, finalize=True)

        event, _ = window.read()
        window.close()

        if event and event != "__CANCEL__" and event != sg.WIN_CLOSED:
            if event == -1:
                self.set_subtitle_track(-1)
                log.info("Subtitles disabled")
            else:
                self.set_subtitle_track(event)
                track_name = next((desc for tid, desc in tracks if tid == event), "Unknown")
                log.info("Subtitle track set to: %s", track_name)

    def show_audio_menu(self) -> None:
        """Show popup menu for audio track selection."""
        tracks = self.get_audio_tracks()

        if not tracks:
            sg.popup("No audio tracks available", title="Audio", keep_on_top=True)
            return

        # Create clickable button layout
        layout = [
            [sg.Text("Select Audio Track:", font=("Arial", 11, "bold"))],
            [sg.Text("")],
        ]

        # Add track buttons
        for track_id, desc in tracks:
            layout.append([sg.Button(desc, key=track_id, size=(40, 1))])

        layout.append([sg.Text("")])
        layout.append([sg.Button("Cancel", key="__CANCEL__", size=(40, 1))])

        window = sg.Window("Audio Tracks", layout, keep_on_top=True, modal=True, finalize=True)

        event, _ = window.read()
        window.close()

        if event and event != "__CANCEL__" and event != sg.WIN_CLOSED:
            self.set_audio_track(event)
            track_name = next((desc for tid, desc in tracks if tid == event), "Unknown")
            log.info("Audio track set to: %s", track_name)

    def show_speed_menu(self) -> None:
        """Show popup menu for playback speed selection."""
        speeds = [
            ("0.25x", 0.25),
            ("0.5x", 0.5),
            ("0.75x", 0.75),
            ("Normal (1x)", 1.0),
            ("1.25x", 1.25),
            ("1.5x", 1.5),
            ("2x", 2.0),
        ]

        current_rate = self.get_playback_rate()

        # Create clickable button layout
        layout = [
            [sg.Text("Select Playback Speed:", font=("Arial", 11, "bold"))],
            [sg.Text("")],
        ]

        # Add speed buttons with checkmark for current speed
        for label, rate in speeds:
            is_current = abs(rate - current_rate) < 0.01
            button_text = f"{label} {'✓' if is_current else ''}"
            button_color = ("white", "#27ae60") if is_current else None
            layout.append([sg.Button(button_text, key=rate, size=(20, 1), button_color=button_color)])

        layout.append([sg.Text("")])
        layout.append([sg.Button("Cancel", key="__CANCEL__", size=(20, 1))])

        window = sg.Window("Playback Speed", layout, keep_on_top=True, modal=True, finalize=True)

        event, _ = window.read()
        window.close()

        if event and event != "__CANCEL__" and event != sg.WIN_CLOSED:
            self.set_playback_rate(event)
            speed_label = next((label for label, rate in speeds if rate == event), "Unknown")
            log.info("Playback speed set to: %s", speed_label)

    def toggle_fullscreen(self) -> None:
        """
        Toggle fullscreen mode.

        This method triggers the fullscreen event that's handled by the main event loop.
        """
        try:
            if self.player_instance.is_fullscreen:
                # Already in fullscreen, trigger exit
                self.window.write_event_value("__EXIT_FULLSCREEN__", None)
                log.debug("Triggered fullscreen exit")
            else:
                # Enter fullscreen by triggering the play event with fullscreen flag
                # This is handled by the main application logic
                self.window.write_event_value("__ENTER_FULLSCREEN__", None)
                log.debug("Triggered fullscreen enter")
        except Exception as e:
            log.error("Failed to toggle fullscreen: %s", e, exc_info=True)

    def update_controls_state(self, is_playing: bool) -> None:
        """
        Enable or disable playback control buttons based on playback state.

        Args:
            is_playing: True if media is playing, False otherwise
        """
        try:
            # List of all playback control button keys
            control_buttons = [
                "_seek_back_30_",
                "_seek_back_10_",
                "_seek_forward_10_",
                "_seek_forward_30_",
                "_pause_play_",
                "_fullscreen_btn_",
                "_subtitles_",
                "_audio_tracks_",
                "_speed_",
            ]

            # Only log when state changes to reduce spam
            if not hasattr(self, '_last_controls_state') or self._last_controls_state != is_playing:
                log.debug("Control buttons state changed: is_playing=%s", is_playing)
                self._last_controls_state = is_playing

            for button_key in control_buttons:
                try:
                    self.window[button_key].update(disabled=not is_playing)
                except Exception as e:
                    log.debug("Failed to update button %s: %s", button_key, e)
        except Exception as e:
            log.error("Failed to update controls state: %s", e, exc_info=True)


def build_playback_controls_row() -> list:
    """
    Build a row of playback control buttons.

    Returns:
        List of PySimpleGUI elements for playback controls
    """
    return [
        sg.Button("⏮ -30s", key="_seek_back_30_", size=(7, 1), button_color=("white", "#2c3e50")),
        sg.Button("⏪ -10s", key="_seek_back_10_", size=(7, 1), button_color=("white", "#34495e")),
        sg.Button("⏸ Pause", key="_pause_play_", size=(8, 1), button_color=("white", "#27ae60")),
        sg.Button("⏩ +10s", key="_seek_forward_10_", size=(7, 1), button_color=("white", "#34495e")),
        sg.Button("⏭ +30s", key="_seek_forward_30_", size=(7, 1), button_color=("white", "#2c3e50")),
        sg.Text("00:00 / 00:00", key="_time_display_", size=(15, 1), justification="center"),
        sg.Button("⛶", key="_fullscreen_btn_", size=(4, 1), button_color=("white", "#e74c3c"), tooltip="Fullscreen"),
        sg.Button("CC", key="_subtitles_", size=(4, 1), button_color=("white", "#9b59b6"), tooltip="Subtitles"),
        sg.Button("🔊", key="_audio_tracks_", size=(4, 1), button_color=("white", "#e67e22"), tooltip="Audio Tracks"),
        sg.Button("⚡", key="_speed_", size=(4, 1), button_color=("white", "#3498db"), tooltip="Playback Speed"),
    ]

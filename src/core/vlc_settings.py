"""
VLC Settings Manager for IPTV Player
Manages user-configurable VLC options that are relevant for IPTV streaming.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .config import DATA_FOLDER

SETTINGS_FILE = Path(DATA_FOLDER) / "vlc_settings.json"


# Default VLC settings optimized for IPTV streaming
DEFAULT_VLC_SETTINGS = {
    # Network & Streaming
    "network_caching": 1000,  # ms - buffer for network streams (default: 1000)
    "live_caching": 300,      # ms - buffer for live streams (default: 300)

    # Hardware Acceleration
    "hw_decoding": "auto",    # auto, disabled, d3d11va, dxva2, qsv

    # Audio
    "audio_output": "auto",   # auto, directsound, wasapi, mmdevice
    "audio_volume": 100,       # 0-200
    "audio_track": -1,         # -1 = auto, 0+ = specific track

    # Video
    "video_output": "auto",   # auto, direct3d11, direct3d9, opengl
    "deinterlace": "off",      # off, on, auto
    "aspect_ratio": "",        # empty = auto, or "16:9", "4:3", etc.

    # Subtitles
    "subtitle_track": -1,      # -1 = disabled, 0+ = specific track

    # Advanced
    "skip_frames": False,      # Skip frames if system is too slow
    "drop_late_frames": True,  # Drop frames that are too late
    "reset_plugins_cache": True,  # Reset plugin cache on startup
}


class VLCSettings:
    """Manager for VLC settings."""

    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults."""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # Merge with defaults to add any new settings
                settings = DEFAULT_VLC_SETTINGS.copy()
                settings.update(saved)
                return settings
            except Exception:
                pass
        return DEFAULT_VLC_SETTINGS.copy()

    def save_settings(self) -> None:
        """Save current settings to file."""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save VLC settings: {e}")

    def get_vlc_args(self) -> list:
        """Convert settings to VLC command-line arguments."""
        args = []

        # Network caching
        if self.settings.get("network_caching"):
            args.append(f"--network-caching={self.settings['network_caching']}")

        if self.settings.get("live_caching"):
            args.append(f"--live-caching={self.settings['live_caching']}")

        # Hardware decoding
        hw = self.settings.get("hw_decoding", "auto")
        if hw == "disabled":
            args.append("--avcodec-hw=none")
        elif hw != "auto":
            args.append(f"--avcodec-hw={hw}")

        # Audio output
        audio_out = self.settings.get("audio_output", "auto")
        if audio_out != "auto":
            args.append(f"--aout={audio_out}")

        # Video output
        video_out = self.settings.get("video_output", "auto")
        if video_out != "auto":
            args.append(f"--vout={video_out}")

        # Deinterlace
        deinterlace = self.settings.get("deinterlace", "off")
        if deinterlace == "on":
            args.append("--deinterlace=1")
            args.append("--deinterlace-mode=blend")
        elif deinterlace == "auto":
            args.append("--deinterlace=-1")

        # Advanced
        if self.settings.get("skip_frames"):
            args.append("--skip-frames")

        if self.settings.get("drop_late_frames"):
            args.append("--drop-late-frames")
        else:
            args.append("--no-drop-late-frames")

        # Reset plugins cache
        if self.settings.get("reset_plugins_cache", True):
            args.append("--reset-plugins-cache")

        return args

    def update(self, key: str, value: Any) -> None:
        """Update a setting and save."""
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()


# Descriptions for UI
SETTING_DESCRIPTIONS = {
    "network_caching": "Network buffer (ms) - Higher values prevent stuttering but increase delay",
    "live_caching": "Live stream buffer (ms) - Lower values reduce delay",
    "hw_decoding": "Hardware acceleration - Use GPU for video decoding",
    "audio_output": "Audio output module",
    "video_output": "Video output module",
    "deinterlace": "Deinterlacing for interlaced content",
    "skip_frames": "Skip frames if playback is too slow",
    "drop_late_frames": "Drop frames that arrive too late",
    "reset_plugins_cache": "Reset VLC plugin cache on startup",
}


# Available options for dropdowns
SETTING_OPTIONS = {
    "hw_decoding": ["auto", "disabled", "d3d11va", "dxva2", "qsv"],
    "audio_output": ["auto", "directsound", "wasapi", "mmdevice"],
    "video_output": ["auto", "direct3d11", "direct3d9", "opengl"],
    "deinterlace": ["off", "on", "auto"],
}


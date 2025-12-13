"""
UI Settings Manager for ZedTV IPTV Player
Manages theme and font settings for PySimpleGUI
"""

import json
from pathlib import Path
from typing import Any, Dict

from ui import PySimpleGUI as sg

from .config import DATA_FOLDER

UI_SETTINGS_FILE = Path(DATA_FOLDER) / "ui_settings.json"

# Default UI settings
DEFAULT_UI_SETTINGS = {
    "theme": "DarkTeal6",
    "font_family": "Arial",
    "font_size": 10,
    "title_font_size": 14,
    "button_font_size": 10,
    "table_font_size": 10,
    # Keyboard shortcuts
    "key_exit_fullscreen": "Escape",
    "key_toggle_controls": "c",
    "key_play_pause": "space",
    "key_seek_forward_small": "Right",
    "key_seek_backward_small": "Left",
    "key_seek_forward_big": "Control_L+Right",
    "key_seek_backward_big": "Control_L+Left",
    "key_volume_up": "Up",
    "key_volume_down": "Down",
    "key_fullscreen": "f",
    "key_subtitle_menu": "s",
    "key_audio_menu": "a",
    "key_speed_menu": "d",
    "key_global_search": "Control_L+f",
}

# Available themes (curated list of good-looking themes)
AVAILABLE_THEMES = [
    "DarkTeal6",
    "DarkBlue3",
    "DarkGrey",
    "DarkGrey1",
    "DarkBrown",
    "DarkPurple",
    "LightGreen",
    "DarkAmber",
    "DarkBlack",
    "DarkBlue",
    "DarkBlue2",
    "DarkBlue12",
    "DarkBrown1",
    "DarkBrown2",
    "DarkGreen",
    "DarkGreen1",
    "DarkGrey2",
    "DarkGrey3",
    "DarkPurple1",
    "DarkPurple2",
    "DarkRed",
    "DarkTeal",
    "DarkTeal1",
    "DarkTeal2",
    "DarkTeal9",
    "LightBlue",
    "LightBlue1",
    "LightBlue2",
    "LightBrown",
    "LightBrown1",
    "LightGreen1",
    "LightGrey",
    "LightGrey1",
    "LightPurple",
    "LightTeal",
    "LightYellow",
    "SystemDefault",
    "SystemDefault1",
    "Black",
    "BlueMono",
    "BluePurple",
    "BrightColors",
    "BrownBlue",
    "Dark",
    "Dark2",
    "Default",
    "Default1",
    "DefaultNoMoreNagging",
    "Green",
    "GreenMono",
    "GreenTan",
    "HotDogStand",
    "Kayak",
    "LightBlue3",
    "LightBrown2",
    "LightBrown3",
    "LightGreen2",
    "LightGreen3",
    "LightGrey2",
    "LightGrey3",
    "Material1",
    "Material2",
    "NeutralBlue",
    "Purple",
    "Python",
    "Reddit",
    "Reds",
    "SandyBeach",
    "TanBlue",
    "TealMono",
    "Topanga",
]

# Available font families
AVAILABLE_FONTS = [
    "Arial",
    "Helvetica",
    "Courier New",
    "Times New Roman",
    "Verdana",
    "Tahoma",
    "Trebuchet MS",
    "Georgia",
    "Comic Sans MS",
    "Segoe UI",
    "Calibri",
    "Consolas",
]

# Font sizes
FONT_SIZES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24]


class UISettings:
    """Manager for UI settings."""

    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults."""
        if UI_SETTINGS_FILE.exists():
            try:
                with open(UI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge with defaults to add any new settings
                settings = DEFAULT_UI_SETTINGS.copy()
                settings.update(saved)
                return settings
            except Exception:
                pass
        return DEFAULT_UI_SETTINGS.copy()

    def save_settings(self) -> None:
        """Save current settings to file."""
        try:
            Path(DATA_FOLDER).mkdir(parents=True, exist_ok=True)
            with open(UI_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save UI settings: {e}")

    def update(self, key: str, value: Any) -> None:
        """Update a setting and save."""
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()

    def apply_theme(self) -> None:
        """Apply the current theme to PySimpleGUI."""
        try:
            sg.theme(self.settings["theme"])
        except Exception:
            sg.theme("DarkTeal6")

    def get_font(self, font_type: str = "normal") -> tuple:
        """Get font tuple for PySimpleGUI elements."""
        family = self.settings.get("font_family", "Arial")

        if font_type == "title":
            size = self.settings.get("title_font_size", 14)
            return (family, size, "bold")
        elif font_type == "button":
            size = self.settings.get("button_font_size", 10)
            return (family, size)
        elif font_type == "table":
            size = self.settings.get("table_font_size", 10)
            return (family, size)
        else:  # normal
            size = self.settings.get("font_size", 10)
            return (family, size)

    def get_all_fonts(self) -> Dict[str, tuple]:
        """Get all font configurations."""
        return {
            "normal": self.get_font("normal"),
            "title": self.get_font("title"),
            "button": self.get_font("button"),
            "table": self.get_font("table"),
        }

    def get_key_binding(self, action: str) -> str:
        """
        Get keyboard binding for a specific action.

        Args:
            action: Action name (e.g., 'exit_fullscreen', 'toggle_controls')

        Returns:
            Key binding string (e.g., 'Escape', 'c')
        """
        key = f"key_{action}"
        return self.settings.get(key, DEFAULT_UI_SETTINGS.get(key, "")) 

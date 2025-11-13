"""Quick test for UI Settings window"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.ui_settings import UISettings
from ui.ui_settings_window import _show_ui_settings_window

if __name__ == "__main__":
    print("Testing UI Settings window...")
    ui_settings = UISettings()
    print(f"Current settings: {ui_settings.settings}")

    # Try to show window (will open GUI)
    result = _show_ui_settings_window(ui_settings)
    print(f"Result: {result}")
    print("Test completed!")


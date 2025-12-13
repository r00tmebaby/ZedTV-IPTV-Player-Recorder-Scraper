"""
Quick test to verify keyboard bindings are correctly configured.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.ui_settings import UISettings

def test_keybindings():
    """Test that keyboard bindings are correctly loaded."""
    settings = UISettings()

    print("=" * 60)
    print("Keyboard Bindings Configuration Test")
    print("=" * 60)

    # Test all bindings
    bindings = [
        ('exit_fullscreen', 'Exit Fullscreen'),
        ('toggle_controls', 'Toggle Controls'),
        ('play_pause', 'Play/Pause'),
        ('fullscreen', 'Toggle Fullscreen'),
        ('seek_forward_small', 'Seek Forward (Small)'),
        ('seek_backward_small', 'Seek Backward (Small)'),
        ('seek_forward_big', 'Seek Forward (Big)'),
        ('seek_backward_big', 'Seek Backward (Big)'),
        ('volume_up', 'Volume Up'),
        ('volume_down', 'Volume Down'),
    ]

    print("\nConfigured Keyboard Shortcuts:")
    print("-" * 60)

    for key_id, description in bindings:
        key_value = settings.get_key_binding(key_id)
        status = "✓" if key_value else "✗"
        print(f"{status} {description:30} : {key_value}")

    print("-" * 60)

    # Check critical bindings
    critical = ['exit_fullscreen', 'toggle_controls']
    all_ok = all(settings.get_key_binding(k) for k in critical)

    if all_ok:
        print("\n✅ All critical keyboard bindings are configured!")
        print("\nESC Key Test:")
        esc_key = settings.get_key_binding('exit_fullscreen')
        print(f"  - Exit fullscreen key: '{esc_key}'")
        print(f"  - Tkinter binding format: '<{esc_key}>'")
        return True
    else:
        print("\n❌ Some critical keyboard bindings are missing!")
        return False

if __name__ == "__main__":
    success = test_keybindings()
    sys.exit(0 if success else 1)


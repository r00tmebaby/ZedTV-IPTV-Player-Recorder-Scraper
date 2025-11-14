"""Cross-platform utilities for screen metrics and dialogs."""

import sys
from typing import Tuple

_is_windows = sys.platform.startswith('win')
_is_mac = sys.platform.startswith('darwin')
_is_linux = sys.platform.startswith('linux')


def get_screen_size() -> Tuple[int, int]:
    """Get screen width and height in a cross-platform way.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    if _is_windows:
        try:
            import ctypes
            width = ctypes.windll.user32.GetSystemMetrics(0)
            height = ctypes.windll.user32.GetSystemMetrics(1)
            return width, height
        except Exception:
            pass
    
    # Use Tkinter for Linux/macOS or as fallback
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except Exception:
        # Fallback to reasonable defaults
        return 1920, 1080


def show_error_dialog(title: str, message: str) -> None:
    """Show an error dialog in a cross-platform way.
    
    Args:
        title: Dialog title
        message: Error message to display
    """
    if _is_windows:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000010)
            return
        except Exception:
            pass
    
    # Fallback to tkinter messagebox for all platforms
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        # Last resort: print to console
        print(f"\n{title}\n{message}\n")


def is_windows() -> bool:
    """Check if running on Windows."""
    return _is_windows


def is_mac() -> bool:
    """Check if running on macOS."""
    return _is_mac


def is_linux() -> bool:
    """Check if running on Linux."""
    return _is_linux

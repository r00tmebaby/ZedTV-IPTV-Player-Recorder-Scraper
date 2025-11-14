"""VLC library path detection for bundled libraries."""

import os
import sys  # Used for platform detection and frozen/PyInstaller checks
from pathlib import Path
from typing import Tuple, Optional


def get_bundled_vlc_paths() -> Tuple[Optional[str], Optional[str]]:
    """Get paths to bundled VLC libraries based on platform.
    
    Returns:
        tuple: (lib_path, plugin_path) or (None, None) if not found
    """
    # Determine base directory (works for both dev and frozen/PyInstaller)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_dir = Path(sys._MEIPASS)
    else:
        # Running as script
        base_dir = Path(__file__).parent.parent
    
    # Platform-specific paths
    if sys.platform.startswith('win'):
        libs_dir = base_dir / 'libs' / 'win'
        lib_name = 'libvlc.dll'
    elif sys.platform.startswith('darwin'):
        libs_dir = base_dir / 'libs' / 'mac'
        lib_name = 'libvlc.dylib'
    elif sys.platform.startswith('linux'):
        libs_dir = base_dir / 'libs' / 'linux'
        lib_name = 'libvlc.so.5'
    else:
        return None, None
    
    lib_path = libs_dir / lib_name
    plugin_path = libs_dir / 'plugins'
    
    if lib_path.exists() and plugin_path.exists():
        return str(lib_path), str(plugin_path)
    
    return None, None


def setup_vlc_environment() -> bool:
    """Set environment variables to use bundled VLC libraries.
    
    Returns:
        True if bundled VLC libraries were found and configured, False otherwise
    """
    lib_path, plugin_path = get_bundled_vlc_paths()
    
    if lib_path and plugin_path:
        os.environ['PYTHON_VLC_LIB_PATH'] = lib_path
        os.environ['PYTHON_VLC_MODULE_PATH'] = plugin_path
        return True
    
    return False

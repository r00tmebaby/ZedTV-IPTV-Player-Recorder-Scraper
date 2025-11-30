# runtime hook to help load VLC libraries and plugins quickly when frozen by PyInstaller
# This runs early in the frozen app and will:
# - add the frozen app folder to the Windows DLL search path (so libvlc.dll is found quickly)
# - set VLC_PLUGIN_PATH to the bundled plugins folder so libvlc doesn't spend time searching
import os
import sys

try:
    # Determine base folder for frozen app. When frozen PyInstaller exposes _MEIPASS.
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        # running normal (dev) mode: base is project root (where main.py lives)
        base = os.path.abspath(
            os.path.dirname(__file__) + os.sep + ".." + os.sep + ".."
        )

    # On Windows, add base to DLL search path so ctypes finds libvlc.dll and friends quickly
    if os.name == "nt":
        try:
            # Python 3.8+: add_dll_directory improves DLL resolution for bundled DLLs
            os.add_dll_directory(base)
        except Exception:
            # fallback: prepend to PATH
            os.environ["PATH"] = base + os.pathsep + os.environ.get("PATH", "")

    # Ensure VLC plugin path points to the bundled "plugins" directory (if present)
    plugins_dir = os.path.join(base, "plugins")
    if os.path.isdir(plugins_dir):
        os.environ["VLC_PLUGIN_PATH"] = plugins_dir

except Exception:
    # Never fail startup because of this hook; just continue
    pass

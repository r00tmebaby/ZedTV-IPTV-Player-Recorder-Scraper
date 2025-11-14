#!/bin/bash
# Test script for WSL Ubuntu

echo "=== ZedTV WSL Test ==="
echo "Testing ZedTV in WSL Ubuntu environment"
echo ""

# Convert Windows path to WSL path
PROJECT_DIR="/mnt/c/Users/zgeor/PycharmProjects/ZedTV-IPTV-Player-Recorder-Scraper-1"

cd "$PROJECT_DIR" || exit 1

echo "1. Checking Python version..."
python3 --version

echo ""
echo "2. Checking if VLC is installed on system..."
which vlc
dpkg -l | grep vlc

echo ""
echo "3. Checking for VLC libraries..."
echo "Looking for libvlc.so..."
find /usr/lib -name "libvlc.so*" 2>/dev/null | head -5
echo "Looking for VLC plugins..."
find /usr/lib -name "libaccess_*" 2>/dev/null | head -3

echo ""
echo "4. Creating Python virtual environment..."
if [ ! -d "venv_wsl" ]; then
    python3 -m venv venv_wsl
fi

echo ""
echo "5. Activating virtual environment and installing requirements..."
source venv_wsl/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "6. Testing imports..."
cd src
python3 << 'PYEOF'
import sys
import os

print("Python:", sys.version)
print("Platform:", sys.platform)

try:
    from utils.vlc_loader import get_bundled_vlc_paths, setup_vlc_environment
    lib_path, plugin_path = get_bundled_vlc_paths()
    print(f"Bundled VLC lib path: {lib_path}")
    print(f"Bundled VLC plugin path: {plugin_path}")

    # Check if bundled libs exist
    if lib_path:
        print(f"Bundled lib exists: {os.path.exists(lib_path)}")
    if plugin_path:
        print(f"Bundled plugins exist: {os.path.exists(plugin_path)}")

    print("\nAttempting to import VLC player...")
    from media.player import Instance
    print("SUCCESS: VLC player module imported!")

    # Try to create an instance
    print("\nAttempting to create VLC instance...")
    inst = Instance()
    print("SUCCESS: VLC instance created!")
    print(f"VLC Version: {inst.get_version()}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "=== Test Complete ==="


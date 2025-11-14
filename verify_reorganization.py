"""
Verify that the file reorganization didn't break anything.
Run this after reorganizing files to ensure all paths still work.
"""

import os
import sys
from pathlib import Path

# Color output for Windows
try:
    import colorama
    colorama.init()
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
except ImportError:
    GREEN = RED = YELLOW = RESET = ''


def check_path(path, description):
    """Check if a path exists."""
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"  {status} {description}: {path}")
    return exists


def main():
    print("=" * 70)
    print("File Reorganization Verification")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent
    os.chdir(project_root)

    all_good = True

    # Check build scripts structure
    print("1. Checking build_scripts structure...")
    paths = [
        ("build_scripts", "Build scripts directory"),
        ("build_scripts/windows", "Windows build scripts"),
        ("build_scripts/windows/build.bat", "Windows main build script"),
        ("build_scripts/windows/build_quick.bat", "Windows quick build"),
        ("build_scripts/windows/run_tests.bat", "Windows test runner"),
        ("build_scripts/windows/advanced", "Windows advanced scripts"),
        ("build_scripts/linux", "Linux build scripts"),
        ("build_scripts/linux/build.sh", "Linux build script"),
        ("build_scripts/macos", "macOS build scripts"),
        ("build_scripts/macos/build.sh", "macOS build script"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Check root convenience scripts
    print("2. Checking root convenience scripts...")
    paths = [
        ("build.bat", "Windows build wrapper"),
        ("build_quick.bat", "Windows quick build wrapper"),
        ("run_tests.bat", "Windows test wrapper"),
        ("quick_test.bat", "Windows quick test wrapper"),
        ("build.sh", "Linux/macOS build wrapper"),
        ("run_tests.sh", "Linux/macOS test wrapper"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Check new organizational folders
    print("3. Checking new organizational folders...")
    paths = [
        ("ci", "CI/CD scripts folder"),
        ("ci/test_pipeline.bat", "Test pipeline script"),
        ("ci/test_version_extraction.bat", "Version extraction test"),
        ("packaging", "Packaging files folder"),
        ("packaging/installer.iss", "Inno Setup installer script"),
        ("specs", "PyInstaller spec files folder"),
        ("specs/ZedTV-IPTV-Player.spec", "Main PyInstaller spec"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Check tests folder
    print("4. Checking tests folder...")
    paths = [
        ("tests", "Tests directory"),
        ("tests/test_cross_platform.py", "Cross-platform test"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Check source structure
    print("5. Checking source structure...")
    paths = [
        ("src", "Source directory"),
        ("src/main.py", "Main entry point"),
        ("src/utils/platform_utils.py", "Platform utilities"),
        ("src/utils/vlc_loader.py", "VLC loader"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Check VLC libraries
    print("6. Checking VLC libraries...")
    paths = [
        ("src/libs", "VLC libraries folder"),
        ("src/libs/win", "Windows VLC libraries"),
        ("src/libs/win/libvlc.dll", "Windows VLC library"),
    ]
    for path, desc in paths:
        if not check_path(path, desc):
            all_good = False
    print()

    # Test imports
    print("7. Testing Python imports...")
    try:
        sys.path.insert(0, str(project_root / 'src'))
        from utils.platform_utils import get_screen_size, is_windows
        from utils.vlc_loader import get_bundled_vlc_paths
        print(f"  {GREEN}✓{RESET} Platform utilities import successfully")
        print(f"  {GREEN}✓{RESET} VLC loader imports successfully")
        print(f"  {GREEN}✓{RESET} Platform detected: Windows={is_windows()}")
    except Exception as e:
        print(f"  {RED}✗{RESET} Import failed: {e}")
        all_good = False
    print()

    # Summary
    print("=" * 70)
    if all_good:
        print(f"{GREEN}All checks passed! ✓{RESET}")
        print("The file reorganization was successful.")
        return 0
    else:
        print(f"{RED}Some checks failed! ✗{RESET}")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


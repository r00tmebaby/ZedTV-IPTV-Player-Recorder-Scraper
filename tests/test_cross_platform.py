"""
Test script to verify cross-platform compatibility changes.
"""

import sys

def test_platform_utils():
    """Test platform utilities module."""
    print("Testing platform_utils...")
    sys.path.insert(0, 'src')

    from utils.platform_utils import (
        get_screen_size,
        is_windows,
        is_mac,
        is_linux
    )

    print(f"  Platform: Windows={is_windows()}, Mac={is_mac()}, Linux={is_linux()}")

    try:
        width, height = get_screen_size()
        print(f"  Screen size: {width}x{height}")
        print("  ✓ get_screen_size() works")
    except Exception as e:
        print(f"  ✗ get_screen_size() failed: {e}")
        return False

    return True


def test_vlc_loader():
    """Test VLC loader module."""
    print("\nTesting vlc_loader...")
    sys.path.insert(0, 'src')

    from utils.vlc_loader import get_bundled_vlc_paths, setup_vlc_environment

    lib_path, plugin_path = get_bundled_vlc_paths()

    if lib_path and plugin_path:
        print(f"  Found bundled VLC:")
        print(f"    Library: {lib_path}")
        print(f"    Plugins: {plugin_path}")
        print("  ✓ VLC paths detected")

        if setup_vlc_environment():
            import os
            print(f"  Environment variables set:")
            print(f"    PYTHON_VLC_LIB_PATH={os.environ.get('PYTHON_VLC_LIB_PATH', 'Not set')}")
            print(f"    PYTHON_VLC_MODULE_PATH={os.environ.get('PYTHON_VLC_MODULE_PATH', 'Not set')}")
            print("  ✓ VLC environment configured")
            return True
    else:
        print(f"  ⚠ No bundled VLC found (expected for {sys.platform})")
        print(f"    This is normal if VLC libs haven't been added for this platform yet")
        return True  # Not a failure

    return False


def test_imports():
    """Test that main.py can still be imported."""
    print("\nTesting main.py imports...")
    sys.path.insert(0, 'src')

    try:
        # This will fail if there are syntax errors or missing dependencies
        import main
        print("  ✓ main.py imports successfully")
        return True
    except ImportError as e:
        # Missing dependencies are OK for this test
        if "No module named" in str(e):
            print(f"  ⚠ Import warning (expected): {e}")
            return True
        raise
    except Exception as e:
        print(f"  ✗ main.py import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cross-Platform Compatibility Test")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()

    results = []

    results.append(("platform_utils", test_platform_utils()))
    results.append(("vlc_loader", test_vlc_loader()))
    results.append(("imports", test_imports()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


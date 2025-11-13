"""Diagnostic script to test VLC library loading."""
import sys
import os
from pathlib import Path

# Add src to path so we can import media.player
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("VLC Library Detection Diagnostic")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print(f"__file__: {__file__}")
print(f"Frozen: {getattr(sys, 'frozen', False)}")
print()

# Set up logging to console
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

print("Attempting to import media.player...")
try:
    from media import player
    print("✓ Successfully imported media.player")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

print("\nCalling player.find_lib()...")
try:
    dll, plugins = player.find_lib()
    print(f"\nRESULT:")
    print(f"  DLL found: {dll is not None}")
    if dll:
        print(f"  DLL object: {dll}")
    print(f"  Plugins path: {plugins}")
except Exception as e:
    print(f"✗ find_lib() raised exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
if dll:
    print("✓ VLC libraries FOUND - attempting Instance creation...")
    try:
        inst = player.Instance()
        print(f"✓ Instance created: {inst}")
        print("\n✓✓✓ VLC IS WORKING ✓✓✓")
    except Exception as e:
        print(f"✗ Instance creation failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ VLC libraries NOT FOUND")
    print("\nExpected locations checked:")
    print(f"  - {Path.cwd() / 'src' / 'libs' / 'win'}")
    print(f"  - {Path.cwd() / 'libs' / 'win'}")
    if os.path.exists('src/libs/win/libvlc.dll'):
        print(f"\n⚠ WARNING: libvlc.dll EXISTS at src/libs/win/libvlc.dll but wasn't loaded!")

print("=" * 60)


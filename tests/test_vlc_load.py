"""Quick test to verify VLC loads correctly from IDE"""
import sys
sys.path.insert(0, 'src')

from media import player

print("Testing VLC library loading...")
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")

dll, plugin_path = player.find_lib()
print(f"\nResult:")
print(f"  DLL: {dll}")
print(f"  Plugin path: {plugin_path}")

if dll:
    print("\n✓ VLC loaded successfully!")
    try:
        inst = player.Instance()
        print(f"✓ Instance created: {inst}")
        mp = inst.media_player_new()
        print(f"✓ Media player created: {mp}")
    except Exception as e:
        print(f"✗ Instance/player creation failed: {e}")
else:
    print("\n✗ VLC DLL not found")


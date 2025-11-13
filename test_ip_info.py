"""Quick test for IP Info window"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.event_handlers import EventHandler

if __name__ == "__main__":
    print("Testing IP Info window...")
    print("This will open a GUI window. Close it to complete the test.")

    try:
        EventHandler.handle_ip_info()
        print("✓ IP Info window test completed successfully!")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


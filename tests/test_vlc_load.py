"""Quick test to verify VLC loads correctly from IDE

Converted to a unittest that is skipped when media.player cannot be imported so
missing native libraries won't break test discovery.
"""

import sys
from pathlib import Path
import unittest
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

MEDIA_IMPORT_ERROR = None
player = None
try:
    from media import player as _player
    player = _player
except Exception as e:
    MEDIA_IMPORT_ERROR = str(e)
    logging.debug("media.player import failed: %s", MEDIA_IMPORT_ERROR)


class TestVLCLoad(unittest.TestCase):
    @unittest.skipIf(MEDIA_IMPORT_ERROR is not None, "media.player not importable: %s" % MEDIA_IMPORT_ERROR)
    def test_load_and_create(self):
        logging.info("Testing VLC library loading via player.find_lib()")
        dll, plugin_path = player.find_lib()
        self.assertTrue(bool(dll), "DLL not found")
        self.assertIsNotNone(plugin_path)
        # Try creating an instance and media player
        inst = player.Instance()
        self.assertIsNotNone(inst)
        mp = inst.media_player_new()
        self.assertIsNotNone(mp)

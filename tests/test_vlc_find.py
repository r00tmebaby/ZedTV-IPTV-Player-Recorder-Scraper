"""Diagnostic script to test VLC library loading.

This module provides a unittest TestCase that will be skipped when the
`media.player` module (and libvlc) is not available. Import errors will not
fail test discovery.
"""

import os
import sys
from pathlib import Path
import unittest
import logging

# Add src to path so we can import media.player
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

# Try to import media.player; if it fails capture the error and allow test discovery
MEDIA_IMPORT_ERROR = None
player = None
try:
    from media import player as _player
    player = _player
except Exception as e:
    MEDIA_IMPORT_ERROR = str(e)
    logging.debug("media.player import failed: %s", MEDIA_IMPORT_ERROR)


class TestVLCFind(unittest.TestCase):
    """VLC detection tests. Skipped when libvlc is not present."""

    @unittest.skipIf(MEDIA_IMPORT_ERROR is not None, "media.player not importable: %s" % MEDIA_IMPORT_ERROR)
    def test_find_lib_and_instance(self):
        """Check that find_lib returns a DLL handle and plugins path and Instance can be created.

        This test will only run when `media.player` imports successfully.
        """
        logging.info("Running VLC detection test")
        dll, plugins = player.find_lib()
        self.assertTrue(bool(dll), "libvlc DLL was not found")
        self.assertIsNotNone(plugins)
        # Attempt to create an Instance
        inst = player.Instance()
        self.assertIsNotNone(inst)

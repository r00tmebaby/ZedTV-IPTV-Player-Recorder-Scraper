import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from parsing.m3u_parser import parse_m3u
from services.epg import load_xmltv

M3U = """#EXTM3U
#EXTINF:-1 tvg-id="chan1" tvg-name="A" group-title="G",A
http://u/a
#EXTINF:-1 tvg-id="chan2" tvg-name="B" group-title="G",B
http://u/b
"""
XMLTV = """
<tv>
  <programme channel="chan1" start="20250101000000 +0000" stop="20250101010000 +0000">
    <title>Show 1</title>
    <desc>Desc 1</desc>
  </programme>
  <programme channel="chan2" start="20250101000000 +0000" stop="20250101003000 +0000">
    <title>News</title>
  </programme>
</tv>
"""


class TestEPGMapping(unittest.TestCase):
    def test_xmltv_map(self):
        parser = parse_m3u(M3U)
        idx = load_xmltv(XMLTV)
        enriched = parser.map_epg(idx)
        self.assertEqual(enriched, 2)
        self.assertTrue(parser.channels[0].epg)
        self.assertEqual(parser.channels[0].epg[0]["title"], "Show 1")


if __name__ == "__main__":
    unittest.main()

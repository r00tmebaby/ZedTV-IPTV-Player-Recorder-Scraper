import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from parsing.m3u_parser import parse_m3u

SAMPLE1 = """#EXTM3U
#EXTINF:-1 tvg-id=1 tvg-name='One' group-title=Sports,One
http://u/1
#EXTINF:-1 tvg-id="2" tvg-name="Two" group-title='News',Two
http://u/2
#EXTINF:-1 tvg-id=3 tvg-name=Three group-title=Movies,Three
http://u/3
"""

SAMPLE2 = """#EXTM3U
#EXTVLCOPT:http-user-agent=TestAgent
#KODIPROP:inputstream.adaptive.manifest_type=dash
#EXTINF:-1 tvg-id='10' tvg-name='A' group-title=Group1, A
http://u/a
#EXTIMG:url=http://img.local/logo.png
#EXTINF:-1 tvg-id=11 tvg-name="B" group-title='Group2',B
http://u/b
"""


class TestAttrVariants(unittest.TestCase):
    def test_attribute_variants(self):
        p = parse_m3u(SAMPLE1)
        self.assertEqual(len(p.channels), 3)
        ids = [c.tvg_id for c in p.channels]
        self.assertEqual(ids, ["1", "2", "3"])
        names = [c.tvg_name for c in p.channels]
        self.assertEqual(names, ["One", "Two", "Three"])


class TestM3UProps(unittest.TestCase):
    def test_props_and_attrs(self):
        p = parse_m3u(SAMPLE2)
        self.assertEqual(len(p.channels), 2)
        ch1 = p.channels[0]
        self.assertEqual(ch1.tvg_id, "10")
        # properties parsed
        self.assertIn("http-user-agent", ch1.vlc_opts)
        self.assertEqual(ch1.vlc_opts["http-user-agent"], "TestAgent")
        self.assertIn("inputstream.adaptive.manifest_type", ch1.kodi_props)
        # unquoted and single-quoted attributes parsed
        ch2 = p.channels[1]
        self.assertEqual(ch2.attrs.get("tvg-id"), "11")
        self.assertEqual(ch2.tvg_name, "B")
        # other property retained
        self.assertTrue(any(line.startswith("#EXTIMG") for line in ch2.properties) or ch2.other_props)


if __name__ == "__main__":
    unittest.main()

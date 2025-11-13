import unittest
from src.m3u_parser import parse_m3u

SAMPLE = """#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="Ch 1" tvg-logo="logo1.png" group-title="News",Ch 1
http://example.com/1
#EXTGRP:Sports
#EXTINF:-1 tvg-id="2" tvg-name="Ch 2",Ch 2
http://example.com/2
#EXTVLCOPT:http-user-agent=MyAgent
#EXTINF:-1 tvg-id="3" tvg-name="Ch 3" group-title="Movies",Ch 3
http://example.com/3
#EXTINF:-1 tvg-id="4" tvg-name="Broken Entry" group-title="Misc"
#EXTVLCOPT:network-caching=1000
#KODIPROP:inputstream.adaptive.license_type=widevine
#EXTINF:-1 tvg-id="5" tvg-name="Ch 5" group-title="Movies",Ch 5
http://example.com/5
"""

class TestM3UParser(unittest.TestCase):
    def test_parse_count(self):
        p = parse_m3u(SAMPLE)
        self.assertEqual(len(p.channels), 4)  # broken entry without URL skipped

    def test_groups(self):
        p = parse_m3u(SAMPLE)
        groups = p.groups()
        self.assertIn('News', groups)
        self.assertIn('Sports', groups)  # from EXTGRP fallback
        self.assertIn('Movies', groups)

    def test_properties_association(self):
        p = parse_m3u(SAMPLE)
        ch3 = [c for c in p.channels if c.tvg_id == '3'][0]
        self.assertEqual(ch3.tvg_name, 'Ch 3')
        ch5 = [c for c in p.channels if c.tvg_id == '5'][0]
        self.assertTrue(any('network-caching' in prop for prop in ch5.properties))

    def test_block_reconstruction(self):
        p = parse_m3u(SAMPLE)
        block = p.channels[0].to_block()
        self.assertIn('#EXTINF', block)
        self.assertIn('http://example.com/1', block)

if __name__ == '__main__':
    unittest.main()


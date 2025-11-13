import unittest, os, tempfile, sys, asyncio
BASE_DIR = os.path.dirname(__file__)
src_path = os.path.join(BASE_DIR, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.m3u_parser import parse_m3u
from src.app import generate_list
from models import Data

SAMPLE = """#EXTM3U
#EXTINF:-1 tvg-id="10" tvg-name="A" group-title="Group1",A
http://u/a
#EXTINF:-1 tvg-id="11" tvg-name="B" group-title="Group2",B
http://u/b
#EXTINF:-1 tvg-id="12" tvg-name="C" group-title="Group1",C
http://u/c
"""

class TestCustomList(unittest.TestCase):
    def test_generate_list_file(self):
        Data.data = SAMPLE
        Data.m3u_parser = parse_m3u(SAMPLE)
        Data.parsed_channels = Data.m3u_parser.channels
        Data.categories = Data.m3u_parser.groups()
        # select Group1 index(es)
        idxs = [Data.categories.index('Group1')]
        values = {'_table_countries_': idxs}
        with tempfile.TemporaryDirectory() as td:
            outfile = os.path.join(td, 'out.m3u')
            asyncio.run(generate_list(values, Data.categories, outfile, True))
            self.assertTrue(os.path.isfile(outfile))
            content = open(outfile, 'r', encoding='utf-8').read()
            self.assertIn('Group1', content)
            self.assertNotIn('Group2', content)
            # Should contain 2 entries (A, C)
            self.assertGreaterEqual(content.count('#EXTINF'), 2)

if __name__ == '__main__':
    unittest.main()

import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from services.xtream import _normalize_base


class TestXtreamSplit(unittest.TestCase):
    def test_normalize_base_http(self):
        self.assertEqual(_normalize_base("example.com"), "http://example.com:80")

    def test_normalize_base_https(self):
        self.assertEqual(_normalize_base("example.com", prefer_https=True), "https://example.com:443")

    def test_normalize_full(self):
        self.assertEqual(_normalize_base("http://demo.com:8080"), "http://demo.com:8080")


if __name__ == "__main__":
    unittest.main()

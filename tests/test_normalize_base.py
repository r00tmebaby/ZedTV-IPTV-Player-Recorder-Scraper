import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.xtream import _normalize_base


def test_bracketed_ipv6_with_port():
    # Input like "[::1]:8080" should be interpreted as an IPv6 literal with provided port
    inp = "[::1]:8080"
    out = _normalize_base(inp)
    assert out == "http://[::1]:8080"


def test_full_url_ipv6_https_with_port():
    inp = "https://[2001:db8::1]:4443"
    out = _normalize_base(inp)
    assert out == "https://[2001:db8::1]:4443"


def test_empty_string_defaults_to_localhost_http():
    # empty string defaults to http localhost:80 by default
    assert _normalize_base("") == "http://localhost:80"
    # but when prefer_https=True, should default to https localhost:443
    assert _normalize_base("", prefer_https=True) == "https://localhost:443"

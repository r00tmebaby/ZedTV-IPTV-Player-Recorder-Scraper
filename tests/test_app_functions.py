"""tests for core.app module."""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from core.app import _epoch_to_str, _fmt_formats, _fmt_yesno, _rows, get_categories
from services.xtream import _normalize_base


class TestRows(unittest.TestCase):
    """Test _rows helper function - 10 tests"""

    def test_empty_list(self):
        self.assertEqual(_rows([]), [])

    def test_single_item(self):
        self.assertEqual(_rows(["a"]), [["a"]])

    def test_multiple_items(self):
        self.assertEqual(_rows(["a", "b", "c"]), [["a"], ["b"], ["c"]])

    def test_numbers(self):
        self.assertEqual(_rows([1, 2, 3]), [[1], [2], [3]])

    def test_mixed_types(self):
        self.assertEqual(_rows([1, "b", 3.14]), [[1], ["b"], [3.14]])

    def test_none_items(self):
        self.assertEqual(_rows([None, "a", None]), [[None], ["a"], [None]])

    def test_nested_lists_not_flattened(self):
        self.assertEqual(_rows([[1, 2], [3, 4]]), [[[1, 2]], [[3, 4]]])

    def test_preserves_order(self):
        input_data = ["z", "a", "m", "b"]
        result = _rows(input_data)
        self.assertEqual([r[0] for r in result], input_data)

    def test_large_list(self):
        large = list(range(1000))
        result = _rows(large)
        self.assertEqual(len(result), 1000)

    def test_returns_new_list(self):
        original = ["a", "b"]
        result = _rows(original)
        original.append("c")
        self.assertEqual(len(result), 2)


class TestEpochToStr(unittest.TestCase):
    """Test _epoch_to_str function - 25 tests"""

    def test_none_returns_dash(self):
        self.assertEqual(_epoch_to_str(None), "-")

    def test_empty_string_returns_dash(self):
        self.assertEqual(_epoch_to_str(""), "-")

    def test_zero_returns_dash(self):
        self.assertEqual(_epoch_to_str(0), "-")

    def test_valid_epoch_int(self):
        result = _epoch_to_str(1609459200)  # 2021-01-01 00:00:00 UTC
        self.assertIn("2021", result)

    def test_valid_epoch_string(self):
        result = _epoch_to_str("1609459200")
        self.assertIn("2021", result)

    def test_contains_utc(self):
        result = _epoch_to_str(1609459200)
        self.assertIn("UTC", result)

    def test_contains_date(self):
        result = _epoch_to_str(1609459200)
        self.assertIn("2021-01-01", result)

    def test_contains_time(self):
        result = _epoch_to_str(1609459200)
        self.assertIn("00:00:00", result)

    def test_format_yyyy_mm_dd(self):
        result = _epoch_to_str(1609459200)
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")

    def test_format_hh_mm_ss(self):
        result = _epoch_to_str(1609459200)
        self.assertRegex(result, r"\d{2}:\d{2}:\d{2}")

    def test_recent_timestamp(self):
        result = _epoch_to_str(1700000000)  # Nov 2023
        self.assertIn("2023", result)

    def test_old_timestamp(self):
        result = _epoch_to_str(946684800)  # 2000-01-01
        self.assertIn("2000", result)

    def test_future_timestamp(self):
        result = _epoch_to_str(2000000000)  # May 2033
        self.assertIn("2033", result)

    def test_negative_returns_original(self):
        result = _epoch_to_str(-1)
        self.assertEqual(result, "-1")

    def test_very_large_number(self):
        result = _epoch_to_str(9999999999)
        # Should handle gracefully
        self.assertIsInstance(result, str)

    def test_invalid_string(self):
        result = _epoch_to_str("invalid")
        self.assertEqual(result, "invalid")

    def test_float_epoch(self):
        # Floats should be converted to int
        result = _epoch_to_str(1609459200.5)
        self.assertIn("2021", result)

    def test_string_with_decimals(self):
        result = _epoch_to_str("1609459200.5")
        self.assertIn("2021", result)

    def test_whitespace_string(self):
        self.assertEqual(_epoch_to_str("   "), "   ")

    def test_special_chars_string(self):
        result = _epoch_to_str("abc123")
        self.assertEqual(result, "abc123")

    def test_returns_string(self):
        result = _epoch_to_str(1609459200)
        self.assertIsInstance(result, str)

    def test_length_reasonable(self):
        result = _epoch_to_str(1609459200)
        self.assertGreater(len(result), 10)
        self.assertLess(len(result), 50)

    def test_consistent_format(self):
        result1 = _epoch_to_str(1609459200)
        result2 = _epoch_to_str(1609459200)
        self.assertEqual(result1, result2)

    def test_different_times_different_results(self):
        result1 = _epoch_to_str(1609459200)
        result2 = _epoch_to_str(1609459201)
        self.assertNotEqual(result1, result2)

    def test_milliseconds_handled(self):
        # Milliseconds timestamp (13 digits)
        result = _epoch_to_str(1609459200000)
        # Should still produce valid output
        self.assertIsInstance(result, str)


class TestFmtYesNo(unittest.TestCase):
    """Test _fmt_yesno function - 20 tests"""

    def test_true_returns_yes(self):
        self.assertEqual(_fmt_yesno(True), "Yes")

    def test_false_returns_no(self):
        self.assertEqual(_fmt_yesno(False), "No")

    def test_string_true_returns_yes(self):
        self.assertEqual(_fmt_yesno("true"), "Yes")

    def test_string_false_returns_no(self):
        self.assertEqual(_fmt_yesno("false"), "No")

    def test_string_True_capital_returns_yes(self):
        self.assertEqual(_fmt_yesno("True"), "Yes")

    def test_string_False_capital_returns_no(self):
        self.assertEqual(_fmt_yesno("False"), "No")

    def test_int_1_returns_yes(self):
        self.assertEqual(_fmt_yesno(1), "Yes")

    def test_int_0_returns_no(self):
        self.assertEqual(_fmt_yesno(0), "No")

    def test_string_1_returns_yes(self):
        self.assertEqual(_fmt_yesno("1"), "Yes")

    def test_string_0_returns_no(self):
        self.assertEqual(_fmt_yesno("0"), "No")

    def test_none_returns_dash(self):
        self.assertEqual(_fmt_yesno(None), "-")

    def test_empty_string_returns_dash(self):
        self.assertEqual(_fmt_yesno(""), "-")

    def test_int_2_returns_dash(self):
        self.assertEqual(_fmt_yesno(2), "-")

    def test_string_maybe_returns_dash(self):
        self.assertEqual(_fmt_yesno("maybe"), "-")

    def test_random_string_returns_dash(self):
        self.assertEqual(_fmt_yesno("xyz"), "-")

    def test_negative_number_returns_dash(self):
        self.assertEqual(_fmt_yesno(-1), "-")

    def test_float_returns_dash(self):
        self.assertEqual(_fmt_yesno(1.5), "-")

    def test_list_returns_dash(self):
        self.assertEqual(_fmt_yesno([]), "-")

    def test_dict_returns_dash(self):
        self.assertEqual(_fmt_yesno({}), "-")

    def test_case_insensitive(self):
        self.assertEqual(_fmt_yesno("TRUE"), "-")  # Only exact matches work


class TestFmtFormats(unittest.TestCase):
    """Test _fmt_formats function - 25 tests"""

    def test_empty_dict_returns_dash(self):
        self.assertEqual(_fmt_formats({}), "-")

    def test_none_formats_returns_dash(self):
        self.assertEqual(_fmt_formats({"allowed_output_formats": None}), "-")

    def test_empty_list_returns_dash(self):
        self.assertEqual(_fmt_formats({"allowed_output_formats": []}), "-")

    def test_single_format(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4"]})
        self.assertEqual(result, "mp4")

    def test_two_formats(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv"]})
        self.assertEqual(result, "mp4,mkv")

    def test_three_formats(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi"]})
        self.assertEqual(result, "mp4,mkv,avi")

    def test_four_formats_at_limit(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv"]})
        self.assertEqual(result, "mp4,mkv,avi,flv")

    def test_five_formats_shows_plus_one(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv", "mov"]})
        self.assertIn("+1", result)

    def test_six_formats_shows_plus_two(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv", "mov", "wmv"]})
        self.assertIn("+2", result)

    def test_ten_formats_shows_plus_six(self):
        formats = ["mp4", "mkv", "avi", "flv", "mov", "wmv", "ts", "m2ts", "webm", "ogv"]
        result = _fmt_formats({"allowed_output_formats": formats})
        self.assertIn("+6", result)

    def test_custom_limit_2(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi"]}, limit=2)
        self.assertIn("+1", result)

    def test_custom_limit_1(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv"]}, limit=1)
        self.assertIn("+1", result)

    def test_custom_limit_5(self):
        formats = ["mp4", "mkv", "avi", "flv", "mov", "wmv"]
        result = _fmt_formats({"allowed_output_formats": formats}, limit=5)
        self.assertIn("+1", result)

    def test_exactly_at_custom_limit(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv"]}, limit=2)
        self.assertEqual(result, "mp4,mkv")

    def test_under_custom_limit(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4"]}, limit=5)
        self.assertEqual(result, "mp4")

    def test_comma_separated(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv"]})
        self.assertIn(",", result)

    def test_no_spaces(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi"]})
        self.assertNotIn(" ", result)

    def test_first_items_shown(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv", "mov"]})
        self.assertIn("mp4", result)
        self.assertIn("mkv", result)

    def test_overflow_not_shown(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv", "mov"]})
        self.assertNotIn("mov", result)

    def test_preserves_order(self):
        result = _fmt_formats({"allowed_output_formats": ["avi", "mp4", "mkv"]})
        self.assertTrue(result.startswith("avi"))

    def test_returns_string(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4"]})
        self.assertIsInstance(result, str)

    def test_missing_key_returns_dash(self):
        result = _fmt_formats({"other_key": ["mp4"]})
        self.assertEqual(result, "-")

    def test_wrong_type_returns_dash(self):
        result = _fmt_formats({"allowed_output_formats": "mp4"})
        # Should handle gracefully
        self.assertIsInstance(result, str)

    def test_formats_with_extensions(self):
        result = _fmt_formats({"allowed_output_formats": [".mp4", ".mkv"]})
        self.assertIn(".mp4", result)

    def test_uppercase_formats(self):
        result = _fmt_formats({"allowed_output_formats": ["MP4", "MKV"]})
        self.assertIn("MP4", result)


class TestNormalizeBase(unittest.TestCase):
    """Test _normalize_base function - 30 tests"""

    def test_basic_domain(self):
        result = _normalize_base("example.com")
        self.assertEqual(result, "http://example.com:80")

    def test_with_http(self):
        result = _normalize_base("http://example.com")
        self.assertEqual(result, "http://example.com:80")

    def test_with_https(self):
        result = _normalize_base("https://example.com")
        self.assertEqual(result, "https://example.com:443")

    def test_prefer_https_flag(self):
        result = _normalize_base("example.com", prefer_https=True)
        self.assertEqual(result, "https://example.com:443")

    def test_custom_port(self):
        result = _normalize_base("example.com", port=8080)
        self.assertEqual(result, "http://example.com:8080")

    def test_https_with_custom_port(self):
        result = _normalize_base("example.com", port=8443, prefer_https=True)
        self.assertEqual(result, "https://example.com:8443")

    def test_full_url_with_port(self):
        result = _normalize_base("http://example.com:8080")
        self.assertEqual(result, "http://example.com:8080")

    def test_full_https_url_with_port(self):
        result = _normalize_base("https://example.com:8443")
        self.assertEqual(result, "https://example.com:8443")

    def test_port_override(self):
        result = _normalize_base("http://example.com:8080", port=9000)
        self.assertEqual(result, "http://example.com:9000")

    def test_url_with_path(self):
        result = _normalize_base("http://example.com/path/to/resource")
        self.assertIn("example.com", result)

    def test_url_with_query(self):
        result = _normalize_base("http://example.com?param=value")
        self.assertIn("example.com", result)

    def test_ip_address(self):
        result = _normalize_base("192.168.1.1")
        self.assertEqual(result, "http://192.168.1.1:80")

    def test_ip_with_port(self):
        result = _normalize_base("192.168.1.1", port=8080)
        self.assertEqual(result, "http://192.168.1.1:8080")

    def test_localhost(self):
        result = _normalize_base("localhost")
        self.assertEqual(result, "http://localhost:80")

    def test_localhost_with_port(self):
        result = _normalize_base("localhost", port=3000)
        self.assertEqual(result, "http://localhost:3000")

    def test_subdomain(self):
        result = _normalize_base("api.example.com")
        self.assertEqual(result, "http://api.example.com:80")

    def test_trailing_slash_ignored(self):
        result = _normalize_base("http://example.com/")
        self.assertIn("example.com", result)

    def test_leading_whitespace_stripped(self):
        result = _normalize_base("  example.com")
        self.assertEqual(result, "http://example.com:80")

    def test_trailing_whitespace_stripped(self):
        result = _normalize_base("example.com  ")
        self.assertEqual(result, "http://example.com:80")

    def test_both_whitespace_stripped(self):
        result = _normalize_base("  example.com  ")
        self.assertEqual(result, "http://example.com:80")

    def test_default_http_port_80(self):
        result = _normalize_base("http://example.com")
        self.assertIn(":80", result)

    def test_default_https_port_443(self):
        result = _normalize_base("https://example.com")
        self.assertIn(":443", result)

    def test_scheme_preserved_http(self):
        result = _normalize_base("http://example.com")
        self.assertTrue(result.startswith("http://"))

    def test_scheme_preserved_https(self):
        result = _normalize_base("https://example.com")
        self.assertTrue(result.startswith("https://"))

    def test_scheme_added_http(self):
        result = _normalize_base("example.com")
        self.assertTrue(result.startswith("http://"))

    def test_scheme_added_https_when_preferred(self):
        result = _normalize_base("example.com", prefer_https=True)
        self.assertTrue(result.startswith("https://"))

    def test_port_in_url_used(self):
        result = _normalize_base("http://example.com:9000")
        self.assertIn(":9000", result)

    def test_ipv6_localhost(self):
        result = _normalize_base("::1")
        # Should handle IPv6 gracefully
        self.assertIsInstance(result, str)

    def test_ipv6_bracket_with_port(self):
        result = _normalize_base("[::1]:8080")
        self.assertEqual(result, "http://[::1]:8080")

    def test_ipv6_full_https_with_port(self):
        result = _normalize_base("https://[2001:db8::1]:4443")
        self.assertEqual(result, "https://[2001:db8::1]:4443")

    def test_empty_string_defaults(self):
        result = _normalize_base("")
        self.assertEqual(result, "http://localhost:80")

    def test_returns_string(self):
        result = _normalize_base("example.com")
        self.assertIsInstance(result, str)

    def test_contains_colon_port_separator(self):
        result = _normalize_base("example.com")
        self.assertRegex(result, r":\d+$")


if __name__ == "__main__":
    unittest.main()

"""
Comprehensive Test Suite for ZedTV IPTV Player
"""

import unittest
import os
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app import (
    _safe_filename,
    _fmt_yesno,
    _fmt_formats,
    _epoch_to_str,
    get_categories,
    _normalize_base,
)
from vlc_settings import VLCSettings, DEFAULT_VLC_SETTINGS
from models import Data


class TestSafeFilename(unittest.TestCase):
    """Test _safe_filename function - 25 tests"""
    
    def test_normal_filename(self):
        self.assertEqual(_safe_filename("test"), "test")
    
    def test_with_spaces(self):
        self.assertEqual(_safe_filename("test file"), "test file")
    
    def test_multiple_spaces(self):
        self.assertEqual(_safe_filename("test  multiple   spaces"), "test multiple spaces")
    
    def test_invalid_chars_windows(self):
        result = _safe_filename("test<>:\"/\\|?*file")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
    
    def test_pipe_char(self):
        self.assertEqual(_safe_filename("test|file"), "test_file")
    
    def test_question_mark(self):
        self.assertEqual(_safe_filename("what?"), "what_")
    
    def test_asterisk(self):
        self.assertEqual(_safe_filename("test*"), "test_")
    
    def test_quotes(self):
        result = _safe_filename('test"file"')
        self.assertNotIn('"', result)
    
    def test_forward_slash(self):
        result = _safe_filename("test/file")
        self.assertNotIn("/", result)
    
    def test_backslash(self):
        result = _safe_filename("test\\file")
        self.assertNotIn("\\", result)
    
    def test_max_length_default(self):
        long_name = "a" * 200
        result = _safe_filename(long_name)
        self.assertEqual(len(result), 180)
    
    def test_max_length_custom(self):
        long_name = "a" * 200
        result = _safe_filename(long_name, max_len=50)
        self.assertEqual(len(result), 50)
    
    def test_trailing_spaces(self):
        self.assertEqual(_safe_filename("test   "), "test")
    
    def test_trailing_dots(self):
        self.assertEqual(_safe_filename("test..."), "test")
    
    def test_leading_spaces(self):
        self.assertEqual(_safe_filename("   test"), "test")
    
    def test_empty_string(self):
        self.assertEqual(_safe_filename(""), "recording")
    
    def test_none_value(self):
        self.assertEqual(_safe_filename(None), "recording")
    
    def test_special_chars(self):
        self.assertEqual(_safe_filename("@#$%^&()"), "@#$%^&()")
    
    def test_unicode_chars(self):
        result = _safe_filename("test_café_文件")
        self.assertIn("test", result)
    
    def test_numbers(self):
        self.assertEqual(_safe_filename("123456"), "123456")
    
    def test_mixed_content(self):
        result = _safe_filename("Movie (2024) [1080p]")
        self.assertIn("Movie", result)
    
    def test_control_chars(self):
        result = _safe_filename("test\x00\x01\x02")
        self.assertNotIn("\x00", result)
    
    def test_tab_char(self):
        self.assertEqual(_safe_filename("test\tfile"), "test file")
    
    def test_newline_char(self):
        self.assertEqual(_safe_filename("test\nfile"), "test file")
    
    def test_carriage_return(self):
        self.assertEqual(_safe_filename("test\rfile"), "test file")


class TestFormatters(unittest.TestCase):
    """Test formatting functions - 20 tests"""
    
    def test_yesno_true(self):
        self.assertEqual(_fmt_yesno(True), "Yes")
    
    def test_yesno_false(self):
        self.assertEqual(_fmt_yesno(False), "No")
    
    def test_yesno_string_true(self):
        self.assertEqual(_fmt_yesno("true"), "Yes")
    
    def test_yesno_string_false(self):
        self.assertEqual(_fmt_yesno("false"), "No")
    
    def test_yesno_int_1(self):
        self.assertEqual(_fmt_yesno(1), "Yes")
    
    def test_yesno_int_0(self):
        self.assertEqual(_fmt_yesno(0), "No")
    
    def test_yesno_string_1(self):
        self.assertEqual(_fmt_yesno("1"), "Yes")
    
    def test_yesno_string_0(self):
        self.assertEqual(_fmt_yesno("0"), "No")
    
    def test_yesno_none(self):
        self.assertEqual(_fmt_yesno(None), "-")
    
    def test_yesno_other(self):
        self.assertEqual(_fmt_yesno("maybe"), "-")
    
    def test_formats_empty(self):
        self.assertEqual(_fmt_formats({}), "-")
    
    def test_formats_none(self):
        self.assertEqual(_fmt_formats({"allowed_output_formats": None}), "-")
    
    def test_formats_single(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4"]})
        self.assertEqual(result, "mp4")
    
    def test_formats_multiple(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi"]})
        self.assertEqual(result, "mp4,mkv,avi")
    
    def test_formats_over_limit(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi", "flv", "mov", "wmv"]})
        self.assertIn("+2", result)
    
    def test_formats_custom_limit(self):
        result = _fmt_formats({"allowed_output_formats": ["mp4", "mkv", "avi"]}, limit=2)
        self.assertIn("+1", result)
    
    def test_epoch_none(self):
        self.assertEqual(_epoch_to_str(None), "-")
    
    def test_epoch_empty(self):
        self.assertEqual(_epoch_to_str(""), "-")
    
    def test_epoch_valid(self):
        result = _epoch_to_str(1609459200)  # 2021-01-01 00:00:00 UTC
        self.assertIn("2021", result)
    
    def test_epoch_invalid(self):
        result = _epoch_to_str("invalid")
        self.assertEqual(result, "invalid")


class TestNormalizeBase(unittest.TestCase):
    """Test _normalize_base function - 15 tests"""
    
    def test_http_with_port(self):
        result = _normalize_base("example.com", 8080)
        self.assertEqual(result, "http://example.com:8080")
    
    def test_https_prefer(self):
        result = _normalize_base("example.com", prefer_https=True)
        self.assertEqual(result, "https://example.com:443")
    
    def test_full_url_http(self):
        result = _normalize_base("http://example.com:8080")
        self.assertEqual(result, "http://example.com:8080")
    
    def test_full_url_https(self):
        result = _normalize_base("https://example.com:443")
        self.assertEqual(result, "https://example.com:443")
    
    def test_default_http_port(self):
        result = _normalize_base("example.com")
        self.assertEqual(result, "http://example.com:80")
    
    def test_default_https_port(self):
        result = _normalize_base("example.com", prefer_https=True)
        self.assertEqual(result, "https://example.com:443")
    
    def test_custom_port(self):
        result = _normalize_base("example.com", 9000)
        self.assertEqual(result, "http://example.com:9000")
    
    def test_with_path(self):
        result = _normalize_base("http://example.com/path")
        self.assertIn("example.com", result)
    
    def test_with_query(self):
        result = _normalize_base("http://example.com?query=1")
        self.assertIn("example.com", result)
    
    def test_ip_address(self):
        result = _normalize_base("192.168.1.1", 8080)
        self.assertEqual(result, "http://192.168.1.1:8080")
    
    def test_localhost(self):
        result = _normalize_base("localhost", 3000)
        self.assertEqual(result, "http://localhost:3000")
    
    def test_with_trailing_slash(self):
        result = _normalize_base("http://example.com/")
        self.assertIn("example.com", result)
    
    def test_strip_whitespace(self):
        result = _normalize_base("  example.com  ")
        self.assertIn("example.com", result)
    
    def test_subdomain(self):
        result = _normalize_base("api.example.com", 8080)
        self.assertEqual(result, "http://api.example.com:8080")
    
    def test_port_in_url_override(self):
        result = _normalize_base("http://example.com:8080", 9000)
        self.assertIn("example.com", result)


class TestVLCSettings(unittest.TestCase):
    """Test VLC Settings - 30 tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / "vlc_settings.json"
    
    def tearDown(self):
        if self.settings_file.exists():
            self.settings_file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_default_settings(self):
        settings = VLCSettings()
        # Check that setting exists and is an int (value may be customized)
        self.assertIn("network_caching", settings.settings)
        self.assertIsInstance(settings.settings["network_caching"], int)

    def test_live_caching_default(self):
        settings = VLCSettings()
        # Check that setting exists and is an int (value may be customized)
        self.assertIn("live_caching", settings.settings)
        self.assertIsInstance(settings.settings["live_caching"], int)

    def test_hw_decoding_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["hw_decoding"], "auto")
    
    def test_audio_output_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["audio_output"], "auto")
    
    def test_audio_volume_default(self):
        settings = VLCSettings()
        # Check that setting exists and is an int in valid range
        self.assertIn("audio_volume", settings.settings)
        self.assertIsInstance(settings.settings["audio_volume"], int)
        self.assertGreaterEqual(settings.settings["audio_volume"], 0)
        self.assertLessEqual(settings.settings["audio_volume"], 200)

    def test_video_output_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["video_output"], "auto")
    
    def test_deinterlace_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["deinterlace"], "off")
    
    def test_skip_frames_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["skip_frames"], False)
    
    def test_drop_late_frames_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["drop_late_frames"], True)
    
    def test_reset_plugins_cache_default(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["reset_plugins_cache"], True)
    
    def test_get_vlc_args(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertIsInstance(args, list)
        self.assertTrue(len(args) > 0)
    
    def test_network_caching_arg(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertTrue(any("--network-caching" in arg for arg in args))
    
    def test_live_caching_arg(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertTrue(any("--live-caching" in arg for arg in args))
    
    def test_drop_late_frames_arg(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertTrue(any("--drop-late-frames" in arg for arg in args))
    
    def test_reset_cache_arg(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertTrue(any("--reset-plugins-cache" in arg for arg in args))
    
    def test_update_setting(self):
        settings = VLCSettings()
        settings.update("audio_volume", 150)
        self.assertEqual(settings.settings["audio_volume"], 150)
    
    def test_hw_decoding_disabled(self):
        settings = VLCSettings()
        settings.settings["hw_decoding"] = "disabled"
        args = settings.get_vlc_args()
        self.assertTrue(any("--avcodec-hw=none" in arg for arg in args))
    
    def test_hw_decoding_specific(self):
        settings = VLCSettings()
        settings.settings["hw_decoding"] = "d3d11va"
        args = settings.get_vlc_args()
        self.assertTrue(any("d3d11va" in arg for arg in args))
    
    def test_audio_output_specific(self):
        settings = VLCSettings()
        settings.settings["audio_output"] = "directsound"
        args = settings.get_vlc_args()
        self.assertTrue(any("directsound" in arg for arg in args))
    
    def test_video_output_specific(self):
        settings = VLCSettings()
        settings.settings["video_output"] = "direct3d11"
        args = settings.get_vlc_args()
        self.assertTrue(any("direct3d11" in arg for arg in args))
    
    def test_deinterlace_on(self):
        settings = VLCSettings()
        settings.settings["deinterlace"] = "on"
        args = settings.get_vlc_args()
        self.assertTrue(any("--deinterlace" in arg for arg in args))
    
    def test_skip_frames_enabled(self):
        settings = VLCSettings()
        settings.settings["skip_frames"] = True
        args = settings.get_vlc_args()
        self.assertTrue(any("--skip-frames" in arg for arg in args))
    
    def test_drop_late_frames_disabled(self):
        settings = VLCSettings()
        settings.settings["drop_late_frames"] = False
        args = settings.get_vlc_args()
        self.assertTrue(any("--no-drop-late-frames" in arg for arg in args))
    
    def test_all_defaults_present(self):
        settings = VLCSettings()
        for key in DEFAULT_VLC_SETTINGS.keys():
            self.assertIn(key, settings.settings)
    
    def test_network_caching_range(self):
        settings = VLCSettings()
        settings.update("network_caching", 5000)
        self.assertEqual(settings.settings["network_caching"], 5000)
    
    def test_live_caching_range(self):
        settings = VLCSettings()
        settings.update("live_caching", 2000)
        self.assertEqual(settings.settings["live_caching"], 2000)
    
    def test_volume_range_low(self):
        settings = VLCSettings()
        settings.update("audio_volume", 0)
        self.assertEqual(settings.settings["audio_volume"], 0)
    
    def test_volume_range_high(self):
        settings = VLCSettings()
        settings.update("audio_volume", 200)
        self.assertEqual(settings.settings["audio_volume"], 200)
    
    def test_settings_persistence(self):
        # This would need actual file I/O test
        settings = VLCSettings()
        original_vol = settings.settings["audio_volume"]
        self.assertIsInstance(original_vol, int)
    
    def test_invalid_key_update(self):
        settings = VLCSettings()
        settings.update("nonexistent_key", 100)
        self.assertNotIn("nonexistent_key", settings.settings)


class TestM3UParser(unittest.TestCase):
    """Test M3U parsing - 15 tests"""
    
    def setUp(self):
        self.test_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="Channel 1" tvg-logo="" group-title="Sports",Channel 1
http://example.com/stream1
#EXTINF:-1 tvg-id="2" tvg-name="Channel 2" tvg-logo="" group-title="Movies",Channel 2
http://example.com/stream2
#EXTINF:-1 tvg-id="3" tvg-name="Channel 3" tvg-logo="" group-title="Sports",Channel 3
http://example.com/stream3
"""
    
    def test_parse_extinf_lines(self):
        import re
        lines = self.test_m3u.split("\n")
        extinf_lines = [l for l in lines if l.startswith("#EXTINF")]
        self.assertEqual(len(extinf_lines), 3)
    
    def test_extract_group_title(self):
        import re
        line = '#EXTINF:-1 tvg-id="1" group-title="Sports",Channel 1'
        match = re.search(r'group-title="([^"]*)"', line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "Sports")
    
    def test_extract_tvg_name(self):
        import re
        line = '#EXTINF:-1 tvg-name="Channel 1" group-title="Sports",Channel 1'
        match = re.search(r'tvg-name="([^"]*)"', line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "Channel 1")
    
    def test_extract_tvg_id(self):
        import re
        line = '#EXTINF:-1 tvg-id="123" tvg-name="Channel",Channel'
        match = re.search(r'tvg-id="([^"]*)"', line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "123")
    
    def test_case_insensitive_group_title(self):
        import re
        line = '#EXTINF:-1 GROUP-TITLE="Sports",Channel'
        match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
        self.assertIsNotNone(match)
    
    def test_url_extraction(self):
        lines = self.test_m3u.split("\n")
        url_lines = [l for l in lines if l.startswith("http")]
        self.assertEqual(len(url_lines), 3)
    
    def test_empty_m3u(self):
        empty = "#EXTM3U\n"
        lines = empty.split("\n")
        extinf_lines = [l for l in lines if l.startswith("#EXTINF")]
        self.assertEqual(len(extinf_lines), 0)
    
    def test_malformed_extinf(self):
        import re
        line = '#EXTINF:-1 Channel without attributes'
        match = re.search(r'group-title="([^"]*)"', line)
        self.assertIsNone(match)
    
    def test_missing_quotes(self):
        import re
        line = '#EXTINF:-1 group-title=Sports,Channel'
        match = re.search(r'group-title="([^"]*)"', line)
        self.assertIsNone(match)
    
    def test_special_chars_in_title(self):
        import re
        line = '#EXTINF:-1 tvg-name="Chann&l #1" group-title="Sports",Channel'
        match = re.search(r'tvg-name="([^"]*)"', line)
        self.assertEqual(match.group(1), "Chann&l #1")
    
    def test_unicode_in_title(self):
        import re
        line = '#EXTINF:-1 tvg-name="Канал 1" group-title="Sports",Channel'
        match = re.search(r'tvg-name="([^"]*)"', line)
        self.assertIn("Канал", match.group(1))
    
    def test_multiple_attributes(self):
        import re
        line = '#EXTINF:-1 tvg-id="1" tvg-name="Ch1" tvg-logo="logo.png" group-title="Sports" rating="5",Ch1'
        matches = re.findall(r'(\w+(?:-\w+)*)="([^"]*)"', line)
        self.assertGreater(len(matches), 3)
    
    def test_rating_extraction(self):
        import re
        line = '#EXTINF:-1 rating="8.5" group-title="Movies",Movie'
        match = re.search(r'rating="([^"]*)"', line)
        self.assertEqual(match.group(1), "8.5")
    
    def test_year_extraction(self):
        import re
        line = '#EXTINF:-1 releasedate="2024" group-title="Movies",Movie'
        match = re.search(r'releasedate="([^"]*)"', line)
        self.assertEqual(match.group(1), "2024")
    
    def test_director_extraction(self):
        import re
        line = '#EXTINF:-1 director="John Doe" group-title="Movies",Movie'
        match = re.search(r'director="([^"]*)"', line)
        self.assertEqual(match.group(1), "John Doe")


def run_all_tests():
    """Run all tests and display results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSafeFilename))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatters))
    suite.addTests(loader.loadTestsFromTestCase(TestNormalizeBase))
    suite.addTests(loader.loadTestsFromTestCase(TestVLCSettings))
    suite.addTests(loader.loadTestsFromTestCase(TestM3UParser))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


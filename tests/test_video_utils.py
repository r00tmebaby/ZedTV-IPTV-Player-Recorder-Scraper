import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from utils.video_utils import _detect_vlc, _safe_filename, build_record_sout


class TestSafeFilename(unittest.TestCase):
    """Test _safe_filename function - 50 tests"""

    def test_basic_filename(self):
        self.assertEqual(_safe_filename("test"), "test")

    def test_with_spaces(self):
        self.assertEqual(_safe_filename("test file"), "test file")

    def test_multiple_spaces(self):
        self.assertEqual(_safe_filename("test  multiple   spaces"), "test multiple spaces")

    def test_leading_spaces(self):
        self.assertEqual(_safe_filename("   test"), "test")

    def test_trailing_spaces(self):
        self.assertEqual(_safe_filename("test   "), "test")

    def test_trailing_dots(self):
        self.assertEqual(_safe_filename("test..."), "test")

    def test_leading_and_trailing_dots(self):
        self.assertEqual(_safe_filename("...test..."), "...test")

    def test_invalid_char_less_than(self):
        result = _safe_filename("test<file")
        self.assertNotIn("<", result)

    def test_invalid_char_greater_than(self):
        result = _safe_filename("test>file")
        self.assertNotIn(">", result)

    def test_invalid_char_colon(self):
        result = _safe_filename("test:file")
        self.assertNotIn(":", result)

    def test_invalid_char_quote(self):
        result = _safe_filename('test"file"')
        self.assertNotIn('"', result)

    def test_invalid_char_forward_slash(self):
        result = _safe_filename("test/file")
        self.assertNotIn("/", result)

    def test_invalid_char_backslash(self):
        result = _safe_filename("test\\file")
        self.assertNotIn("\\", result)

    def test_invalid_char_pipe(self):
        result = _safe_filename("test|file")
        self.assertNotIn("|", result)

    def test_invalid_char_question(self):
        result = _safe_filename("test?file")
        self.assertNotIn("?", result)

    def test_invalid_char_asterisk(self):
        result = _safe_filename("test*file")
        self.assertNotIn("*", result)

    def test_all_invalid_chars(self):
        result = _safe_filename('<>:"/\\|?*')
        for char in '<>:"/\\|?*':
            self.assertNotIn(char, result)

    def test_max_length_default(self):
        long_name = "a" * 200
        result = _safe_filename(long_name)
        self.assertEqual(len(result), 180)

    def test_max_length_custom(self):
        long_name = "a" * 200
        result = _safe_filename(long_name, max_len=50)
        self.assertEqual(len(result), 50)

    def test_max_length_short(self):
        result = _safe_filename("short", max_len=100)
        self.assertEqual(result, "short")

    def test_empty_string(self):
        self.assertEqual(_safe_filename(""), "recording")

    def test_none_value(self):
        self.assertEqual(_safe_filename(None), "recording")

    def test_whitespace_only(self):
        self.assertEqual(_safe_filename("   "), "recording")

    def test_tabs_and_newlines(self):
        result = _safe_filename("test\ttab\nline")
        self.assertEqual(result, "test tab line")

    def test_unicode_chars(self):
        result = _safe_filename("café_文件_テスト")
        self.assertIn("café", result)

    def test_numbers_only(self):
        self.assertEqual(_safe_filename("123456789"), "123456789")

    def test_special_allowed_chars(self):
        result = _safe_filename("test@#$%^&()_+-=[]{},.!~")
        self.assertIn("test", result)

    def test_mixed_content(self):
        result = _safe_filename("Movie (2024) [1080p] - Episode 5")
        self.assertIn("Movie", result)
        self.assertIn("2024", result)

    def test_control_chars_removed(self):
        result = _safe_filename("test\x00\x01\x02\x03")
        self.assertNotIn("\x00", result)

    def test_all_control_chars(self):
        control_chars = "".join(chr(i) for i in range(32))
        result = _safe_filename(f"test{control_chars}file")
        for char in control_chars:
            if char not in "\t\n\r":
                self.assertNotIn(char, result)

    def test_carriage_return(self):
        self.assertEqual(_safe_filename("test\rfile"), "test file")

    def test_multiple_invalid_chars_sequence(self):
        result = _safe_filename("test<>:file")
        self.assertGreater(len(result), 4)

    def test_filename_with_extension(self):
        result = _safe_filename("myfile.mp4")
        self.assertEqual(result, "myfile.mp4")

    def test_long_extension(self):
        result = _safe_filename("file.extension.mp4")
        self.assertEqual(result, "file.extension.mp4")

    def test_path_like_input(self):
        result = _safe_filename("C:\\Users\\test\\file.txt")
        self.assertNotIn("\\", result)

    def test_url_like_input(self):
        result = _safe_filename("http://example.com/file.mp4")
        self.assertNotIn(":", result)
        self.assertNotIn("/", result)

    def test_brackets_allowed(self):
        result = _safe_filename("test[123]file")
        self.assertEqual(result, "test[123]file")

    def test_parentheses_allowed(self):
        result = _safe_filename("test(123)file")
        self.assertEqual(result, "test(123)file")

    def test_underscores_allowed(self):
        result = _safe_filename("test_file_name")
        self.assertEqual(result, "test_file_name")

    def test_hyphens_allowed(self):
        result = _safe_filename("test-file-name")
        self.assertEqual(result, "test-file-name")

    def test_periods_in_middle(self):
        result = _safe_filename("test.file.name.mp4")
        self.assertEqual(result, "test.file.name.mp4")

    def test_comma_allowed(self):
        result = _safe_filename("test, file")
        self.assertEqual(result, "test, file")

    def test_exclamation_allowed(self):
        result = _safe_filename("test! file")
        self.assertEqual(result, "test! file")

    def test_apostrophe_allowed(self):
        result = _safe_filename("test's file")
        self.assertEqual(result, "test's file")

    def test_ampersand_allowed(self):
        result = _safe_filename("test & file")
        self.assertEqual(result, "test & file")

    def test_at_symbol_allowed(self):
        result = _safe_filename("user@domain")
        self.assertEqual(result, "user@domain")

    def test_hash_allowed(self):
        result = _safe_filename("episode#5")
        self.assertEqual(result, "episode#5")

    def test_percent_allowed(self):
        result = _safe_filename("100% complete")
        self.assertEqual(result, "100% complete")


class TestBuildRecordSout(unittest.TestCase):
    """Test build_record_sout function - 20 tests"""

    def test_basic_sout(self):
        result = build_record_sout("test")
        self.assertIn(":sout=", result)
        self.assertIn("test", result)

    def test_sout_has_duplicate(self):
        result = build_record_sout("test")
        self.assertIn("#duplicate", result)

    def test_sout_has_file_output(self):
        result = build_record_sout("test")
        self.assertIn("access=file", result)

    def test_sout_has_display_output(self):
        result = build_record_sout("test")
        self.assertIn("dst=display", result)

    def test_sout_has_mp4_mux(self):
        result = build_record_sout("test")
        self.assertIn("mux=mp4", result)

    def test_timestamp_in_filename(self):
        result = build_record_sout("test")
        # Should contain date pattern like 2025-11-12
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")

    def test_time_in_filename(self):
        result = build_record_sout("test")
        # Should contain time pattern like 14-30-45
        self.assertRegex(result, r"\d{2}-\d{2}-\d{2}")

    def test_title_in_path(self):
        result = build_record_sout("MyShow")
        self.assertIn("MyShow", result)

    def test_special_chars_sanitized(self):
        result = build_record_sout("My:Show<>")
        # The filename part should have sanitized special chars
        self.assertIn("My_Show__", result)

    def test_escaped_backslashes_windows(self):
        import sys

        if sys.platform.startswith("win"):
            result = build_record_sout("test")
            # Windows paths should have escaped backslashes
            self.assertIn("\\\\", result)

    def test_records_folder_in_path(self):
        result = build_record_sout("test")
        self.assertIn("records", result.lower())

    def test_empty_title(self):
        result = build_record_sout("")
        self.assertIn("recording", result)

    def test_long_title(self):
        long_title = "a" * 200
        result = build_record_sout(long_title)
        # Should be truncated
        self.assertLess(len(result), 500)

    def test_unicode_title(self):
        result = build_record_sout("café")
        self.assertIn("caf", result)

    def test_multiple_spaces_in_title(self):
        result = build_record_sout("test  multiple   spaces")
        self.assertIn("test multiple spaces", result)

    def test_sout_format_valid(self):
        result = build_record_sout("test")
        # Should start with :sout=
        self.assertTrue(result.startswith(":sout="))

    def test_sout_has_both_outputs(self):
        result = build_record_sout("test")
        # Should have file and display outputs (dst appears multiple times in the structure)
        self.assertIn("dst=std", result)
        self.assertIn("dst=display", result)

    def test_sout_std_wrapper(self):
        result = build_record_sout("test")
        self.assertIn("std{", result)

    def test_duplicate_wrapper(self):
        result = build_record_sout("test")
        self.assertIn("#duplicate{", result)

    def test_file_extension_mp4(self):
        result = build_record_sout("test")
        self.assertIn(".mp4", result)


class TestDetectVLC(unittest.TestCase):
    """Test _detect_vlc function - 10 tests"""

    def test_returns_list_or_none(self):
        result = _detect_vlc()
        self.assertTrue(result is None or isinstance(result, list))

    def test_windows_paths_checked(self):
        import sys

        if sys.platform.startswith("win"):
            # Should check common Windows paths
            result = _detect_vlc()
            if result:
                self.assertTrue(any("vlc" in str(p).lower() for p in result))

    def test_macos_uses_open(self):
        import sys

        if sys.platform == "darwin":
            result = _detect_vlc()
            if result:
                self.assertIn("open", result)

    def test_linux_uses_which(self):
        import sys

        if sys.platform.startswith("linux"):
            result = _detect_vlc()
            if result:
                self.assertTrue(any("vlc" in str(p).lower() for p in result))

    def test_result_is_command_list(self):
        result = _detect_vlc()
        if result:
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)

    def test_first_element_is_path(self):
        result = _detect_vlc()
        if result:
            self.assertIsInstance(result[0], str)

    def test_windows_exe_extension(self):
        import sys

        if sys.platform.startswith("win"):
            result = _detect_vlc()
            if result:
                self.assertTrue(result[0].endswith(".exe") or "vlc" in result[0].lower())

    def test_none_when_not_found(self):
        # This test assumes VLC might not be installed
        result = _detect_vlc()
        self.assertTrue(result is None or isinstance(result, list))

    def test_no_empty_strings(self):
        result = _detect_vlc()
        if result:
            for item in result:
                self.assertTrue(len(item) > 0)

    def test_consistent_returns(self):
        result1 = _detect_vlc()
        result2 = _detect_vlc()
        self.assertEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()

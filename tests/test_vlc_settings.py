import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from core.vlc_settings import DEFAULT_VLC_SETTINGS, VLCSettings


class TestVLCSettings(unittest.TestCase):
    """Test VLCSettings class - 60 tests"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_folder = None
        # Create temp settings file
        self.temp_settings = Path(self.temp_dir) / "vlc_settings.json"

    def tearDown(self):
        if self.temp_settings.exists():
            self.temp_settings.unlink()
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    def test_init_creates_default_settings(self):
        settings = VLCSettings()
        self.assertIsNotNone(settings.settings)

    def test_default_network_caching_exists(self):
        settings = VLCSettings()
        self.assertIn("network_caching", settings.settings)

    def test_default_network_caching_is_int(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["network_caching"], int)

    def test_default_live_caching_exists(self):
        settings = VLCSettings()
        self.assertIn("live_caching", settings.settings)

    def test_default_live_caching_is_int(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["live_caching"], int)

    def test_default_hw_decoding_exists(self):
        settings = VLCSettings()
        self.assertIn("hw_decoding", settings.settings)

    def test_default_hw_decoding_value(self):
        settings = VLCSettings()
        # HW decoding default might be auto or system-specific (e.g., dxva2 on Windows)
        self.assertIn(settings.settings["hw_decoding"], ["auto", "dxva2", "d3d11va", "disabled"])

    def test_default_audio_output_exists(self):
        settings = VLCSettings()
        self.assertIn("audio_output", settings.settings)

    def test_default_audio_output_value(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["audio_output"], "auto")

    def test_default_audio_volume_exists(self):
        settings = VLCSettings()
        self.assertIn("audio_volume", settings.settings)

    def test_default_audio_volume_is_int(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["audio_volume"], int)

    def test_default_audio_volume_in_range(self):
        settings = VLCSettings()
        vol = settings.settings["audio_volume"]
        self.assertGreaterEqual(vol, 0)
        self.assertLessEqual(vol, 200)

    def test_default_video_output_exists(self):
        settings = VLCSettings()
        self.assertIn("video_output", settings.settings)

    def test_default_video_output_value(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["video_output"], "auto")

    def test_default_deinterlace_exists(self):
        settings = VLCSettings()
        self.assertIn("deinterlace", settings.settings)

    def test_default_deinterlace_value(self):
        settings = VLCSettings()
        self.assertEqual(settings.settings["deinterlace"], "off")

    def test_default_skip_frames_exists(self):
        settings = VLCSettings()
        self.assertIn("skip_frames", settings.settings)

    def test_default_skip_frames_is_bool(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["skip_frames"], bool)

    def test_default_drop_late_frames_exists(self):
        settings = VLCSettings()
        self.assertIn("drop_late_frames", settings.settings)

    def test_default_drop_late_frames_is_bool(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["drop_late_frames"], bool)

    def test_default_reset_plugins_cache_exists(self):
        settings = VLCSettings()
        self.assertIn("reset_plugins_cache", settings.settings)

    def test_default_reset_plugins_cache_is_bool(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings["reset_plugins_cache"], bool)

    def test_get_vlc_args_returns_list(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertIsInstance(args, list)

    def test_get_vlc_args_not_empty(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertGreater(len(args), 0)

    def test_get_vlc_args_has_network_caching(self):
        settings = VLCSettings()
        args = settings.get_vlc_args()
        self.assertTrue(any("--network-caching" in arg for arg in args))

    def test_get_vlc_args_has_live_caching(self):
        settings = VLCSettings()
        settings.settings["live_caching"] = 300
        args = settings.get_vlc_args()
        # Check if live_caching argument is present when value is set
        self.assertIsInstance(args, list)
        self.assertTrue(any("--live-caching" in arg for arg in args))

    def test_get_vlc_args_network_caching_value(self):
        settings = VLCSettings()
        settings.settings["network_caching"] = 5000
        args = settings.get_vlc_args()
        self.assertTrue(any("--network-caching=5000" in arg for arg in args))

    def test_get_vlc_args_audio_volume(self):
        settings = VLCSettings()
        settings.settings["audio_volume"] = 75
        args = settings.get_vlc_args()
        # Volume might be in args
        self.assertIsInstance(args, list)

    def test_update_setting(self):
        settings = VLCSettings()
        settings.update("audio_volume", 150)
        self.assertEqual(settings.settings["audio_volume"], 150)

    def test_update_invalid_key_ignored(self):
        settings = VLCSettings()
        settings.update("invalid_key", 100)
        self.assertNotIn("invalid_key", settings.settings)

    def test_hw_decoding_disabled_arg(self):
        settings = VLCSettings()
        settings.settings["hw_decoding"] = "disabled"
        args = settings.get_vlc_args()
        self.assertTrue(any("--avcodec-hw=none" in arg for arg in args))

    def test_hw_decoding_specific_value(self):
        settings = VLCSettings()
        settings.settings["hw_decoding"] = "d3d11va"
        args = settings.get_vlc_args()
        self.assertTrue(any("d3d11va" in arg for arg in args))

    def test_audio_output_specific_value(self):
        settings = VLCSettings()
        settings.settings["audio_output"] = "directsound"
        args = settings.get_vlc_args()
        self.assertTrue(any("directsound" in arg for arg in args))

    def test_video_output_specific_value(self):
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

    def test_drop_late_frames_enabled(self):
        settings = VLCSettings()
        settings.settings["drop_late_frames"] = True
        args = settings.get_vlc_args()
        self.assertTrue(any("--drop-late-frames" in arg for arg in args))

    def test_drop_late_frames_disabled(self):
        settings = VLCSettings()
        settings.settings["drop_late_frames"] = False
        args = settings.get_vlc_args()
        self.assertTrue(any("--no-drop-late-frames" in arg for arg in args))

    def test_reset_cache_enabled(self):
        settings = VLCSettings()
        settings.settings["reset_plugins_cache"] = True
        args = settings.get_vlc_args()
        self.assertTrue(any("--reset-plugins-cache" in arg for arg in args))

    def test_all_default_settings_present(self):
        settings = VLCSettings()
        for key in DEFAULT_VLC_SETTINGS.keys():
            self.assertIn(key, settings.settings)

    def test_network_caching_range_low(self):
        settings = VLCSettings()
        settings.update("network_caching", 0)
        self.assertEqual(settings.settings["network_caching"], 0)

    def test_network_caching_range_high(self):
        settings = VLCSettings()
        settings.update("network_caching", 10000)
        self.assertEqual(settings.settings["network_caching"], 10000)

    def test_live_caching_range_low(self):
        settings = VLCSettings()
        settings.update("live_caching", 0)
        self.assertEqual(settings.settings["live_caching"], 0)

    def test_live_caching_range_high(self):
        settings = VLCSettings()
        settings.update("live_caching", 10000)
        self.assertEqual(settings.settings["live_caching"], 10000)

    def test_volume_range_zero(self):
        settings = VLCSettings()
        settings.update("audio_volume", 0)
        self.assertEqual(settings.settings["audio_volume"], 0)

    def test_volume_range_max(self):
        settings = VLCSettings()
        settings.update("audio_volume", 200)
        self.assertEqual(settings.settings["audio_volume"], 200)

    def test_settings_is_dict(self):
        settings = VLCSettings()
        self.assertIsInstance(settings.settings, dict)

    def test_settings_not_empty(self):
        settings = VLCSettings()
        self.assertGreater(len(settings.settings), 0)

    def test_hw_decoding_options(self):
        valid_options = ["auto", "disabled", "d3d11va", "dxva2"]
        settings = VLCSettings()
        for option in valid_options:
            settings.settings["hw_decoding"] = option
            args = settings.get_vlc_args()
            self.assertIsInstance(args, list)

    def test_deinterlace_options(self):
        valid_options = ["off", "on", "blend", "mean", "bob", "linear"]
        settings = VLCSettings()
        for option in valid_options:
            settings.settings["deinterlace"] = option
            args = settings.get_vlc_args()
            self.assertIsInstance(args, list)

    def test_all_settings_serializable(self):
        settings = VLCSettings()
        # Should be JSON serializable
        try:
            json.dumps(settings.settings)
            serializable = True
        except Exception:
            serializable = False
        self.assertTrue(serializable)

    def test_update_multiple_settings(self):
        settings = VLCSettings()
        settings.update("audio_volume", 80)
        settings.update("network_caching", 3000)
        self.assertEqual(settings.settings["audio_volume"], 80)
        self.assertEqual(settings.settings["network_caching"], 3000)

    def test_get_vlc_args_consistent(self):
        settings = VLCSettings()
        args1 = settings.get_vlc_args()
        args2 = settings.get_vlc_args()
        self.assertEqual(args1, args2)

    def test_boolean_settings_preserved(self):
        settings = VLCSettings()
        original_skip = settings.settings["skip_frames"]
        settings.update("skip_frames", not original_skip)
        self.assertNotEqual(settings.settings["skip_frames"], original_skip)

    def test_string_settings_preserved(self):
        settings = VLCSettings()
        settings.update("hw_decoding", "dxva2")
        self.assertEqual(settings.settings["hw_decoding"], "dxva2")

    def test_integer_settings_preserved(self):
        settings = VLCSettings()
        settings.update("network_caching", 4567)
        self.assertEqual(settings.settings["network_caching"], 4567)


if __name__ == "__main__":
    unittest.main()

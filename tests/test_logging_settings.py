import os
import json
import unittest
from pathlib import Path

from src.logging_settings import LoggingSettings, LoggingConfig, LOGGING_SETTINGS_FILE


class TestLoggingSettings(unittest.TestCase):
    def setUp(self):
        # Backup and remove existing file if present
        self._bak = None
        if LOGGING_SETTINGS_FILE.exists():
            self._bak = LOGGING_SETTINGS_FILE.read_text(encoding="utf-8")
            LOGGING_SETTINGS_FILE.unlink(missing_ok=True)

    def tearDown(self):
        if self._bak is not None:
            LOGGING_SETTINGS_FILE.write_text(self._bak, encoding="utf-8")

    def test_default_load(self):
        ls = LoggingSettings()
        self.assertIsInstance(ls.settings, LoggingConfig)
        self.assertIn(ls.settings.level, ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    def test_save_and_load(self):
        ls = LoggingSettings()
        ls.update(level="DEBUG", max_file_size_mb=2, backup_count=3, retention_days=7, console_enabled=True)
        # Reload
        ls2 = LoggingSettings()
        self.assertEqual(ls2.settings.level, "DEBUG")
        self.assertEqual(ls2.settings.max_file_size_mb, 2)
        self.assertEqual(ls2.settings.backup_count, 3)
        self.assertEqual(ls2.settings.retention_days, 7)
        self.assertTrue(ls2.settings.console_enabled)


if __name__ == '__main__':
    unittest.main()


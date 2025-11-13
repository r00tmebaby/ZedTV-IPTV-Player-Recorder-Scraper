"""
Logging settings manager for ZedTV IPTV Player.
Stores and loads logging configuration used by the application.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from .config import DATA_FOLDER

LOGGING_SETTINGS_FILE = Path(DATA_FOLDER) / "logging_settings.json"


@dataclass
class LoggingConfig:
    # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    level: str = "INFO"
    # Maximum size of a single log file in megabytes before rotation
    max_file_size_mb: int = 5
    # How many rotated log files to keep (per-file base name)
    backup_count: int = 5
    # Remove log files older than this many days from the logs directory (0 = no age cleanup)
    retention_days: int = 14
    # Also echo logs to console/stdout (useful for debugging from terminal)
    console_enabled: bool = False


DEFAULT_LOGGING_CONFIG = LoggingConfig()


class LoggingSettings:
    def __init__(self) -> None:
        self.settings: LoggingConfig = self.load_settings()

    def load_settings(self) -> LoggingConfig:
        try:
            if LOGGING_SETTINGS_FILE.exists():
                raw: Dict[str, Any] = json.loads(LOGGING_SETTINGS_FILE.read_text(encoding="utf-8"))
                # merge defaults with file content (for forward compat)
                merged = asdict(DEFAULT_LOGGING_CONFIG)
                merged.update(raw or {})
                return LoggingConfig(**merged)
        except Exception:
            pass
        return DEFAULT_LOGGING_CONFIG

    def save_settings(self) -> None:
        try:
            LOGGING_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            LOGGING_SETTINGS_FILE.write_text(
                json.dumps(asdict(self.settings), indent=2),
                encoding="utf-8",
            )
        except Exception:
            # fallback: ignore failures silently
            pass

    def update(self, **kwargs: Any) -> None:
        changed = False
        for k, v in kwargs.items():
            if hasattr(self.settings, k):
                setattr(self.settings, k, v)
                changed = True
        if changed:
            self.save_settings()

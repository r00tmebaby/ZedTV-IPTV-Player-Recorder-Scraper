"""
Application logging initialization with rotation and retention.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from __version__ import APP_NAME, __version__

from .config import DATA_FOLDER
from .logging_settings import LoggingConfig, LoggingSettings

LOGS_DIR = Path(DATA_FOLDER) / "logs"
LOG_FILE_BASENAME = "app.log"  # will rotate to app.log.1, app.log.2 ...


def _safe_int(v: int, minimum: int, default: int) -> int:
    try:
        v = int(v)
    except Exception:
        return default
    return max(minimum, v)


def init_logging(settings: Optional[LoggingConfig] = None) -> logging.Logger:
    """Initialize root logger according to settings and return a module logger."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    ls = LoggingSettings().settings if settings is None else settings
    level = getattr(logging, (ls.level or "INFO").upper(), logging.INFO)
    max_bytes = _safe_int(ls.max_file_size_mb, 1, 5) * 1024 * 1024
    backup_count = _safe_int(ls.backup_count, 1, 5)

    # Create handler for rotating file
    logfile = LOGS_DIR / LOG_FILE_BASENAME
    handler = RotatingFileHandler(logfile, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)

    # Configure root logger only once
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if re-initialized
    _seen = []
    for h in list(root.handlers):
        if isinstance(h, RotatingFileHandler):
            _seen.append(h)
    if not _seen:
        root.addHandler(handler)

    # Optional console echo
    if ls.console_enabled:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

    # Write banner
    root.info("\n=== %s v%s started ===", APP_NAME, __version__)
    root.info(
        "Logging level=%s, file=%s, maxMB=%s, backups=%s",
        logging.getLevelName(level),
        str(logfile),
        ls.max_file_size_mb,
        backup_count,
    )

    # Run retention cleanup
    try:
        cleanup_old_logs(retention_days=_safe_int(ls.retention_days, 0, 14))
    except Exception as e:
        root.warning("Log retention cleanup failed: %s", e)

    return logging.getLogger("zedtv")


def cleanup_old_logs(retention_days: int) -> None:
    """Delete rotated log files older than retention_days. If 0, skip."""
    if retention_days <= 0:
        return
    cutoff = datetime.now() - timedelta(days=retention_days)
    if not LOGS_DIR.exists():
        return
    for p in LOGS_DIR.iterdir():
        if not p.is_file():
            continue
        if p.name == LOG_FILE_BASENAME or p.name.startswith(LOG_FILE_BASENAME + "."):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime < cutoff:
                    p.unlink(missing_ok=True)
            except Exception:
                pass

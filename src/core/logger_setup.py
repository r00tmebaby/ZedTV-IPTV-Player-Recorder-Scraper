"""
Application logging initialization with rotation and retention.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import os
from typing import Optional

try:
    from __version__ import APP_NAME, __version__  # type: ignore
except Exception:
    APP_NAME = "ZedTV"
    __version__ = "0.0.0"

from .config import DATA_FOLDER, LOGS_FOLDER
from .logging_settings import LoggingConfig, LoggingSettings

LOG_FILE_BASENAME = "app.log"  # will rotate to app.log.1, app.log.2 ...
# Determine final logs directory early so other modules importing LOGS_DIR get correct path.
_base_override = os.environ.get("LOG_ROOT")
if _base_override:
    LOGS_DIR = Path(_base_override) / "logs"
elif getattr(sys, "frozen", False):
    LOGS_DIR = Path(sys.executable).parent / LOGS_FOLDER
else:
    LOGS_DIR = Path(LOGS_FOLDER)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_int(v: int, minimum: int, default: int) -> int:
    try:
        v = int(v)
    except Exception:
        return default
    return max(minimum, v)


def init_logging(settings: Optional[LoggingConfig] = None) -> logging.Logger:
    """Initialize root logger according to settings and return a module logger.

    Improvements:
    - When frozen, place logs under <exe dir>/data/logs to avoid ambiguous CWD.
    - Allow override via env var LOG_ROOT.
    - Remove delay so file is created immediately; flush after banner.
    """
    # Primary logs dir only (legacy 'logs/')
    target_logs = LOGS_DIR

    ls = LoggingSettings().settings if settings is None else settings
    level = getattr(logging, (ls.level or "INFO").upper(), logging.INFO)
    max_bytes = _safe_int(ls.max_file_size_mb, 1, 5) * 1024 * 1024
    backup_count = _safe_int(ls.backup_count, 1, 5)

    logfile = target_logs / LOG_FILE_BASENAME
    handler_main = RotatingFileHandler(
        logfile,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=False,
    )
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler_main.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    if not any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", "") == str(logfile)
        for h in root.handlers
    ):
        root.addHandler(handler_main)

    if ls.console_enabled or os.environ.get("LOG_CONSOLE") == "1":
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

    root.info("\n=== %s v%s started ===", APP_NAME, __version__)
    root.info(
        "Logging level=%s, file=%s, maxMB=%s, backups=%s",
        logging.getLevelName(level),
        str(logfile),
        ls.max_file_size_mb,
        backup_count,
    )
    root.info(
        "Process frozen=%s exe_dir=%s",
        getattr(sys, "frozen", False),
        (
            Path(sys.executable).parent
            if getattr(sys, "frozen", False)
            else os.getcwd()
        ),
    )

    try:
        cleanup_old_logs(retention_days=_safe_int(ls.retention_days, 0, 14))
    except Exception as e:
        root.warning("Log retention cleanup failed: %s", e)

    # Force flush so file is guaranteed to exist early.
    for h in root.handlers:
        try:
            h.flush()
        except Exception:
            pass

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
        if p.name == LOG_FILE_BASENAME or p.name.startswith(
            LOG_FILE_BASENAME + "."
        ):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime < cutoff:
                    p.unlink(missing_ok=True)
            except Exception:
                pass

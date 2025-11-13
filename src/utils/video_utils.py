"""Video-related utility helpers (safe filename + record sout builder + external VLC launcher)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from sys import platform
from typing import List, Optional

from core.config import INVALID_WIN, RECORDS_FOLDER
from ui import PySimpleGUI as sg

logger = logging.getLogger("zedtv.video")


def _safe_filename(name: str, max_len: int = 180) -> str:
    """Return a Windows-safe filename (no reserved chars, trimmed)."""
    s = re.sub(r"\s+", " ", name or "").strip()
    s = "".join((c if c not in INVALID_WIN and ord(c) >= 32 else "_") for c in s)
    s = s.rstrip(" .")[:max_len]
    return s or "recording"


def build_record_sout(title: str) -> str:
    """Build VLC :sout= option string for recording while displaying."""
    logger.debug("Building record sout for title='%s'", title)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = f"{ts} - {_safe_filename(title)}.mp4"
    dst_path = Path(RECORDS_FOLDER).resolve() / fname
    dst = str(dst_path)
    if platform.startswith("win"):
        dst = dst.replace("\\", "\\\\")  # Escape for VLC on Windows
    return f":sout=#duplicate{{" f"dst=std{{access=file,mux=mp4,dst='{dst}'}}," f"dst=display" f"}}"


def _detect_vlc() -> Optional[List[str]]:
    """Return command list to launch VLC, or None if not found."""
    if platform.startswith("win"):
        candidates = [
            shutil.which("vlc.exe"),
            r"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            r"C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe",
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return [c]
        return None
    if platform == "darwin":
        return ["open", "-a", "VLC"]
    path = shutil.which("vlc")
    return [path] if path else None


def launch_vlc_external(url: str) -> None:
    """Launch an external VLC process for the given URL (non-blocking)."""
    logger.info("Launching external VLC url=%s", url)
    cmd = _detect_vlc()
    if not cmd:
        sg.popup_error(
            "VLC executable not found. Please install VLC or add it to PATH.",
            keep_on_top=True,
        )
        return
    try:
        if platform == "darwin":
            subprocess.Popen([*cmd, url])
        else:
            subprocess.Popen(
                [*cmd, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception as ex:
        sg.popup_error(f"Failed to launch VLC: {ex}", keep_on_top=True)

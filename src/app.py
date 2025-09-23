import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from sys import platform
from typing import Optional, List
from urllib.parse import urlparse

import httpx

from config import INVALID_WIN, HEADERS, RECORDS_FOLDER
import PySimpleGUI as sg
from models import Data


def _rows(xs):
    return [[x] for x in xs]


def _epoch_to_str(s: str | int | None) -> str:
    if not s:
        return "-"
    try:
        return datetime.fromtimestamp(int(s), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except Exception:
        return str(s)


def _detect_vlc() -> Optional[List[str]]:
    """Return command list to launch VLC, or None if not found."""
    # Windows
    if platform.startswith("win"):
        candidates = [
            shutil.which("vlc.exe"),
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return [c]
        return None
    # macOS
    if platform == "darwin":
        return ["open", "-a", "VLC"]
    # Linux/else
    path = shutil.which("vlc")
    return [path] if path else None


def _launch_vlc_external(url: str) -> None:
    cmd = _detect_vlc()
    if not cmd:
        sg.popup_error(
            "VLC executable not found. "
            "Please install VLC or add it to PATH.",
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


async def generate_list(
    values: dict, categories: list, new_file: Path = "", do_file: bool = False
) -> List[str]:
    result = []
    lines = Data.data.split("\n")
    if os.path.isfile(new_file) and do_file:
        os.remove(new_file)
    for i, each_line in enumerate(lines):
        for item in values["_table_countries_"]:
            if categories[item] in each_line:
                if do_file:
                    with open(new_file, "a+", encoding="UTF-8") as file:
                        file.write(f"{lines[i]}\n{lines[i + 1]}\n")
                else:
                    result.append(f"{lines[i]}\n{lines[i + 1]}")
    return result


async def get_selected() -> List[List[str]]:
    """
    Build rows for the right-hand table from the selected category:
    [Title, Rating, Year, Group]
    Pulls attributes directly from the EXTINF line.
    Falls back to Data.xtream_catalog (if present).
    """
    rows: List[List[str]] = []

    # Optional index from the rich Xtream catalog we stashed
    by_id = {}
    cat = getattr(Data, "xtream_catalog", None)
    if cat:
        for kind in ("live", "vod"):
            for s in cat.get(kind, []):
                by_id[str(s.get("id"))] = s  # map stream_id -> full dict

    for block in Data.selected_list:  # each block = "EXTINF...\nURL"
        extinf = block.split("\n", 1)[0]

        # basic fields
        title = re.search(r'tvg-name="(.*?)"', extinf)
        rating = re.search(r'rating="(.*?)"', extinf)
        releasedate = re.search(r'releasedate="(.*?)"', extinf)
        sid = re.search(r'tvg-id="(\d+)"', extinf)

        title = title.group(1) if title else ""
        rating_val = (rating.group(1) if rating else "") or ""
        released = (releasedate.group(1) if releasedate else "") or ""

        # derive a 4-digit year if possible
        year = ""
        if released:
            m = re.search(r"\b(\d{4})\b", released)
            year = m.group(1) if m else ""

        # fallback to catalog if EXTINF didn’t have rating/year
        if (not rating_val or not year) and sid and sid.group(1) in by_id:
            raw = by_id[sid.group(1)]
            if not rating_val:
                rating_val = (raw.get("rating") or "").strip()
            if not year:
                rel = (raw.get("releasedate") or "").strip()
                if rel:
                    m = re.search(r"\b(\d{4})\b", rel)
                    year = m.group(1) if m else year

        rows.append([title, rating_val, year])

    return rows


def get_categories(filter_search: str = None) -> List[str]:
    if os.path.isfile(Data.filename):
        categories = []
        with open(Data.filename, "r", encoding="utf8") as file:
            Data.data = file.read()
            Data.categories = re.findall(r"group-title=\"(.*?)\"", Data.data)

        for value in Data.categories:
            if value not in categories:
                if filter_search is not None:
                    if filter_search.lower() in value.lower():
                        categories.append(value)
                else:
                    categories.append(value)
        return categories
    return []


def _fmt_yesno(x) -> str:
    if x in (True, "1", 1, "true", "True"):
        return "Yes"
    if x in (False, "0", 0, "false", "False"):
        return "No"
    return "-"


def _fmt_formats(ui: dict, limit: int = 4) -> str:
    fmt = ui.get("allowed_output_formats") or []
    if not fmt:
        return "-"
    return ",".join(fmt[:limit]) + (
        f" +{len(fmt)-limit}" if len(fmt) > limit else ""
    )


def _safe_filename(name: str, max_len: int = 180) -> str:
    """Return a Windows-safe filename (no reserved chars, trimmed)."""
    s = re.sub(r"\s+", " ", name or "").strip()
    s = "".join(
        (c if c not in INVALID_WIN and ord(c) >= 32 else "_") for c in s
    )
    s = s.rstrip(" .")[:max_len]
    return s or "recording"


def _build_record_sout(title: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = f"{ts} - {_safe_filename(title)}.mp4"
    dst = (Path(RECORDS_FOLDER) / fname).as_posix()  # VLC-friendly path
    return (
        f"sout=#duplicate{{dst=std{{access=file,mux=mp4,dst='{dst}'}},"
        f"dst=display}}"
    )


def _normalize_base(
    host_or_url: str, port: int | None = None, prefer_https: bool = False
) -> str:
    """Return base like http(s)://host:port suitable for Xtream paths."""
    url = host_or_url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = ("https://" if prefer_https else "http://") + url
    u = urlparse(url)
    scheme = "https" if (prefer_https or u.scheme == "https") else "http"
    host = u.hostname or host_or_url
    p = port or (u.port or (443 if scheme == "https" else 80))

    return f"{scheme}://{host}:{p}"


def _xtream_api(base: str, username: str, password: str, **params) -> dict:
    """Call player_api.php and return JSON."""
    q = {"username": username, "password": password}

    q.update(params)
    r = httpx.get(
        f"{base}/player_api.php", params=q, headers=HEADERS, verify=False
    )
    r.raise_for_status()
    return r.json()


def _build_m3u_from_xtream(
    base: str, username: str, password: str
) -> tuple[str, dict]:
    """
    Fetch live + VOD from Xtream.
    Returns:
      (m3u_text, catalog_dict)
    """

    cats_live = (
        _xtream_api(base, username, password, action="get_live_categories")
        or []
    )
    streams_live = (
        _xtream_api(base, username, password, action="get_live_streams") or []
    )
    cats_vod = (
        _xtream_api(base, username, password, action="get_vod_categories")
        or []
    )
    streams_vod = (
        _xtream_api(base, username, password, action="get_vod_streams") or []
    )

    cat_live = {
        str(c["category_id"]): c.get("category_name", "Live")
        for c in cats_live
    }
    cat_vod = {
        str(c["category_id"]): c.get("category_name", "VOD") for c in cats_vod
    }

    lines = ["#EXTM3U"]
    catalog = {"live": [], "vod": []}

    # --- LIVE ---
    for s in streams_live:
        stream_id = s.get("stream_id")
        if not stream_id:
            continue

        name = s.get("name", "Live")
        logo = s.get("stream_icon", "")
        ctitle = cat_live.get(str(s.get("category_id")), "Live")
        url = f"{base}/live/{username}/{password}/{stream_id}.m3u8"

        # old m3u line (compatibility)
        lines.append(
            f'#EXTINF:-1 tvg-id="{stream_id}" tvg-name="{name}" '
            f'tvg-logo="{logo}" group-title="[LIVE] {ctitle}",{name}'
        )
        lines.append(url)

        # structured metadata
        catalog["live"].append(
            {
                "id": stream_id,
                "name": name,
                "logo": logo,
                "category": ctitle,
                "url": url,
                "raw": s,  # keep original Xtream dict for extra info
            }
        )

    # --- VOD ---
    for s in streams_vod or []:
        stream_id = s.get("stream_id")
        if not stream_id:
            continue

        name = s.get("name", "Movie")
        logo = s.get("stream_icon", "")
        ext = (s.get("container_extension") or "mp4").lstrip(".")
        ctitle = cat_vod.get(str(s.get("category_id")), "VOD")
        url = f"{base}/movie/{username}/{password}/{stream_id}.{ext}"

        # pull rich metadata
        rating = s.get("rating", "")
        releasedate = s.get("releasedate", "")
        plot = (s.get("plot") or "").replace('"', "'")
        director = (s.get("director") or "").replace('"', "'")

        # EXTINF with extras
        lines.append(
            f"#EXTINF:-1 "
            f'tvg-id="{stream_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="[VOD] {ctitle}" '
            f'rating="{rating}" '
            f'releasedate="{releasedate}" '
            f'director="{director}" '
            f'plot="{plot}",{name}'
        )
        lines.append(url)

        # structured metadata in catalog
        catalog["vod"].append(
            {
                "id": stream_id,
                "name": name,
                "logo": logo,
                "category": ctitle,
                "url": url,
                "rating": rating,
                "releasedate": releasedate,
                "plot": plot,
                "director": director,
                "raw": s,
            }
        )

    return "\n".join(lines), catalog

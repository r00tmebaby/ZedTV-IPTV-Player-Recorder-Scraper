import os
import re
from datetime import datetime, timezone
from pathlib import Path
from sys import platform
from typing import List
from urllib.parse import urlparse

import httpx
import ipaddress

from .config import HEADERS, RECORDS_FOLDER
from ui import PySimpleGUI as sg
from .models import Data
from parsing.m3u_parser import parse_m3u  # new import
from services.xtream import _build_m3u_from_xtream, _normalize_base, _xtream_api  # re-exported for settings/account
from utils.video_utils import build_record_sout as _build_record_sout, launch_vlc_external as _launch_vlc_external, _safe_filename
import logging

logger = logging.getLogger("zedtv.app")


def _rows(xs):
    return [[x] for x in xs]


def _epoch_to_str(s: str | int | None) -> str:
    if not s:
        return "-"
    try:
        # Convert to float first to handle decimals, then to int
        epoch = int(float(s))
        # Reject negative timestamps
        if epoch < 0:
            return str(s)
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except Exception:
        return str(s)


def get_selected() -> List[List[str]]:
    logger.debug("get_selected building table rows from %d selected blocks", len(Data.selected_list))
    """
    Build rows for the right-hand table from the selected category:
    [Title, Rating, Year]
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
        if not title:
            # fallback: use portion after last comma
            try:
                title = re.search(r",([^,]+)$", extinf)
            except Exception:
                title = None
        rating = re.search(r'rating="(.*?)"', extinf)
        releasedate = re.search(r'releasedate="(.*?)"', extinf)
        sid = re.search(r'tvg-id="(\d+)"', extinf)

        title_val = title.group(1) if title else ""
        rating_val = (rating.group(1) if rating else "") or ""
        released = (releasedate.group(1) if releasedate else "") or ""

        # derive a 4-digit year if possible
        year = ""
        if released:
            m = re.search(r"\b(\d{4})\b", released)
            year = m.group(1) if m else ""

        # fallback to catalog if EXTINF didn't have rating/year
        if (not rating_val or not year) and sid and sid.group(1) in by_id:
            raw = by_id[sid.group(1)]
            if not rating_val:
                rating_val = (raw.get("rating") or "").strip()
            if not year:
                rel = (raw.get("releasedate") or "").strip()
                if rel:
                    m = re.search(r"\b(\d{4})\b", rel)
                    year = m.group(1) if m else year

        rows.append([title_val, rating_val, year])

    logger.debug("get_selected produced %d rows", len(rows))
    Data.rows_cache = rows
    Data.search_titles_lower = [ (r[0] or '').lower() for r in rows ]
    return rows


def get_categories(filter_search: str = None) -> List[str]:
    logger.info("get_categories invoked filename=%s filter=%s", Data.filename, filter_search)
    if os.path.isfile(Data.filename):
        try:
            with open(Data.filename, "r", encoding="utf8", errors="ignore") as file:
                Data.data = file.read()
            Data.m3u_parser = parse_m3u(Data.data)
            Data.parsed_channels = Data.m3u_parser.channels
            cats = Data.m3u_parser.groups()
            if filter_search:
                cats = [c for c in cats if filter_search.lower() in c.lower()]
            Data.categories = cats
            Data.categories_master = list(cats) if not filter_search else Data.categories_master or list(cats)
            logger.info("Parsed categories total=%d", len(cats))
            return cats
        except Exception as e:
            logger.exception("Failed to read/parse M3U file '%s': %s", Data.filename, e)
            return []
    else:
        logger.warning("File does not exist: %s", Data.filename)
    return []


async def generate_list(values: dict, categories: List[str], new_file: str = None, do_file: bool = False) -> List[str]:
    """
    Generate a filtered list of channels based on selected categories.

    Args:
        values: Dictionary containing '_table_countries_' key with selected category indices
        categories: List of all category names
        new_file: Optional path to write filtered M3U file
        do_file: If True, write the filtered content to new_file

    Returns:
        List of channel blocks (EXTINF + URL) for the selected categories
    """
    logger.info("generate_list called with %d categories, do_file=%s", len(categories), do_file)

    # Get selected category indices
    selected_indices = values.get("_table_countries_", [])
    if not selected_indices:
        logger.warning("No categories selected in generate_list")
        return []

    # Get selected category names
    selected_cats = [categories[i] for i in selected_indices if 0 <= i < len(categories)]
    logger.info("Selected categories: %s", selected_cats)

    # Filter channels by selected categories
    if not Data.m3u_parser or not Data.m3u_parser.channels:
        logger.warning("No parsed channels available")
        return []

    filtered_blocks = []
    for channel in Data.m3u_parser.channels:
        if channel.group_title in selected_cats:
            # Reconstruct the channel block (EXTINF + URL)
            block = channel.to_block()
            filtered_blocks.append(block)

    logger.info("Filtered %d channels from selected categories", len(filtered_blocks))

    # Optionally write to file
    if do_file and new_file:
        try:
            content = "#EXTM3U\n" + "\n".join(filtered_blocks)
            Path(new_file).write_text(content, encoding="utf-8")
            logger.info("Written filtered M3U to %s (%d channels)", new_file, len(filtered_blocks))
        except Exception as e:
            logger.error("Failed to write M3U file %s: %s", new_file, e)

    return filtered_blocks


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



def _build_record_sout(title: str) -> str:
    logger.debug("Building record sout for title='%s'", title)
    """Build VLC sout option string for recording while displaying.
    Returns the option string (with the ':sout=' prefix for VLC).
    """
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = f"{ts} - {_safe_filename(title)}.mp4"

    # Use absolute path and convert to string (on Windows, use backslashes)
    dst_path = Path(RECORDS_FOLDER).resolve() / fname
    dst = str(dst_path)  # Use native path format

    # Escape backslashes for VLC (Windows needs double backslashes)
    if platform.startswith("win"):
        dst = dst.replace("\\", "\\\\")

    # Build the sout string: duplicate to both file and display
    # Note: The ':sout=' prefix is required for VLC options
    return (
        f":sout=#duplicate{{"
        f"dst=std{{access=file,mux=mp4,dst='{dst}'}},"
        f"dst=display"
        f"}}"
    )


def _normalize_base(
    host_or_url: str, port: int | None = None, prefer_https: bool = False
) -> str:
    logger.debug("_normalize_base host_or_url=%s port=%s prefer_https=%s", host_or_url, port, prefer_https)
    """Return base like http(s)://host:port suitable for Xtream paths.

    Handles hostnames, IPv4, IPv6 (with or without brackets), and full URLs.
    """
    raw = (host_or_url or "").strip()
    if not raw:
        # Fallback safe default
        scheme = "https" if prefer_https else "http"
        return f"{scheme}://localhost:{443 if scheme=='https' else 80}"

    has_scheme = re.match(r"^https?://", raw, re.I) is not None

    # If the input already has a scheme, rely on urlparse but carefully format IPv6
    if has_scheme:
        u = urlparse(raw)
        scheme = "https" if (prefer_https or u.scheme == "https") else "http"
        host = u.hostname or "localhost"
        # Bracket IPv6 literal for output if needed
        if host and ":" in host and not host.startswith("["):
            try:
                if ipaddress.ip_address(host).version == 6:
                    host = f"[{ipaddress.ip_address(host).compressed}]"
            except Exception:
                pass
        p = port or (u.port or (443 if scheme == "https" else 80))
        return f"{scheme}://{host}:{p}"

    # No scheme provided: treat as host (possibly with port)
    host_part = raw
    detected_port: int | None = None
    host_out = host_part

    # Case 1: Bracketed IPv6, optionally with :port
    m = re.match(r"^\[(?P<ipv6>[^\]]+)\](?::(?P<p>\d+))?$", host_part)
    if m:
        addr = m.group("ipv6")
        try:
            ip = ipaddress.ip_address(addr)
            if ip.version == 6:
                host_out = f"[{ip.compressed}]"
                if m.group("p"):
                    try:
                        detected_port = int(m.group("p"))
                    except Exception:
                        detected_port = None
        except Exception:
            # Fall through leaving host_out as-is
            pass
    else:
        # Case 2: Unbracketed IPv6 literal (multiple colons) without port
        if host_part.count(":") >= 2:
            try:
                ip = ipaddress.ip_address(host_part)
                if ip.version == 6:
                    host_out = f"[{ip.compressed}]"
            except Exception:
                # Not a pure IPv6 literal; could be hostname with colon issues
                pass
        else:
            # Case 3: hostname/IPv4, optional :port
            if ":" in host_part:
                name, _, pstr = host_part.partition(":")
                host_out = name
                if pstr.isdigit():
                    detected_port = int(pstr)
            else:
                host_out = host_part

    scheme = "https" if prefer_https else "http"
    p = port or detected_port or (443 if scheme == "https" else 80)
    return f"{scheme}://{host_out}:{p}"


def _xtream_api(base: str, username: str, password: str, **params) -> dict:
    logger.info("Xtream API call base=%s action=%s", base, params.get('action'))
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
    logger.info("Building M3U from Xtream base=%s user=%s", base, username)
    base = _normalize_base(base)
    # Submit API calls in

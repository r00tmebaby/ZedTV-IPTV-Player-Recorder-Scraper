import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from parsing.m3u_parser import parse_m3u
from services.xtream import _build_m3u_from_xtream, _normalize_base, _xtream_api  # re-exported for settings/account
from utils.video_utils import _safe_filename
from utils.video_utils import build_record_sout as _build_record_sout


from .models import Data

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
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
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
    Data.search_titles_lower = [(r[0] or "").lower() for r in rows]
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
    return ",".join(fmt[:limit]) + (f" +{len(fmt)-limit}" if len(fmt) > limit else "")


# Functions from xtream and video_utils are imported at top and re-exported
# No need to redefine them here

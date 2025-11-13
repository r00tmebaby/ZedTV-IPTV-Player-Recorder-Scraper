"""EPG ingestion hooks (XMLTV and JSON) and indexing by channel id.
This module provides lightweight functions to parse common EPG formats
into a normalized in-memory index that maps channel identifiers (like epg-id)
to programme lists.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import json
import logging
from xml.etree import ElementTree as ET

log = logging.getLogger("zedtv.epg")

Programme = dict  # shape: {start, stop, title, desc, category, season, episode, rating}
EPGIndex = Dict[str, List[Programme]]


def load_xmltv(xml_content: str) -> EPGIndex:
    """Parse XMLTV content to an epg index.
    We collect <programme> nodes grouped by their channel attribute.
    """
    index: EPGIndex = {}
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        log.warning("XMLTV parse failed: %s", e)
        return index
    for p in root.findall("programme"):
        try:
            ch = p.get("channel") or ""
            if not ch:
                continue
            start = p.get("start")
            stop = p.get("stop")
            title_el = p.find("title")
            desc_el = p.find("desc")
            cat_el = p.find("category")
            ep_el = p.find("episode-num")
            # Try rating/value first, then rating
            rating_el = p.find("rating/value")
            if rating_el is None:
                rating_el = p.find("rating")

            # Extract text and strip whitespace, handle None properly
            def get_text(el):
                if el is not None and el.text:
                    return el.text.strip()
                return ""

            prog = {
                "start": start or "",
                "stop": stop or "",
                "title": get_text(title_el),
                "desc": get_text(desc_el),
                "category": get_text(cat_el),
                "episode": get_text(ep_el),
                "rating": get_text(rating_el),
            }
            index.setdefault(ch, []).append(prog)
        except Exception as e:
            log.debug("Skip malformed programme: %s", e)
    # Optional: sort programmes by start
    for ch, arr in index.items():
        try:
            arr.sort(key=lambda x: x.get("start") or "")
        except Exception:
            pass
    log.info("XMLTV loaded channels=%d total_programmes=%d", len(index), sum(len(v) for v in index.values()))
    return index


essential_keys = {"channel", "start", "stop", "title"}

def load_json_epg(json_content: str, mapping: Optional[dict] = None) -> EPGIndex:
    """Parse a simple JSON EPG format.
    Expected shape (flexible): { "programmes": [ {"channel": "id", "start": "...", "stop": "...", "title": "...", ... }, ... ] }
    mapping: optional dict to rename keys: {"chan":"channel", "beg":"start", ...}
    """
    index: EPGIndex = {}
    try:
        obj = json.loads(json_content)
    except Exception as e:
        log.warning("JSON EPG parse failed: %s", e)
        return index

    # Handle list at root (invalid but graceful)
    if isinstance(obj, list):
        return index

    progs = obj.get("programmes") or obj.get("entries") or []
    m = mapping or {}

    # Helper to convert None to empty string
    def to_str(val):
        return str(val) if val is not None else ""

    def norm(d: dict) -> Programme:
        return {
            "start": to_str(d.get(m.get("start","start"), "")),
            "stop": to_str(d.get(m.get("stop","stop"), "")),
            "title": to_str(d.get(m.get("title","title"), "")),
            "desc": to_str(d.get(m.get("desc","desc"), "")),
            "category": to_str(d.get(m.get("category","category"), "")),
            "episode": to_str(d.get(m.get("episode","episode"), "")),
            "rating": to_str(d.get(m.get("rating","rating"), "")),
        }

    for item in progs:
        try:
            # Skip non-dict items
            if not isinstance(item, dict):
                continue
            ch = item.get(m.get("channel","channel"), "")
            if not ch:
                continue
            # Convert integer channel IDs to string
            ch = str(ch)
            index.setdefault(ch, []).append(norm(item))
        except Exception as e:
            log.debug("Skip malformed JSON programme: %s", e)

    for ch, arr in index.items():
        try:
            arr.sort(key=lambda x: x.get("start") or "")
        except Exception:
            pass
    log.info("JSON EPG loaded channels=%d total_programmes=%d", len(index), sum(len(v) for v in index.values()))
    return index

# NOTE: This module remains at top-level for compatibility; future code may move to services.epg.

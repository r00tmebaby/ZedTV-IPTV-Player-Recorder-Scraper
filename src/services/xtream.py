"""Xtream Codes API helpers and M3U builder.

This module encapsulates network calls and transformation logic needed to
fetch categories and streams, then build an M3U playlist and a rich catalog.

NOTE: This module will be relocated to services.xtream; keep name for backward compatibility.
"""

from __future__ import annotations

import ipaddress
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import httpx

from core.config import HEADERS

logger = logging.getLogger("zedtv.xtream")


def _normalize_base(
    host_or_url: str, port: int | None = None, prefer_https: bool = False
) -> str:
    """Return base like http(s)://host:port suitable for Xtream paths.

    Handles hostnames, IPv4, IPv6 (with or without brackets), and full URLs.
    """
    logger.debug(
        "_normalize_base host_or_url=%s port=%s prefer_https=%s",
        host_or_url,
        port,
        prefer_https,
    )
    raw = (host_or_url or "").strip()
    if not raw:
        # Fallback safe default
        scheme = "https" if prefer_https else "http"
        return f"{scheme}://localhost:{443 if scheme == 'https' else 80}"

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
    """Call player_api.php and return JSON.

    Raises for HTTP errors; returns parsed JSON body.
    """
    logger.info(
        "Xtream API call base=%s action=%s", base, params.get("action")
    )
    q = {"username": username, "password": password}
    q.update(params)
    r = httpx.get(
        f"{base}/player_api.php", params=q, headers=HEADERS, verify=False
    )
    r.raise_for_status()
    return r.json()


def _build_m3u_from_xtream(
    base: str, username: str, password: str
) -> Tuple[str, Dict[str, List[dict]]]:
    """Fetch Live and VOD streams and construct an M3U text and rich catalog.

    Returns (m3u_text, catalog) where catalog has keys: live, vod.
    Performs the 4 API calls in parallel.
    """
    logger.info("Building M3U from Xtream base=%s user=%s", base, username)
    base = _normalize_base(base)

    tasks = {
        "cats_live": dict(action="get_live_categories"),
        "streams_live": dict(action="get_live_streams"),
        "cats_vod": dict(action="get_vod_categories"),
        "streams_vod": dict(action="get_vod_streams"),
    }
    results: Dict[str, list] = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        future_map = {
            ex.submit(_xtream_api, base, username, password, **params): key
            for key, params in tasks.items()
        }
        for fut in as_completed(future_map):
            key = future_map[fut]
            try:
                results[key] = fut.result() or []
            except Exception as e:
                logger.warning("Xtream fetch failed for %s: %s", key, e)
                results[key] = []

    cats_live = results.get("cats_live", [])
    streams_live = results.get("streams_live", [])
    cats_vod = results.get("cats_vod", [])
    streams_vod = results.get("streams_vod", [])

    cat_live = {
        str(c.get("category_id")): c.get("category_name", "Live")
        for c in cats_live
    }
    cat_vod = {
        str(c.get("category_id")): c.get("category_name", "VOD")
        for c in cats_vod
    }

    lines = ["#EXTM3U"]
    catalog: Dict[str, List[dict]] = {"live": [], "vod": []}

    # --- LIVE ---
    for s in streams_live:
        stream_id = s.get("stream_id") or s.get("id") or s.get("streamId")
        if not stream_id:
            logger.warning("Live stream missing id - skipped raw=%s", s)
            continue
        name = s.get("name") or s.get("title") or f"Live {stream_id}"
        logo = s.get("stream_icon") or s.get("logo") or s.get("icon") or ""
        ctitle = cat_live.get(
            str(
                s.get("category_id")
                or s.get("categoryId")
                or s.get("category")
            ),
            "Live",
        )
        epg_id = s.get("epg_channel_id") or s.get("epg") or ""
        url = f"{base}/live/{username}/{password}/{stream_id}.m3u8"
        lines.append(
            f'#EXTINF:-1 tvg-id="{stream_id}" tvg-name="{name}" '
            f'tvg-logo="{logo}" group-title="[LIVE] {ctitle}" epg-id="{epg_id}",{name}'
        )
        lines.append(url)
        catalog["live"].append(
            {
                "id": stream_id,
                "name": name,
                "logo": logo,
                "category": ctitle,
                "url": url,
                "epg_id": epg_id,
                "raw": s,
            }
        )

    # --- VOD ---
    for s in streams_vod or []:
        stream_id = s.get("stream_id") or s.get("id") or s.get("streamId")
        if not stream_id:
            logger.warning("VOD stream missing id - skipped raw=%s", s)
            continue
        name = s.get("name") or s.get("title") or f"Movie {stream_id}"
        logo = s.get("stream_icon") or s.get("logo") or s.get("icon") or ""
        ext = (
            s.get("container_extension")
            or s.get("containerExtension")
            or "mp4"
        ).lstrip(".")
        ctitle = cat_vod.get(
            str(
                s.get("category_id")
                or s.get("categoryId")
                or s.get("category")
            ),
            "VOD",
        )
        url = f"{base}/movie/{username}/{password}/{stream_id}.{ext}"
        rating = s.get("rating") or s.get("imdb_rating") or ""
        releasedate = s.get("releasedate") or s.get("releaseDate") or ""
        plot = (s.get("plot") or s.get("description") or "").replace('"', "'")
        director = (s.get("director") or "").replace('"', "'")
        epg_id = s.get("epg_channel_id") or s.get("epg") or ""
        lines.append(
            f"#EXTINF:-1 "
            f'tvg-id="{stream_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="[VOD] {ctitle}" '
            f'rating="{rating}" '
            f'releasedate="{releasedate}" '
            f'director="{director}" '
            f'plot="{plot}" '
            f'epg-id="{epg_id}",{name}'
        )
        lines.append(url)
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
                "epg_id": epg_id,
                "raw": s,
            }
        )

    logger.info(
        "Xtream build complete live=%d vod=%d",
        len(catalog["live"]),
        len(catalog["vod"]),
    )
    return "\n".join(lines), catalog

"""M3U parser (structured Channel model and robust parsing)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger("zedtv.m3u")

_EXTINF_RE = re.compile(
    r"^#EXTINF:(?P<duration>-?\d+)\s*(?P<attr_part>[^,]*?)\s*,(?P<title>.*)$"
)
_ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\s]+))')
_EXTGRP_RE = re.compile(r"^#EXTGRP:(?P<grp>.+)$")
_PROP_PREFIXES = ("#EXTVLCOPT", "#KODIPROP", "#EXTHTTP", "#EXTIMG")


@dataclass
class Channel:
    index: int
    duration: int
    title: str
    url: str
    attrs: Dict[str, str] = field(default_factory=dict)
    group: str = ""
    properties: List[str] = field(default_factory=list)
    extgrp: Optional[str] = None
    raw_extinf: str = ""
    vlc_opts: Dict[str, str] = field(default_factory=dict)
    kodi_props: Dict[str, str] = field(default_factory=dict)
    other_props: List[str] = field(default_factory=list)
    epg: List[dict] | None = None

    def to_block(self) -> str:
        lines: List[str] = []
        lines.extend(self.properties)
        if self.raw_extinf:
            lines.append(self.raw_extinf)
        else:
            attr_part = " ".join(
                f'{k}="{v}"' for k, v in sorted(self.attrs.items())
            )
            lines.append(f"#EXTINF:{self.duration} {attr_part},{self.title}")
        lines.append(self.url)
        return "\n".join(lines)

    @property
    def tvg_id(self) -> str:
        return self.attrs.get("tvg-id", "")

    @property
    def tvg_name(self) -> str:
        return self.attrs.get("tvg-name", self.title)

    @property
    def tvg_logo(self) -> str:
        return self.attrs.get("tvg-logo", "")

    @property
    def group_title(self) -> str:
        return self.attrs.get(
            "group-title", self.group or self.extgrp or "Other"
        )

    @property
    def all_properties(self) -> Dict[str, Dict[str, str] | List[str]]:
        return {
            "vlc": self.vlc_opts,
            "kodi": self.kodi_props,
            "other_raw": self.other_props,
        }


class M3UParser:
    def __init__(self, raw: str):
        self.raw = raw or ""
        self.channels: List[Channel] = []
        logger.debug("M3UParser init: raw length=%d", len(self.raw))
        self._parse()

    def _parse(self) -> None:
        lines = self.raw.splitlines()
        pending_props: List[str] = []
        last_extgrp: Optional[str] = None
        index = 0
        i = 0
        total = len(lines)
        while i < total:
            line = lines[i].strip("\ufeff\ufdfa ")
            if not line:
                i += 1
                continue
            if line.startswith("#EXTM3U"):
                pass
            m_grp = _EXTGRP_RE.match(line)
            if m_grp:
                last_extgrp = m_grp.group("grp").strip()
                i += 1
                continue
            if line.startswith(_PROP_PREFIXES):
                pending_props.append(lines[i])
                try:
                    if line.startswith("#EXTVLCOPT:"):
                        kv = line.split(":", 1)[1]
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            pending_props.append(
                                f"__PARSED_VLC__:{k.strip()}={v.strip()}"
                            )
                    elif line.startswith("#KODIPROP:"):
                        kv = line.split(":", 1)[1]
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            pending_props.append(
                                f"__PARSED_KODI__:{k.strip()}={v.strip()}"
                            )
                except Exception:
                    logger.debug("Failed parsing property line '%s'", line)
                i += 1
                continue
            m = _EXTINF_RE.match(line)
            if m:
                duration_str = m.group("duration")
                try:
                    duration = int(duration_str)
                except ValueError:
                    duration = -1
                attr_part = m.group("attr_part") or ""
                title = m.group("title").strip()
                attrs: Dict[str, str] = {}
                for am in _ATTR_RE.finditer(attr_part):
                    key = am.group(1).strip()
                    val = (
                        am.group(2) or am.group(3) or am.group(4) or ""
                    ).strip()
                    if key not in attrs:
                        attrs[key] = val
                group = attrs.get("group-title", "") or (last_extgrp or "")
                url = ""
                j = i + 1
                while j < total:
                    nxt = lines[j].strip()
                    if not nxt:
                        j += 1
                        continue
                    if nxt.startswith("#") and not nxt.lower().startswith(
                        "#http"
                    ):
                        break
                    url = nxt
                    break
                if not url:
                    i += 1
                    pending_props.clear()
                    last_extgrp = None
                    continue
                chan = Channel(
                    index=index,
                    duration=duration,
                    title=title,
                    url=url,
                    attrs=attrs,
                    group=group,
                    properties=[
                        p
                        for p in pending_props
                        if not p.startswith("__PARSED_")
                    ],
                    extgrp=last_extgrp,
                    raw_extinf=lines[i],
                )
                for pp in pending_props:
                    if pp.startswith("__PARSED_VLC__:"):
                        kv = pp.split(":", 1)[1]
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            chan.vlc_opts[k] = v
                    elif pp.startswith("__PARSED_KODI__:"):
                        kv = pp.split(":", 1)[1]
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            chan.kodi_props[k] = v
                    elif pp.startswith("#") and not pp.startswith(
                        _PROP_PREFIXES
                    ):
                        chan.other_props.append(pp)
                epg_id = (
                    attrs.get("epg-id")
                    or attrs.get("epg_channel_id")
                    or attrs.get("tvg-id")
                )
                if epg_id:
                    chan.attrs.setdefault("epg-id", epg_id)
                self.channels.append(chan)
                index += 1
                pending_props.clear()
                last_extgrp = None
                i = j + 1
                continue
            i += 1

    def groups(self) -> List[str]:
        seen = []
        added = set()
        for c in self.channels:
            g = c.group_title.strip() or "Other"
            if g not in added:
                added.add(g)
                seen.append(g)
        return seen

    def filter_by_groups(self, groups: Iterable[str]) -> List[Channel]:
        target = set(groups)
        return [c for c in self.channels if c.group_title in target]

    def to_blocks(self, channels: Iterable[Channel]) -> List[str]:
        return [c.to_block() for c in channels]

    def map_epg(
        self, epg_index: Dict[str, List[dict]], key_order: List[str] = None
    ) -> int:
        if key_order is None:
            key_order = ["epg-id", "epg_channel_id", "tvg-id"]
        enriched = 0
        for ch in self.channels:
            epg_key = None
            for k in key_order:
                val = ch.attrs.get(k)
                if val and val in epg_index:
                    epg_key = val
                    break
            if epg_key:
                ch.epg = epg_index.get(epg_key, [])
                enriched += 1
        return enriched


def parse_m3u(raw: str) -> M3UParser:
    logger.info("parse_m3u invoked raw_length=%d", len(raw or ""))
    return M3UParser(raw)

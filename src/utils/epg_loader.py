"""
EPG (Electronic Program Guide) loading module.

This module handles asynchronous loading and mapping of EPG data from XML and JSON files.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import sys

from services.epg import load_json_epg, load_xmltv

# Module logger
log = logging.getLogger(__name__)


async def load_epg_async(data_module: Any) -> None:
    """
    Load EPG files in background after UI is shown.

    This function loads both XML and JSON EPG files from the data/epg directory
    and maps them to channels if an m3u_parser is available.

    Args:
        data_module: Data module containing m3u_parser and other state
    """
    log.info("Starting background EPG loading")
    try:
        base_dir = (
            (
                Path(sys.executable).parent
                if getattr(sys, "frozen", False)
                else Path(__file__).parent.parent
            )
            / "data"
            / "epg"
        )
        log.debug("EPG base directory: %s", base_dir)

        epg_index: Dict[str, List[Any]] = {}

        if not base_dir.exists():
            log.warning("EPG directory does not exist: %s", base_dir)
            return

        # Load XML EPG files first
        xml_count = 0
        for p in base_dir.glob("*.xml*"):
            log.debug("Processing XML EPG file: %s", p)
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                idx = load_xmltv(content)

                for k, arr in idx.items():
                    epg_index.setdefault(k, []).extend(arr)

                xml_count += 1
                log.info(
                    "Loaded XML EPG file: %s (%d entries)", p.name, len(idx)
                )

            except Exception as e:
                log.error(
                    "Failed to load EPG file %s: %s", p, e, exc_info=True
                )

        log.info("Loaded %d XML EPG files", xml_count)

        # Then load JSON EPG files
        json_count = 0
        for p in base_dir.glob("*.json"):
            log.debug("Processing JSON EPG file: %s", p)
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                idx = load_json_epg(content)

                for k, arr in idx.items():
                    epg_index.setdefault(k, []).extend(arr)

                json_count += 1
                log.info(
                    "Loaded JSON EPG file: %s (%d entries)", p.name, len(idx)
                )

            except Exception as e:
                log.error(
                    "Failed to load EPG file %s: %s", p, e, exc_info=True
                )

        log.info("Loaded %d JSON EPG files", json_count)

        # Map EPG to channels if m3u_parser is available
        if epg_index and getattr(data_module, "m3u_parser", None):
            try:
                log.debug("Mapping EPG to channels")
                data_module.m3u_parser.map_epg(epg_index)

                # Count channels with EPG data
                channels_with_epg = len(
                    [
                        c
                        for c in data_module.m3u_parser.channels
                        if getattr(c, "epg", None)
                    ]
                )

                log.info(
                    "EPG mapped to channels: %d channels have EPG data",
                    channels_with_epg,
                )

            except Exception as e:
                log.error("EPG mapping failed: %s", e, exc_info=True)
        else:
            if not epg_index:
                log.warning("No EPG data loaded")
            if not getattr(data_module, "m3u_parser", None):
                log.warning("No m3u_parser available for EPG mapping")

        log.info("EPG loading complete: %d total entries", len(epg_index))

    except Exception as e:
        log.error("EPG loading failed: %s", e, exc_info=True)

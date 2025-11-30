"""
Search and filter functionality for categories and channels.

This module handles live filtering of categories and channels based on user input.
"""

import logging
import time
from typing import Any, Dict, List, Optional

# Module logger
log = logging.getLogger(__name__)

# Move app helpers to module level to avoid repeated runtime imports
try:
    from core.app import _rows, get_selected
except Exception:
    # fallback: avoid hard failure during test discovery if core.app is not importable yet
    _rows = None  # type: ignore
    get_selected = None  # type: ignore


class SearchHandler:
    """
    Manages search and filtering for categories and channels.

    Attributes:
        last_ch_search: Debounce tracking for channel search
    """

    def __init__(self) -> None:
        """Initialize the search handler.

        Initializes debounce state used by channel filtering.
        """
        log.debug("Initializing SearchHandler")
        self.last_ch_search: Dict[str, Any] = {"text": "", "ts": 0}

    @staticmethod
    def filter_categories(
        search_text: str, data_module: Any, category_window: Any
    ) -> None:
        """
        Filter categories based on search text.

        This function is a pure operation that does not require instance state, so it is
        implemented as a static method to make intent explicit.

        Args:
            search_text: Search query text
            data_module: Data module containing categories (must expose .categories and .categories_master)
            category_window: Category window to update (optional)
        """
        log.debug("filter_categories invoked with text=%r", search_text)
        try:
            t = (search_text or "").strip().lower()
            base = getattr(data_module, "categories_master", None) or getattr(
                data_module, "categories", []
            )

            if t:
                data_module.categories = [c for c in base if t in c.lower()]
                log.info(
                    "Category filter applied: %d matches out of %d",
                    len(data_module.categories),
                    len(base),
                )
            else:
                data_module.categories = list(base)
                log.debug("Category filter cleared")

            if category_window is not None and _rows is not None:
                try:
                    category_window["_table_countries_"].update(
                        _rows(data_module.categories)
                    )
                    log.debug("Category window updated")
                except Exception:
                    log.exception("Failed to update category window")

        except Exception:
            log.exception("Failed to filter categories")

    def filter_channels(
        self,
        search_text: str,
        data_module: Any,
        channel_window: Any,
        player_instance: Any,
        debounce_ms: float = 120.0,
    ) -> None:
        """
        Filter channels based on search text with debouncing.

        Uses instance debounce state to avoid excessive filtering while typing.

        Args:
            search_text: Search query text
            data_module: Data module containing channels and caches
            channel_window: Channel window to update (optional)
            player_instance: Player instance for accessing master channel list
            debounce_ms: Debounce delay in milliseconds (default: 120)
        """
        log.debug(
            "filter_channels invoked with text=%r debounce_ms=%s",
            search_text,
            debounce_ms,
        )

        now = time.time()
        txt = (search_text or "").strip().lower()

        # Debounce: only process if text changed and enough time has passed
        if txt == self.last_ch_search["text"] or (
            now - self.last_ch_search["ts"]
        ) <= (debounce_ms / 1000.0):
            log.debug(
                "Channel filter debounced (text unchanged or within debounce window)"
            )
            return

        self.last_ch_search["text"] = txt
        self.last_ch_search["ts"] = now

        try:
            # Get base channel list
            base_list: List[Any] = (
                getattr(player_instance, "_channels_master", None)
                or getattr(data_module, "selected_list", [])
                or []
            )

            # Get or generate display rows
            if not getattr(data_module, "rows_cache", None) or len(
                getattr(data_module, "rows_cache", [])
            ) != len(base_list):
                # Recompute selected_list and rows
                data_module.selected_list = base_list
                if get_selected is None:
                    log.debug(
                        "get_selected not available; skipping row generation"
                    )
                    rows = []
                else:
                    rows = get_selected()
            else:
                rows = data_module.rows_cache

            # Apply filter
            if txt:
                # Ensure search_titles_lower exists
                search_titles_lower = getattr(
                    data_module, "search_titles_lower", None
                )
                if search_titles_lower is None:
                    # Build it from rows if possible
                    search_titles_lower = [(r[0] or "").lower() for r in rows]
                    data_module.search_titles_lower = search_titles_lower

                idxs = [
                    i
                    for i, tval in enumerate(data_module.search_titles_lower)
                    if txt in tval
                ]
                data_module.selected_list = [base_list[i] for i in idxs]

                if channel_window is not None:
                    try:
                        channel_window["_iptv_content_"].update(
                            [rows[i] for i in idxs]
                        )
                    except Exception:
                        log.exception(
                            "Failed to update channel window with filtered rows"
                        )

                log.info(
                    "Channel filter applied: %d matches out of %d",
                    len(idxs),
                    len(base_list),
                )
            else:
                data_module.selected_list = base_list

                if channel_window is not None:
                    try:
                        channel_window["_iptv_content_"].update(rows)
                    except Exception:
                        log.exception(
                            "Failed to update channel window when clearing filter"
                        )

                log.debug("Channel filter cleared")

        except Exception:
            log.exception("Failed to filter channels")

    def handle_search_event(
        self,
        field: str,
        text: str,
        data_module: Any,
        category_window: Any,
        channel_window: Any,
        player_instance: Any,
    ) -> None:
        """
        Handle search event from either category or channel search field.

        Args:
            field: Search field identifier ('_cat_search_' or '_ch_search_')
            text: Search text
            data_module: Data module
            category_window: Category window
            channel_window: Channel window
            player_instance: Player instance
        """
        log.debug("handle_search_event: field=%s text=%r", field, text)

        raw_text = text or ""

        if field == "_cat_search_":
            # category filtering is pure and safe to call directly
            self.filter_categories(raw_text, data_module, category_window)
        elif field == "_ch_search_":
            self.filter_channels(
                raw_text, data_module, channel_window, player_instance
            )
        else:
            log.warning("Unknown search field: %s", field)

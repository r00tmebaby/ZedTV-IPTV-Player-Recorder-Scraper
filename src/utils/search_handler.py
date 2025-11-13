"""
Search and filter functionality for categories and channels.

This module handles live filtering of categories and channels based on user input.
"""
import logging
import time
from typing import Dict, List, Any, Optional

# Module logger
log = logging.getLogger(__name__)


class SearchHandler:
    """
    Manages search and filtering for categories and channels.
    
    Attributes:
        last_ch_search: Debounce tracking for channel search
    """
    
    def __init__(self):
        """Initialize the search handler."""
        log.debug("Initializing SearchHandler")
        self.last_ch_search: Dict[str, Any] = {"text": "", "ts": 0}

    def filter_categories(self, search_text: str, data_module: Any,
                         category_window: Any) -> None:
        """
        Filter categories based on search text.
        
        Args:
            search_text: Search query text
            data_module: Data module containing categories
            category_window: Category window to update
        """
        log.debug("Filtering categories with text: '%s'", search_text)
        try:
            t = search_text.strip().lower()
            base = data_module.categories_master or data_module.categories
            
            if t:
                data_module.categories = [c for c in base if t in c.lower()]
                log.info("Category filter applied: %d matches out of %d", 
                        len(data_module.categories), len(base))
            else:
                data_module.categories = list(base)
                log.debug("Category filter cleared")
            
            if category_window:
                from core.app import _rows
                category_window["_table_countries_"].update(
                    _rows(data_module.categories)
                )
                log.debug("Category window updated")
                
        except Exception as e:
            log.error("Failed to filter categories: %s", e, exc_info=True)

    def filter_channels(self, search_text: str, data_module: Any,
                       channel_window: Any, player_instance: Any,
                       debounce_ms: float = 120.0) -> None:
        """
        Filter channels based on search text with debouncing.
        
        Args:
            search_text: Search query text
            data_module: Data module containing channels
            channel_window: Channel window to update
            player_instance: Player instance for accessing master channel list
            debounce_ms: Debounce delay in milliseconds (default: 120)
        """
        log.debug("Filtering channels with text: '%s'", search_text)
        
        now = time.time()
        txt = search_text.strip().lower()
        
        # Debounce: only process if text changed and enough time has passed
        if (txt == self.last_ch_search["text"] or 
            (now - self.last_ch_search["ts"]) <= (debounce_ms / 1000.0)):
            log.debug("Channel filter debounced")
            return
        
        self.last_ch_search["text"] = txt
        self.last_ch_search["ts"] = now
        
        try:
            from core.app import get_selected
            
            # Get base channel list
            base_list = (player_instance._channels_master or 
                        getattr(data_module, "selected_list", []) or [])
            
            # Get or generate display rows
            if (not data_module.rows_cache or 
                len(data_module.rows_cache) != len(base_list)):
                data_module.selected_list = base_list
                rows = get_selected()
            else:
                rows = data_module.rows_cache
            
            # Apply filter
            if txt:
                idxs = [i for i, tval in enumerate(data_module.search_titles_lower) 
                       if txt in tval]
                data_module.selected_list = [base_list[i] for i in idxs]
                
                if channel_window:
                    channel_window["_iptv_content_"].update([rows[i] for i in idxs])
                
                log.info("Channel filter applied: %d matches out of %d", 
                        len(idxs), len(base_list))
            else:
                data_module.selected_list = base_list
                
                if channel_window:
                    channel_window["_iptv_content_"].update(rows)
                
                log.debug("Channel filter cleared")
                
        except Exception as e:
            log.error("Failed to filter channels: %s", e, exc_info=True)

    def handle_search_event(self, field: str, text: str, data_module: Any,
                           category_window: Any, channel_window: Any,
                           player_instance: Any) -> None:
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
        log.debug("Handling search event: field=%s, text='%s'", field, text)
        
        raw_text = text or ""
        
        if field == "_cat_search_":
            self.filter_categories(raw_text, data_module, category_window)
        elif field == "_ch_search_":
            self.filter_channels(raw_text, data_module, channel_window, 
                               player_instance)
        else:
            log.warning("Unknown search field: %s", field)

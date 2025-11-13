"""
Channel selection and playback handler.

This module handles channel selection, parsing, and playback initiation.
"""
import logging
import re
import asyncio
from typing import Optional, Tuple, Any

from ui.layout import sg
from core.models import Data
from core.app import _build_record_sout
from core.player import launch_vlc_external

# Module logger
log = logging.getLogger(__name__)


class ChannelHandler:
    """
    Handles channel selection and playback operations.
    
    Attributes:
        last_channel_idx: Last selected channel index
    """
    
    def __init__(self):
        """Initialize the channel handler."""
        log.debug("Initializing ChannelHandler")
        self.last_channel_idx: Optional[int] = None

    def get_selected_channel_index(self, event: str, values: dict,
                                   channel_window: Any) -> Optional[int]:
        """
        Get the selected channel index from various sources.
        
        Args:
            event: Event name
            values: Window values dictionary
            channel_window: Channel window reference
            
        Returns:
            Selected channel index or None
        """
        log.debug("Getting selected channel index for event: %s", event)
        selected_idx = None
        
        # Primary selection from table widget
        if "_iptv_content_" in values and len(values["_iptv_content_"]) == 1:
            selected_idx = values["_iptv_content_"][0]
            self.last_channel_idx = selected_idx
            log.debug("Channel selected from table: index=%d", selected_idx)
        
        # Fallback: use last remembered selection for context menu actions
        if selected_idx is None and event in ["Record", "Full Screen", "Play in VLC"]:
            if self.last_channel_idx is not None:
                selected_idx = self.last_channel_idx
                log.debug("Using last_channel_idx=%d for event %s", selected_idx, event)
        
        # Final fallback: read current selection directly from listbox element
        if selected_idx is None and channel_window:
            try:
                cur_sel = channel_window["_iptv_content_"].Widget.curselection()
                if cur_sel:
                    selected_idx = cur_sel[0]
                    self.last_channel_idx = selected_idx
                    log.debug("Channel selected from listbox: index=%d", selected_idx)
            except Exception as e:
                log.error("Failed to read listbox selection: %s", e)
        
        return selected_idx

    def parse_channel_block(self, selected_idx: int) -> Optional[Tuple[str, str]]:
        """
        Parse channel information from selected index.
        
        Args:
            selected_idx: Index of selected channel
            
        Returns:
            Tuple of (title, media_link) or None if parsing fails
        """
        log.debug("Parsing channel block at index: %d", selected_idx)
        try:
            block = Data.selected_list[selected_idx]
            parts = block.split("\n")
            extinf_line = parts[0] if parts else ""
            media_link = parts[1] if len(parts) > 1 else ""
            
            # Find media link if not on line 2
            if not media_link:
                for p in parts[1:]:
                    if p.strip() and not p.strip().startswith('#'):
                        media_link = p.strip()
                        break
            
            # Extract title from tvg-name or EXTINF
            m = re.search(r'tvg-name="(.*?)"', extinf_line)
            if m:
                title = m.group(1)
            else:
                title = extinf_line.split(",", 1)[-1] if "," in extinf_line else "Unknown"
            
            title = title.replace("|", "")
            
            log.info("Channel parsed: title='%s', url='%s'", title, media_link)
            return (title, media_link)
            
        except Exception as e:
            log.error("Failed to parse channel block at index %d: %s", 
                     selected_idx, e, exc_info=True)
            return None

    async def handle_channel_playback(self, event: str, values: dict,
                                     channel_window: Any, player_instance: Any,
                                     play_callback: callable) -> None:
        """
        Handle channel playback request.
        
        Args:
            event: Event name ('_iptv_content_', 'Full Screen', etc.)
            values: Window values dictionary
            channel_window: Channel window reference
            player_instance: Player instance
            play_callback: Async callback for playing media
        """
        log.info("Handling channel playback: event=%s", event)
        
        # Get selected channel index
        selected_idx = self.get_selected_channel_index(event, values, channel_window)
        
        if selected_idx is None:
            if event != "_iptv_content_":
                log.warning("No channel selected for playback")
                try:
                    sg.popup_error("No channel selected. Please click a channel first.",
                                 keep_on_top=True)
                except Exception as e:
                    log.error("Failed to show error popup: %s", e)
            return
        
        # Parse channel information
        parse_result = self.parse_channel_block(selected_idx)
        if parse_result is None:
            log.error("Failed to parse channel, aborting playback")
            return
        
        title, media_link = parse_result
        
        # Handle external VLC playback
        if event == "Play in VLC":
            log.info("Launching external VLC for: %s", media_link)
            try:
                launch_vlc_external(media_link)
                player_instance.players.stop()
                log.info("External VLC launched successfully")
            except Exception as e:
                log.error("Failed to launch external VLC: %s", e, exc_info=True)
            return
        
        # Handle recording
        if event == "Record" and Data.media_instance:
            log.info("Starting recording: %s -> %s", title, media_link)
            try:
                player_instance.players.stop()
            except Exception as e:
                log.warning("Failed to stop player before recording: %s", e)
            
            try:
                sout = _build_record_sout(title)
                media_obj = player_instance.vlc_instance.media_new(media_link)
                media_obj.add_option(sout)
                Data.media_instance = media_obj
                player_instance.players.set_media(media_obj)
                player_instance.players.play()
                log.info("Recording started: %s | %s", title, sout)
            except Exception as e:
                log.error("Failed to start recording: %s", e, exc_info=True)
            return
        
        # Handle normal/fullscreen playback
        log.info("Starting %s playback: %s", 
                "fullscreen" if event == "Full Screen" else "normal", title)
        try:
            Data.media_instance = player_instance.vlc_instance.media_new(media_link)
            await asyncio.ensure_future(
                play_callback(Data.media_instance, event == "Full Screen")
            )
        except Exception as e:
            log.error("Failed to create media instance or start playback: %s", 
                     e, exc_info=True)

    async def handle_category_selection(self, values: dict, window_manager: Any,
                                       player_instance: Any) -> None:
        """
        Handle category selection and update channel list.
        
        Args:
            values: Window values dictionary
            window_manager: WindowManager instance
            player_instance: Player instance
        """
        log.info("Handling category selection")
        try:
            from core.app import generate_list, get_selected
            
            # Generate channel list from selected categories
            Data.selected_list = await generate_list(values, Data.categories)
            player_instance._channels_master = list(Data.selected_list)
            
            # Store selected category indices
            try:
                Data.selected_category_indices = values.get("_table_countries_", []) or []
                log.debug("Selected category indices: %s", Data.selected_category_indices)
            except Exception as e:
                log.error("Failed to store category indices: %s", e)
                Data.selected_category_indices = []
            
            # Get display rows
            rows = get_selected()
            
            # Check for empty results
            table_values = None
            if "_table_countries_" in values:
                table_values = values["_table_countries_"]
            
            if not rows and table_values:
                selected_cat = Data.categories[table_values[0]]
                log.warning("No streams found for category: %s", selected_cat)
                sg.popup_error(
                    f"No streams found for category:\n'{selected_cat}'\n\n"
                    "This could mean:\n"
                    "• The M3U file doesn't have streams in this category\n"
                    "• The category name format doesn't match\n"
                    "• Check the logs for debugging info",
                    title="No Streams Found",
                    keep_on_top=True
                )
            
            # Update channel window
            if window_manager.channel_visible and window_manager.channel_window:
                window_manager.channel_window["_iptv_content_"].update(rows)
                log.info("Channel list updated: %d channels", len(rows))
            
        except Exception as e:
            log.error("Failed to handle category selection: %s", e, exc_info=True)

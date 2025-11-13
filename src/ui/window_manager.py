"""
Window management utilities for the IPTV player application.

Handles creation, positioning, and management of multiple windows including
category, channel, and main windows.
"""
import logging
import ctypes
from typing import Optional, Tuple, Any

from ui.layout import sg, build_category_panel_layout, build_channel_panel_layout
from core.config import ICON

# Module logger
log = logging.getLogger(__name__)


class WindowManager:
    """
    Manages multiple application windows and their positioning.
    
    Attributes:
        category_window: Category selection window
        channel_window: Channel list window
        category_visible: Category window visibility flag
        channel_visible: Channel window visibility flag
        main_window: Main application window reference
    """
    
    def __init__(self, main_window: Any):
        """
        Initialize the window manager.
        
        Args:
            main_window: Reference to main application window
        """
        log.info("Initializing WindowManager")
        self.main_window = main_window
        self.category_window: Optional[Any] = None
        self.channel_window: Optional[Any] = None
        self.category_visible: bool = True
        self.channel_visible: bool = True

    def create_category_window(self, ui_settings: Any) -> Any:
        """
        Create the category selection window.
        
        Args:
            ui_settings: UI settings object for styling
            
        Returns:
            Created category window
        """
        log.info("Creating category window")
        try:
            layout = build_category_panel_layout(ui_settings.get_font("table"))
            window = sg.Window(
                "",
                layout,
                icon=ICON,
                resizable=True,
                size=(320, 700),
                location=(10, 100),
                finalize=True,
                keep_on_top=False,
            )
            self.category_window = window
            self.category_visible = True
            log.info("Category window created successfully")
            return window
        except Exception as e:
            log.error("Failed to create category window: %s", e, exc_info=True)
            raise

    def create_channel_window(self, ui_settings: Any) -> Any:
        """
        Create the channel list window.
        
        Args:
            ui_settings: UI settings object for styling
            
        Returns:
            Created channel window
        """
        log.info("Creating channel window")
        try:
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            layout = build_channel_panel_layout(ui_settings.get_font("table"))
            window = sg.Window(
                "",
                layout,
                icon=ICON,
                resizable=True,
                size=(450, 700),
                location=(screen_width - 460, 100),
                finalize=True,
                keep_on_top=False,
            )
            self.channel_window = window
            self.channel_visible = True
            log.info("Channel window created successfully")
            return window
        except Exception as e:
            log.error("Failed to create channel window: %s", e, exc_info=True)
            raise

    def dock_panels(self) -> None:
        """Position category and channel windows relative to main window."""
        log.debug("Docking panels")
        try:
            self.main_window.TKroot.update_idletasks()
            x = self.main_window.TKroot.winfo_x()
            y = self.main_window.TKroot.winfo_y()
            w = 690
            h = 700
            screen_w = ctypes.windll.user32.GetSystemMetrics(0)
            margin = 6
            
            # Position category window to the left
            if self.category_window is not None and self.category_visible:
                cat_w, cat_h = 320, h
                cat_x = max(0, x - cat_w - margin)
                cat_y = y
                try:
                    self.category_window.move(cat_x, cat_y)
                    self.category_window.size = (cat_w, cat_h)
                    log.debug("Category window docked at (%d, %d)", cat_x, cat_y)
                except Exception as e:
                    log.warning("Failed to position category window: %s", e)
            
            # Position channel window to the right
            if self.channel_window is not None and self.channel_visible:
                ch_w, ch_h = 450, 700
                ch_x = min(screen_w - ch_w, x + w + margin)
                ch_y = y
                try:
                    self.channel_window.move(ch_x, ch_y)
                    self.channel_window.size = (ch_w, ch_h)
                    log.debug("Channel window docked at (%d, %d)", ch_x, ch_y)
                except Exception as e:
                    log.warning("Failed to position channel window: %s", e)
                    
        except Exception as e:
            log.error("Failed to dock panels: %s", e)

    def bind_search_entries(self) -> None:
        """Bind keyboard events to search entry fields."""
        log.debug("Binding search entry events")
        
        # Category search binding
        try:
            if self.category_window is not None and self.category_visible:
                cat_entry = self.category_window["_cat_search_"].Widget
                
                def _on_cat_key(ev=None):
                    """Handle category search keypress."""
                    try:
                        text = cat_entry.get()
                        self.main_window.write_event_value("__KEY_FILTER__", 
                                                           ("_cat_search_", text))
                        log.debug("Category search filter: '%s'", text)
                    except Exception as e:
                        log.error("Failed to handle category search: %s", e)
                
                cat_entry.bind("<KeyRelease>", _on_cat_key)
                log.debug("Category search binding complete")
        except Exception as e:
            log.error("Failed to bind category search: %s", e)
        
        # Channel search binding
        try:
            if self.channel_window is not None and self.channel_visible:
                ch_entry = self.channel_window["_ch_search_"].Widget
                
                def _on_ch_key(ev=None):
                    """Handle channel search keypress."""
                    try:
                        text = ch_entry.get()
                        self.main_window.write_event_value("__KEY_FILTER__", 
                                                          ("_ch_search_", text))
                        log.debug("Channel search filter: '%s'", text)
                    except Exception as e:
                        log.error("Failed to handle channel search: %s", e)
                
                ch_entry.bind("<KeyRelease>", _on_ch_key)
                log.debug("Channel search binding complete")
        except Exception as e:
            log.error("Failed to bind channel search: %s", e)

    def restore_layout(self, ui_settings: Any) -> None:
        """
        Restore both category and channel windows if closed.
        
        Args:
            ui_settings: UI settings object for styling
        """
        log.info("Restoring window layout")
        
        if self.category_window is None:
            log.debug("Restoring category window")
            self.create_category_window(ui_settings)
            self.bind_search_entries()
        
        if self.channel_window is None:
            log.debug("Restoring channel window")
            self.create_channel_window(ui_settings)
            self.bind_search_entries()
        
        self.dock_panels()
        log.info("Window layout restored")

    def setup_window_sync(self) -> None:
        """Setup window minimize/restore synchronization."""
        log.debug("Setting up window synchronization")
        
        _sync_flag = {"processing": False, "iconified": False}
        
        def _on_root_unmap(ev=None):
            """Handle main window minimize."""
            if _sync_flag["processing"]:
                return
            _sync_flag["processing"] = True
            try:
                state = self.main_window.TKroot.state()
                if state == "iconic":
                    _sync_flag["iconified"] = True
                    log.debug("Main window minimized, minimizing child windows")
                    
                    if self.category_visible and self.category_window:
                        try:
                            self.category_window.TKroot.iconify()
                        except Exception as e:
                            log.error("Failed to minimize category window: %s", e)
                    
                    if self.channel_visible and self.channel_window:
                        try:
                            self.channel_window.TKroot.iconify()
                        except Exception as e:
                            log.error("Failed to minimize channel window: %s", e)
            except Exception as e:
                log.error("Failed in unmap handler: %s", e)
            finally:
                _sync_flag["processing"] = False
        
        def _on_root_map(ev=None):
            """Handle main window restore."""
            if _sync_flag["processing"]:
                return
            _sync_flag["processing"] = True
            try:
                state = self.main_window.TKroot.state()
                if state == "normal" and _sync_flag["iconified"]:
                    log.debug("Main window restored, restoring child windows")
                    
                    if self.category_visible and self.category_window:
                        try:
                            self.category_window.TKroot.deiconify()
                            self.category_window.BringToFront()
                        except Exception as e:
                            log.error("Failed to restore category window: %s", e)
                    
                    if self.channel_visible and self.channel_window:
                        try:
                            self.channel_window.TKroot.deiconify()
                            self.channel_window.BringToFront()
                        except Exception as e:
                            log.error("Failed to restore channel window: %s", e)
                    
                    self.dock_panels()
                    _sync_flag["iconified"] = False
            except Exception as e:
                log.error("Failed in map handler: %s", e)
            finally:
                _sync_flag["processing"] = False
        
        def _on_window_configure(ev=None):
            """Handle main window move/resize."""
            self.dock_panels()
        
        try:
            self.main_window.TKroot.bind("<Unmap>", _on_root_unmap)
            self.main_window.TKroot.bind("<Map>", _on_root_map)
            self.main_window.TKroot.bind("<Configure>", _on_window_configure)
            log.debug("Window sync bindings complete")
        except Exception as e:
            log.error("Failed to setup window sync: %s", e)

    def close_category_window(self) -> None:
        """Close the category window."""
        log.info("Closing category window")
        try:
            if self.category_window:
                self.category_window.close()
            self.category_window = None
            self.category_visible = False
            log.debug("Category window closed")
        except Exception as e:
            log.error("Failed to close category window: %s", e)

    def close_channel_window(self) -> None:
        """Close the channel window."""
        log.info("Closing channel window")
        try:
            if self.channel_window:
                self.channel_window.close()
            self.channel_window = None
            self.channel_visible = False
            log.debug("Channel window closed")
        except Exception as e:
            log.error("Failed to close channel window: %s", e)

    def get_active_windows(self) -> list:
        """
        Get list of currently active windows.
        
        Returns:
            List of active window references
        """
        window_list = [self.main_window]
        if self.category_visible and self.category_window:
            window_list.append(self.category_window)
        if self.channel_visible and self.channel_window:
            window_list.append(self.channel_window)
        log.debug("Active windows count: %d", len(window_list))
        return window_list

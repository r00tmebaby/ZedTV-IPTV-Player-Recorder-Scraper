"""
Playback control module for media playback operations.

This module handles media playback initialization, control, and error handling.
"""
import logging
from sys import platform as platform
from typing import Any, Optional

from ui.layout import sg

# Module logger
log = logging.getLogger(__name__)


async def play_media(media_play_link: Any, full_screen: bool, player_instance: Any,
                     main_window: Any, canvas_element: Any, 
                     clear_background_callback: callable) -> None:
    """
    Play media content in normal or fullscreen mode.
    
    Args:
        media_play_link: Media object or URL string to play
        full_screen: Whether to play in fullscreen mode
        player_instance: Player class instance
        main_window: Main application window
        canvas_element: Canvas element for video display
        clear_background_callback: Callback to clear background image
    """
    media_url = getattr(media_play_link, 'get_mrl', lambda: str(media_play_link))()
    log.info("Starting playback: %s, fullscreen=%s", media_url, full_screen)
    
    # Check if VLC is available
    try:
        if player_instance.is_dummy_instance():
            msg = (
                "VLC (libvlc) is not available. Playback won't work inside the app.\n\n"
                "Options:\n"
                "• Install VLC and try again\n"
                "• Or set PYTHON_VLC_LIB_PATH to libvlc.dll and PYTHON_VLC_MODULE_PATH to VLC plugins\n"
                "• Or use 'Play in VLC' from the context menu"
            )
            log.error("VLC not available: %s", msg.replace('\n', ' '))
            try:
                sg.popup_error(msg, keep_on_top=True)
            except Exception as e:
                log.error("Failed to show error popup: %s", e)
            return
    except Exception as e:
        log.error("Failed to check VLC availability: %s", e)
        return
    
    # Stop any current playback
    try:
        if player_instance.players is not None:
            player_instance.players.stop()
            log.debug("Stopped previous playback")
    except Exception as e:
        log.warning("Failed to stop previous playback: %s", e)
    
    # Set the media to play
    try:
        player_instance.players.set_media(media_play_link)
        log.debug("Media set successfully")
    except Exception as e:
        log.error("Failed to set media: %s", e)
        return
    
    # Clear background
    clear_background_callback()
    
    # Detach any previous window handle to avoid stale bindings
    try:
        player_instance.players.set_xwindow(0)
        player_instance.players.set_hwnd(0)
        log.debug("Detached previous window handles")
    except Exception as e:
        log.warning("Failed to detach window handles: %s", e)
    
    if full_screen:
        log.debug("Entering fullscreen mode")
        player_instance.enter_fullscreen_window(main_window)
    else:
        log.debug("Playing in normal mode")
        try:
            canvas_widget = canvas_element.Widget
            canvas_widget.update_idletasks()
            canvas_id = canvas_widget.winfo_id()
            
            if platform.startswith("linux"):
                player_instance.players.set_xwindow(canvas_id)
                log.debug("Attached to xwindow: %s", canvas_id)
            else:
                player_instance.players.set_hwnd(canvas_id)
                log.debug("Attached to hwnd: %s", canvas_id)
        except Exception as e:
            log.error("Failed to attach player to canvas: %s", e)
    
    # Start playback
    try:
        player_instance.players.play()
        log.info("Playback started successfully in %s mode", 
                "fullscreen" if full_screen else "normal")
    except Exception as e:
        log.error("Failed to start playback: %s", e)


def stop_playback(player_instance: Any, show_background_callback: callable) -> None:
    """
    Stop media playback and show background.
    
    Args:
        player_instance: Player class instance
        show_background_callback: Callback to show background image
    """
    log.info("Stopping playback")
    try:
        player_instance.players.stop()
        show_background_callback()
        log.debug("Playback stopped, background shown")
    except Exception as e:
        log.error("Failed to stop playback: %s", e)

"""
Main application entry point for ZedTV IPTV Player.

This module orchestrates the application initialization and main event loop.
"""
import asyncio
import ctypes
import logging
from typing import Optional

from __version__ import __version__, FULL_VERSION_STRING, APP_NAME
from core.config import ICON
from ui.layout import sg, build_layout
from core.models import Data
from core.settings import _auto_restore_last
from core.app import get_categories
from core.vlc_settings import VLCSettings
from core.ui_settings import UISettings
from core.logging_settings import LoggingSettings
from core.logger_setup import init_logging
from core.player import Player
from ui.background import BackgroundManager
from ui.window_manager import WindowManager
from ui.splash_screen import SplashScreen
from ui.event_handlers import EventHandler
from ui.channel_handler import ChannelHandler
from utils.playback import play_media, stop_playback
from utils.epg_loader import load_epg_async
from utils.search_handler import SearchHandler

# Module logger (initialized after logging setup)
log: Optional[logging.Logger] = None


async def main() -> None:
    """
    Main application entry point and event loop.
    
    Initializes all components, creates UI windows, and runs the main event loop.
    """
    global log
    
    # Initialize logging first
    logging_settings = LoggingSettings()
    app_logger = init_logging(logging_settings.settings)
    log = app_logger.getChild("main")
    log.info("="*60)
    log.info("%s v%s starting", APP_NAME, __version__)
    log.info("="*60)
    log.debug("Application main() starting")

    # Initialize UI settings and theme
    ui_settings = UISettings()
    ui_settings.apply_theme()
    fonts = ui_settings.get_all_fonts()
    sg.set_options(font=fonts["normal"], button_element_size=(10, 1), element_padding=(0, 0))
    log.debug("UI settings and theme applied")

    # Load initial categories
    Data.categories = get_categories()
    log.info("Loaded %d categories on startup", len(Data.categories or []))

    # EPG will be loaded in background after UI is ready
    epg_loading_started = False

    # Validate Pillow version
    try:
        import PIL
        from PIL import Image as _Img
        ver = getattr(PIL, '__version__', 'unknown')
        if tuple(int(x) for x in ver.split('.')[:2]) < (10, 0):
            log.warning("Pillow version %s < 10.0.0 - consider upgrading", ver)
        else:
            log.debug("Pillow version OK: %s", ver)
    except Exception as e:
        log.warning("Could not validate Pillow version: %s", e)

    # Initialize VLC settings
    vlc_settings = VLCSettings()
    log.debug("VLC settings initialized")

    # Show splash screen
    splash = SplashScreen()
    splash.show()

    # Build main layout
    main_layout, _, _ = build_layout(ui_settings)
    log.debug("Main layout built")

    # Create main window
    splash.update_progress(40, "Creating main window...")
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    
    window = sg.Window(
        f"ZED-TV IPTV Player v{__version__}",
        main_layout,
        icon=ICON,
        resizable=False,
        return_keyboard_events=True,
        use_default_focus=True,
        size=(690, 450),
        location=(screen_width // 3, 40),
    ).finalize()
    log.info("Main window created")

    # Create window manager and child windows
    splash.update_progress(50, "Creating panels...")
    window_manager = WindowManager(window)
    window_manager.create_category_window(ui_settings)
    splash.update_progress(60, "Creating channel panel...")
    window_manager.create_channel_window(ui_settings)
    splash.update_progress(70)
    
    # Setup window synchronization
    window_manager.setup_window_sync()
    window_manager.bind_search_entries()
    window_manager.dock_panels()
    log.debug("Window manager configured")

    # Auto-restore last session
    splash.update_progress(80, "Restoring last session...")
    try:
        _auto_restore_last(window, window_manager.category_window)
        log.debug("Auto-restore completed")
    except Exception as e:
        log.debug("Auto-restore failed: %s", e)

    # Close splash screen
    splash.close()

    # Initialize Player
    Player.initialize(vlc_settings)
    log.info("Player initialized")
    
    # Check if using dummy VLC instance and notify user
    if Player.is_dummy_instance():
        try:
            sg.popup_error(
                "VLC (libvlc) could not be initialized. In-app playback will be disabled.\n\n"
                "To enable playback:\n"
                "• Install VLC, or\n"
                "• Set PYTHON_VLC_LIB_PATH to libvlc.dll and PYTHON_VLC_MODULE_PATH to VLC plugins folder, or\n"
                "• Use 'Play in VLC' to launch external VLC.",
                keep_on_top=True
            )
        except Exception as e:
            log.error("Failed to show VLC error popup: %s", e)

    # Initialize background manager
    background_mgr = BackgroundManager(window["_canvas_video_"])
    background_mgr.show_background(Player)
    log.debug("Background manager initialized")

    # Initialize handlers
    event_handler = EventHandler()
    channel_handler = ChannelHandler()
    search_handler = SearchHandler()
    log.debug("Event handlers initialized")

    # Create playback callback wrappers
    async def play(media, fullscreen=False):
        """Play media wrapper."""
        await play_media(media, fullscreen, Player, window,
                        window["_canvas_video_"], background_mgr.clear_background)
    
    def stop():
        """Stop playback wrapper."""
        stop_playback(Player, lambda: background_mgr.show_background(Player))

    # Main event loop
    log.info("Entering main event loop")
    
    while True:
        # Read events from all windows
        active_window, event, values = sg.read_all_windows(timeout=100)

        # Normalize menu event text (strip '&' accelerators)
        ev = event.replace('&', '') if isinstance(event, str) else event

        # Start EPG loading in background after first event loop
        if not epg_loading_started:
            epg_loading_started = True
            try:
                asyncio.create_task(load_epg_async(Data))
                log.debug("EPG background loading started")
            except Exception as e:
                log.error("Failed to start EPG background task: %s", e)

        if ev == sg.TIMEOUT_KEY:
            continue
        
        # Track channel table clicks
        if isinstance(event, tuple):
            event_handler.handle_channel_table_click(event)
            channel_handler.last_channel_idx = event_handler.last_channel_idx
        
        # Handle exit from fullscreen
        if ev == "__EXIT_FULLSCREEN__":
            log.debug("Exiting fullscreen")
            Player.exit_fullscreen_window(window, window["_canvas_video_"],
                                         lambda: background_mgr.show_background(Player))
            continue
        
        # Handle search filters
        if ev == "__KEY_FILTER__":
            try:
                field, text = values[event]
                search_handler.handle_search_event(field, text, Data,
                                                   window_manager.category_window,
                                                   window_manager.channel_window,
                                                   Player)
            except Exception as e:
                log.error("Key filter handling failed: %s", e, exc_info=True)
            continue
        
        # Handle window show events
        if ev == "Show Categories" and not window_manager.category_visible:
            log.info("Showing category window")
            window_manager.create_category_window(ui_settings)
            window_manager.bind_search_entries()
            window_manager.dock_panels()
            continue
        
        if ev == "Show Channels" and not window_manager.channel_visible:
            log.info("Showing channel window")
            window_manager.create_channel_window(ui_settings)
            window_manager.bind_search_entries()
            window_manager.dock_panels()
            continue
        
        if ev == "Restore Layout":
            log.info("Restoring layout")
            window_manager.restore_layout(ui_settings)
            continue
        
        # Handle window close events
        if ev in (sg.WIN_CLOSED, "Exit"):
            log.info("Exit triggered from window=%s", getattr(active_window, 'Title', 'main'))
            if active_window == window:
                break
            elif active_window == window_manager.category_window:
                window_manager.close_category_window()
                continue
            elif active_window == window_manager.channel_window:
                window_manager.close_channel_window()
                continue
        
        # Menu events
        if ev == "About":
            event_handler.handle_about()
        elif ev == "How to Use":
            event_handler.handle_help()
        elif ev == "Open Logs Folder":
            event_handler.handle_open_logs_folder()
        elif ev == "Logging Settings":
            event_handler.handle_logging_settings(logging_settings)
        elif ev == "View Current Log":
            event_handler.handle_view_current_log()
        elif ev == "Open":
            event_handler.handle_open_playlist(window_manager)
        elif ev == "Custom List" and Data.filename:
            await event_handler.handle_custom_list(values)
        elif ev == "Add Account":
            event_handler.handle_add_account(window_manager)
        elif ev == "Accounts...":
            event_handler.handle_choose_account(window_manager)
        elif ev == "Reload from Current" and Data.xtream_account is not None:
            event_handler.handle_reload_account(window_manager)
        elif ev == "UI Settings":
            if event_handler.handle_ui_settings(ui_settings):
                break  # Exit for restart
        elif ev == "VLC Settings":
            event_handler.handle_vlc_settings(Player.settings)
        elif ev == "IP Info":
            event_handler.handle_ip_info()
        elif ev == "_table_countries_" and Data.categories:
            await channel_handler.handle_category_selection(values, window_manager, Player)
        elif ev == "Stop":
            stop()
        elif ev in ["_iptv_content_", "Record", "Full Screen", "Play in VLC"]:
            await channel_handler.handle_channel_playback(
                ev, values, window_manager.channel_window, Player, play
            )
        
        # Handle keyboard shortcuts
        if event is not None and event is not sg.TIMEOUT_KEY:
            if isinstance(event, str) and len(event) == 1 and ord(event) == 27:  # ESC
                if Player.is_fullscreen:
                    Player.exit_fullscreen_window(window, window["_canvas_video_"],
                                                 lambda: background_mgr.show_background(Player))
                    log.debug("ESC pressed - exited fullscreen")
                else:
                    stop()
                    log.debug("ESC pressed - playback stopped")

    log.info("Application exiting - cleanup in progress")


if __name__ == "__main__":
    asyncio.run(main())

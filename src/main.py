"""
Main application entry point for ZedTV IPTV Player.

This module orchestrates the application initialization and main event loop.
"""

# Early crash capture before importing the rest of the app
import sys as _sys
import os as _os


def _write_startup_error(exc_type, exc, tb) -> None:
    try:
        import traceback
        import datetime

        base_dir = (
            _os.path.dirname(_sys.executable)
            if getattr(_sys, "frozen", False)
            else _os.getcwd()
        )
        log_path = _os.path.join(base_dir, "startup_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(
                "\n=== Startup error at %s ===\n"
                % datetime.datetime.now().isoformat()
            )
            f.write("%s: %s\n" % (exc_type.__name__, exc))
            traceback.print_tb(tb, file=f)
            # Useful env context
            f.write(
                "PYTHON_VLC_LIB_PATH=%s\n"
                % _os.environ.get("PYTHON_VLC_LIB_PATH", "")
            )
            f.write(
                "PYTHON_VLC_MODULE_PATH=%s\n"
                % _os.environ.get("PYTHON_VLC_MODULE_PATH", "")
            )
            f.write(
                "VLC_PLUGIN_PATH=%s\n" % _os.environ.get("VLC_PLUGIN_PATH", "")
            )
            f.write(
                "PATH contains exe dir? %s\n"
                % (base_dir in _os.environ.get("PATH", ""))
            )
        # Also try the app logger if already initialized
        try:
            import logging as _logging

            _logging.getLogger().error(
                "Uncaught exception", exc_info=(exc_type, exc, tb)
            )
            for _h in _logging.getLogger().handlers:
                try:
                    _h.flush()
                except Exception:
                    pass
        except Exception:
            pass
        # Best-effort user notice
        try:
            import ctypes

            msg = (
                "ZedTV failed to start.\n\n"
                "A startup_error.log was written next to the .exe.\n"
                "Please share it so we can fix the issue."
            )
            ctypes.windll.user32.MessageBoxW(
                None, msg, "ZedTV Startup Error", 0x00000010
            )
        except Exception:
            pass
    except Exception:
        pass


_sys.excepthook = _write_startup_error

# Now import the rest of the app
import asyncio
import ctypes
import logging
import os
import sys
from typing import List, Optional

from __version__ import APP_NAME, __version__
from core.app import get_categories
from core.config import ICON
from core.logger_setup import init_logging
from core.logging_settings import LoggingSettings
from core.models import Data

# Ensure VLC (libvlc) can be found in frozen builds before importing Player
if getattr(sys, "frozen", False):
    try:
        exe_dir = os.path.dirname(sys.executable)
        candidate_libs = [
            os.path.join(exe_dir, "libvlc.dll"),
            os.path.join(exe_dir, "libs", "win", "libvlc.dll"),
        ]
        candidate_plugins = [
            os.path.join(exe_dir, "plugins"),
            os.path.join(exe_dir, "libs", "win", "plugins"),
        ]
        lib_path = next((p for p in candidate_libs if os.path.exists(p)), None)
        plugins_path = next(
            (p for p in candidate_plugins if os.path.isdir(p)), None
        )

        # Prepend likely dirs to PATH and DLL search
        dll_dirs = [exe_dir, os.path.join(exe_dir, "libs", "win")]
        for d in dll_dirs:
            if os.path.isdir(d):
                os.environ["PATH"] = (
                    d + os.pathsep + os.environ.get("PATH", "")
                )
                try:
                    if hasattr(os, "add_dll_directory"):
                        os.add_dll_directory(d)
                except Exception:
                    pass

        if lib_path:
            os.environ.setdefault("PYTHON_VLC_LIB_PATH", lib_path)
        if plugins_path:
            os.environ.setdefault("PYTHON_VLC_MODULE_PATH", plugins_path)
            os.environ.setdefault("VLC_PLUGIN_PATH", plugins_path)
    except Exception:
        # Fail silently; Player will fall back to system VLC detection
        pass
from core.player import Player
from core.settings import _auto_restore_last
from core.ui_settings import UISettings
from core.vlc_settings import VLCSettings
from ui.background import BackgroundManager
from ui.channel_handler import ChannelHandler
from ui.event_handlers import EventHandler
from ui.global_search import show_global_search
from ui.layout import build_layout, sg
from ui.playback_controls import PlaybackControls
from ui.splash_screen import SplashScreen
from ui.window_manager import WindowManager
from utils.epg_loader import load_epg_async
from utils.playback import play_media, stop_playback
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
    log.info("=" * 60)
    log.info("%s v%s starting", APP_NAME, __version__)
    log.info("=" * 60)
    log.debug("Application main() starting")

    # Initialize UI settings and theme
    ui_settings = UISettings()
    ui_settings.apply_theme()
    fonts = ui_settings.get_all_fonts()
    sg.set_options(
        font=fonts["normal"],
        button_element_size=(10, 1),
        element_padding=(0, 0),
    )
    log.debug("UI settings and theme applied")

    # Load initial categories
    Data.categories = get_categories()
    log.info("Loaded %d categories on startup", len(Data.categories or []))

    # EPG will be loaded in background after UI is ready
    epg_loading_started = False

    # Validate Pillow version
    try:
        import PIL

        ver = getattr(PIL, "__version__", "unknown")
        if tuple(int(x) for x in ver.split(".")[:2]) < (10, 0):
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
                keep_on_top=True,
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
    playback_controls = PlaybackControls(Player, window)
    log.debug("Event handlers initialized")

    # Initially disable all playback controls (no media playing)
    playback_controls.update_controls_state(False)
    log.debug("Playback controls initially disabled")

    # Helper function to flash a button (visual feedback for keyboard shortcuts)
    def flash_button(button_key: str, duration_ms: int = 150):
        """
        Flash a button to provide visual feedback.

        Args:
            button_key: The key of the button to flash
            duration_ms: Duration of the flash in milliseconds
        """
        try:
            if button_key in window.AllKeysDict:
                button = window[button_key]
                original_color = button.ButtonColor
                # Flash to a lighter color
                button.update(button_color=("white", "#1abc9c"))
                # Schedule color restoration
                window.TKroot.after(duration_ms, lambda: button.update(button_color=original_color))
        except Exception as e:
            log.debug("Failed to flash button %s: %s", button_key, e)

    # Keyboard shortcut mappings (key -> button_key, action)
    keyboard_shortcuts = {
        "Left:113": ("_seek_back_30_", lambda: playback_controls.seek_backward(30)),
        "Right:114": ("_seek_forward_30_", lambda: playback_controls.seek_forward(30)),
        "s": ("_subtitles_", lambda: playback_controls.show_subtitle_menu()),
        "S": ("_subtitles_", lambda: playback_controls.show_subtitle_menu()),
        "a": ("_audio_tracks_", lambda: playback_controls.show_audio_menu()),
        "A": ("_audio_tracks_", lambda: playback_controls.show_audio_menu()),
        "d": ("_speed_", lambda: playback_controls.show_speed_menu()),
        "D": ("_speed_", lambda: playback_controls.show_speed_menu()),
        "space": ("_pause_play_", None),  # Special handling below
        "f": ("_fullscreen_btn_", None),  # Special handling below
        "F": ("_fullscreen_btn_", None),
    }

    # Global search shortcut (Ctrl+F)
    global_search_key = ui_settings.get_key_binding("global_search")
    log.info("Global search keyboard shortcut: %s", global_search_key)

    # Helper function to collect all channels from parsed data
    def get_all_channels() -> List[dict]:
        """
        Collect all channels from parsed data for global search.

        Returns:
            List of channel dictionaries with title, category, rating, year, url
        """
        all_channels = []

        if Data.m3u_parser and Data.parsed_channels:
            # Use parsed channels from m3u_parser
            for channel in Data.parsed_channels:
                all_channels.append({
                    "title": channel.title or "Unknown",
                    "category": channel.group_title or "",
                    "rating": getattr(channel, "rating", ""),
                    "year": getattr(channel, "year", ""),
                    "url": channel.url or "",
                    "channel_obj": channel  # Store original channel object
                })
        elif Data.selected_list:
            # Fallback to selected_list if parser not available
            for item in Data.selected_list:
                # Parse basic info from EXTINF line
                title = "Unknown"
                if "," in item:
                    parts = item.split(",", 1)
                    if len(parts) > 1:
                        title = parts[1].strip()

                all_channels.append({
                    "title": title,
                    "category": "",
                    "rating": "",
                    "year": "",
                    "url": "",
                    "raw": item
                })

        log.debug("Collected %d channels for global search", len(all_channels))
        return all_channels

    # Global search play callback
    async def play_from_search(channel_dict: dict):
        """
        Play a channel selected from global search.

        Args:
            channel_dict: Channel dictionary from search results
        """
        try:
            # Extract URL and title
            url = channel_dict.get("url", "")
            title = channel_dict.get("title", "Unknown")

            if not url:
                log.warning("No URL found for channel: %s", title)
                sg.popup_error("Cannot play: No URL found", title="Error", keep_on_top=True)
                return

            log.info("Playing from global search: %s", title)

            # Create media object
            media = f"#EXTINF:-1,{title}\n{url}"

            # Play the media
            await play(media, fullscreen=False)

            # Enable control buttons
            playback_controls.update_controls_state(True)

        except Exception as e:
            log.error("Failed to play from search: %s", e, exc_info=True)
            sg.popup_error(f"Failed to play: {e}", title="Error", keep_on_top=True)

    # Create playback callback wrappers
    async def play(media, fullscreen=False):
        """Play media wrapper."""
        await play_media(
            media,
            fullscreen,
            Player,
            window,
            window["_canvas_video_"],
            background_mgr.clear_background,
        )

    def stop():
        """Stop playback wrapper."""
        stop_playback(Player, lambda: background_mgr.show_background(Player))

    # Helper function to refresh playback timer
    def update_time_display():
        """Refresh the playback timer and control button states."""
        try:
            has_media = False
            if Player.players:
                try:
                    state = Player.players.get_state()
                    has_media = state in [0, 1, 2, 3, 4]
                except Exception:
                    has_media = Player.players.is_playing()

            if has_media:
                time_info = playback_controls.get_time_info()
                current_str = playback_controls.format_time(time_info['current'])
                total_str = playback_controls.format_time(time_info['total'])
                rate = time_info.get('rate', 1.0)
                if abs(rate - 1.0) > 0.01:
                    time_display = f"{current_str} / {total_str} ({rate}x)"
                else:
                    time_display = f"{current_str} / {total_str}"
                window["_time_display_"].update(time_display)
                try:
                    if Player.players.get_state() == 4:
                        window["_pause_play_"].update("▶ Play")
                    else:
                        window["_pause_play_"].update("⏸ Pause")
                except Exception:
                    window["_pause_play_"].update("⏸ Pause")
                playback_controls.update_controls_state(True)
            else:
                window["_time_display_"].update("00:00 / 00:00")
                window["_pause_play_"].update("⏸ Pause")
                playback_controls.update_controls_state(False)
        except Exception as exc:
            log.debug("Failed to update time display: %s", exc)

    # Main event loop
    log.info("Entering main event loop")

    while True:
        # Read events from all windows
        active_window, event, values = sg.read_all_windows(timeout=100)

        # Normalize menu event text (strip '&' accelerators)
        ev = event.replace("&", "") if isinstance(event, str) else event

        # Start EPG loading in background after first event loop
        if not epg_loading_started:
            epg_loading_started = True
            try:
                asyncio.create_task(load_epg_async(Data))
                log.debug("EPG background loading started")
            except Exception as e:
                log.error("Failed to start EPG background task: %s", e)

        if event == sg.TIMEOUT_KEY:
            update_time_display()
            continue

        # Handle global search (Ctrl+F)
        if ev == global_search_key or ev == "Global Search (Ctrl+F)":
            try:
                all_channels = get_all_channels()
                if not all_channels:
                    sg.popup("No channels loaded. Please open an M3U file or Xtream account first.",
                            title="Global Search", keep_on_top=True)
                    log.info("Global search: no channels available")
                else:
                    log.info("Opening global search with %d channels", len(all_channels))
                    # Create async wrapper for play callback
                    def sync_play_wrapper(channel_dict):
                        asyncio.create_task(play_from_search(channel_dict))

                    show_global_search(all_channels, sync_play_wrapper)
            except Exception as e:
                log.error("Failed to open global search: %s", e, exc_info=True)
                sg.popup_error(f"Failed to open global search: {e}", title="Error", keep_on_top=True)
            continue

        # Handle keyboard shortcuts (only if main window has focus)
        if active_window == window and ev in keyboard_shortcuts:
            button_key, action = keyboard_shortcuts[ev]

            # Check if media is playing for playback controls
            has_media = Player.players and (Player.players.is_playing() or
                                           (Player.players.get_state() in [1, 2, 3, 4] if Player.players else False))

            if button_key == "_pause_play_":
                if has_media:
                    flash_button(button_key)
                    try:
                        if Player.players and Player.players.is_playing():
                            Player.players.pause()
                            window["_pause_play_"].update("▶ Play")
                            log.info("Playback paused (keyboard: %s)", ev)
                        elif Player.players:
                            Player.players.play()
                            window["_pause_play_"].update("⏸ Pause")
                            log.info("Playback resumed (keyboard: %s)", ev)
                    except Exception as e:
                        log.error("Failed to toggle pause via keyboard: %s", e)
                continue

            elif button_key == "_fullscreen_btn_":
                if has_media and Data.media_instance:
                    flash_button(button_key)
                    if not Player.is_fullscreen:
                        try:
                            Player.enter_fullscreen_window(window, playback_controls)
                            log.info("Entered fullscreen (keyboard: %s)", ev)
                        except Exception as e:
                            log.error("Failed to enter fullscreen via keyboard: %s", e)
                    else:
                        try:
                            Player.exit_fullscreen_window(
                                window,
                                window["_canvas_video_"],
                                lambda: background_mgr.show_background(Player),
                            )
                            log.info("Exited fullscreen (keyboard: %s)", ev)
                        except Exception as e:
                            log.error("Failed to exit fullscreen via keyboard: %s", e)
                continue

            elif has_media and action:
                # Execute the action and flash the button
                flash_button(button_key)
                try:
                    action()
                    log.info("Executed %s (keyboard: %s)", button_key, ev)
                except Exception as e:
                    log.error("Failed to execute %s via keyboard: %s", button_key, e)
                continue

        # Track channel table clicks
        if isinstance(event, tuple):
            event_handler.handle_channel_table_click(event)
            channel_handler.last_channel_idx = event_handler.last_channel_idx

        # Handle exit from fullscreen
        if ev == "__EXIT_FULLSCREEN__":
            try:
                Player.exit_fullscreen_window(
                    window,
                    window["_canvas_video_"],
                    lambda: background_mgr.show_background(Player),
                )
                log.debug("Exited fullscreen via __EXIT_FULLSCREEN__ event")
            except Exception as e:
                log.error("Failed to exit fullscreen: %s", e, exc_info=True)
            continue

        # Handle search filters
        if ev == "__KEY_FILTER__":
            try:
                field, text = values[event]
                search_handler.handle_search_event(
                    field,
                    text,
                    Data,
                    window_manager.category_window,
                    window_manager.channel_window,
                    Player,
                )
            except Exception as e:
                log.error("Key filter handling failed: %s", e, exc_info=True)
            continue

        # Handle playback control events
        if ev == "_seek_back_30_":
            playback_controls.seek_backward(30)
            continue
        elif ev == "_seek_back_10_":
            playback_controls.seek_backward(10)
            continue
        elif ev == "_seek_forward_10_":
            playback_controls.seek_forward(10)
            continue
        elif ev == "_seek_forward_30_":
            playback_controls.seek_forward(30)
            continue
        elif ev == "_pause_play_":
            try:
                if Player.players and Player.players.is_playing():
                    Player.players.pause()
                    window["_pause_play_"].update("▶ Play")
                    log.debug("Playback paused")
                elif Player.players:
                    Player.players.play()
                    window["_pause_play_"].update("⏸ Pause")
                    log.debug("Playback resumed")
            except Exception as e:
                log.error("Failed to toggle pause: %s", e, exc_info=True)
            continue
        elif ev == "_subtitles_":
            playback_controls.show_subtitle_menu()
            continue
        elif ev == "_audio_tracks_":
            playback_controls.show_audio_menu()
            continue
        elif ev == "_speed_":
            playback_controls.show_speed_menu()
            continue
        elif ev == "_fullscreen_btn_":
            # Toggle fullscreen if media is playing
            if Player.players and Player.players.is_playing() and Data.media_instance:
                if not Player.is_fullscreen:
                    try:
                        Player.enter_fullscreen_window(window, playback_controls)
                        log.debug("Entered fullscreen via button")
                    except Exception as e:
                        log.error("Failed to enter fullscreen: %s", e, exc_info=True)
                else:
                    try:
                        Player.exit_fullscreen_window(
                            window,
                            window["_canvas_video_"],
                            lambda: background_mgr.show_background(Player),
                        )
                        log.debug("Exited fullscreen via button")
                    except Exception as e:
                        log.error("Failed to exit fullscreen: %s", e, exc_info=True)
            else:
                log.debug("Cannot toggle fullscreen: no media playing")
            continue

        # Handle custom fullscreen enter event
        if ev == "__ENTER_FULLSCREEN__":
            if Player.players and Player.players.is_playing() and Data.media_instance:
                if not Player.is_fullscreen:
                    try:
                        Player.enter_fullscreen_window(window, playback_controls)
                        log.debug("Entered fullscreen via event")
                    except Exception as e:
                        log.error("Failed to enter fullscreen: %s", e, exc_info=True)
            continue

        # Update time display and control button states on every loop iteration
        try:
            # Check if media is loaded (playing or paused)
            has_media = False
            if Player.players:
                try:
                    state = Player.players.get_state()
                    # States: 0=NothingSpecial, 1=Opening, 2=Buffering, 3=Playing, 4=Paused, 5=Stopped, 6=Ended, 7=Error
                    has_media = state in [1, 2, 3, 4]  # Opening, Buffering, Playing, or Paused
                except Exception:
                    has_media = Player.players.is_playing()

            if has_media:
                time_info = playback_controls.get_time_info()
                current_str = playback_controls.format_time(time_info['current'])
                total_str = playback_controls.format_time(time_info['total'])
                rate = time_info.get('rate', 1.0)

                # Show playback speed if not normal (1.0x)
                if abs(rate - 1.0) > 0.01:  # Not exactly 1.0
                    time_display = f"{current_str} / {total_str} ({rate}x)"
                else:
                    time_display = f"{current_str} / {total_str}"

                window["_time_display_"].update(time_display)

                # Update pause button text based on state
                try:
                    if Player.players.get_state() == 4:  # Paused state
                        window["_pause_play_"].update("▶ Play")
                    else:
                        window["_pause_play_"].update("⏸ Pause")
                except Exception:
                    window["_pause_play_"].update("⏸ Pause")

                # Enable control buttons when media is loaded
                playback_controls.update_controls_state(True)
            else:
                window["_time_display_"].update("00:00 / 00:00")
                window["_pause_play_"].update("⏸ Pause")

                # Disable control buttons when no media
                playback_controls.update_controls_state(False)
        except Exception as e:
            log.debug("Failed to update time display: %s", e)

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
            log.info(
                "Exit triggered from window=%s",
                getattr(active_window, "Title", "main"),
            )
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
            await channel_handler.handle_category_selection(
                values, window_manager, Player
            )
        elif ev == "Stop":
            stop()
            playback_controls.update_controls_state(False)
            log.debug("Disabled control buttons after stop")
        elif ev in [
            "_iptv_content_",
            "Record",
            "Full Screen",
            "Play in VLC",
            "Send to Browser",
        ]:
            await channel_handler.handle_channel_playback(
                ev, values, window_manager.channel_window, Player, play
            )
            # Enable control buttons after playback starts
            if ev in ["_iptv_content_", "Record", "Full Screen"]:
                playback_controls.update_controls_state(True)
                log.debug("Enabled control buttons after playback start")
        # Handle keyboard shortcuts
        if event is not None and event is not sg.TIMEOUT_KEY:
            # ESC key
            if (
                isinstance(event, str) and len(event) == 1 and ord(event) == 27
            ):  # ESC
                if Player.is_fullscreen:
                    try:
                        Player.exit_fullscreen_window(
                            window,
                            window["_canvas_video_"],
                            lambda: background_mgr.show_background(Player),
                        )
                        log.debug("ESC pressed - exited fullscreen")
                    except Exception as e:
                        log.error("Failed to exit fullscreen with ESC: %s", e, exc_info=True)
                else:
                    stop()
                    playback_controls.update_controls_state(False)
                    log.debug("ESC pressed - playback stopped")
            # Space key - pause/play
            elif isinstance(event, str) and event == " ":
                try:
                    if Player.players and Player.players.is_playing():
                        Player.players.pause()
                        window["_pause_play_"].update("▶ Play")
                        log.debug("Space pressed - paused")
                    elif Player.players:
                        Player.players.play()
                        window["_pause_play_"].update("⏸ Pause")
                        log.debug("Space pressed - resumed")
                except Exception as e:
                    log.error("Failed to toggle pause with space: %s", e)
            # Arrow keys for seeking
            elif isinstance(event, str) and event in ["Left:37", "Right:39"]:
                if event == "Left:37":  # Left arrow - seek backward
                    playback_controls.seek_backward(5)
                    log.debug("Left arrow - seek backward 5s")
                elif event == "Right:39":  # Right arrow - seek forward
                    playback_controls.seek_forward(5)
                    log.debug("Right arrow - seek forward 5s")
            # F key for fullscreen
            elif isinstance(event, str) and event.lower() == "f":
                if Player.players and Player.players.is_playing() and Data.media_instance:
                    if not Player.is_fullscreen:
                        try:
                            Player.enter_fullscreen_window(window)
                            log.debug("F pressed - entered fullscreen")
                        except Exception as e:
                            log.error("Failed to enter fullscreen: %s", e)
                    else:
                        Player.exit_fullscreen_window(
                            window,
                            window["_canvas_video_"],
                            lambda: background_mgr.show_background(Player),
                        )
                        log.debug("F pressed - exited fullscreen")

    log.info("Application exiting - cleanup in progress")


def update_time_display():
        """Refresh the playback timer and control button states."""
        try:
            has_media = False
            if Player.players:
                try:
                    state = Player.players.get_state()
                    has_media = state in [0, 1, 2, 3, 4]
                except Exception:
                    has_media = Player.players.is_playing()

            if has_media:
                time_info = playback_controls.get_time_info()
                current_str = playback_controls.format_time(time_info['current'])
                total_str = playback_controls.format_time(time_info['total'])
                rate = time_info.get('rate', 1.0)
                if abs(rate - 1.0) > 0.01:
                    time_display = f"{current_str} / {total_str} ({rate}x)"
                else:
                    time_display = f"{current_str} / {total_str}"
                window["_time_display_"].update(time_display)
                try:
                    if Player.players.get_state() == 4:
                        window["_pause_play_"].update("▶ Play")
                    else:
                        window["_pause_play_"].update("⏸ Pause")
                except Exception:
                    window["_pause_play_"].update("⏸ Pause")
                playback_controls.update_controls_state(True)
            else:
                window["_time_display_"].update("00:00 / 00:00")
                window["_pause_play_"].update("⏸ Pause")
                playback_controls.update_controls_state(False)
        except Exception as exc:
            log.debug("Failed to update time display: %s", exc)


if __name__ == "__main__":
    # Add the src directory to sys.path
    directory = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(directory, "core")
    sys.path.insert(0, src_path)

    asyncio.run(main())

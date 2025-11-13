"""
Event handlers for the main application.

This module contains event handling logic for menu actions, window events,
and user interactions.
"""
import logging
import os
from pathlib import Path

from __version__ import __version__, APP_NAME, APP_AUTHOR
from ui.layout import sg
from core.models import Data
from ui.help_window import show_help_window
from ui.settings_window import _show_vlc_settings_window
from ui.ui_settings_window import _show_ui_settings_window
from ui.logging_settings_window import _show_logging_settings_window
from core.logger_setup import LOGS_DIR

# Module logger  
log = logging.getLogger(__name__)


class EventHandler:
    """
    Handles all application events including menu actions and user interactions.
    
    Attributes:
        last_channel_idx: Index of last selected channel for context menu
    """
    
    def __init__(self):
        """Initialize the event handler."""
        log.debug("Initializing EventHandler")
        self.last_channel_idx = None

    def handle_channel_table_click(self, event: tuple) -> None:
        """
        Handle channel table click to track selected row.
        
        Args:
            event: Click event tuple containing row information
        """
        try:
            if isinstance(event, tuple) and len(event) >= 3:
                if event[0] == "_iptv_content_" and "+CLICKED+" in str(event):
                    clicked_row = int(event[2][0]) if isinstance(event[2], tuple) else None
                    if clicked_row is not None and clicked_row >= 0:
                        self.last_channel_idx = clicked_row
                        log.debug("Channel table clicked: row=%d", clicked_row)
        except Exception as e:
            log.error("Failed to handle channel table click: %s", e)

    def handle_about(self) -> None:
        """Display about dialog."""
        log.info("Showing About dialog")
        try:
            sg.popup(f"{APP_NAME} & {APP_AUTHOR}", f"v{__version__} Released on 22.09.2025",
                    no_titlebar=True, grab_anywhere=True, keep_on_top=True)
        except Exception as e:
            log.error("Failed to show About dialog: %s", e)

    def handle_help(self) -> None:
        """Display help window."""
        log.info("Showing Help window")
        try:
            show_help_window()
        except Exception as e:
            log.error("Failed to show Help window: %s", e)

    def handle_open_logs_folder(self) -> None:
        """Open the logs folder in file explorer."""
        log.info("Opening logs folder: %s", LOGS_DIR)
        try:
            os.startfile(str(LOGS_DIR))
        except Exception as e:
            log.error("Failed to open logs folder: %s", e)
            sg.popup_error(f"Cannot open logs folder: {LOGS_DIR}")

    def handle_logging_settings(self, logging_settings) -> None:
        """Show logging settings window."""
        log.info("Opening logging settings")
        try:
            changed = _show_logging_settings_window(logging_settings)
            if changed:
                log.info("Logging settings changed")
                sg.popup("Logging settings saved. Please restart to apply.", keep_on_top=True)
        except Exception as e:
            log.error("Failed to handle logging settings: %s", e)

    def handle_view_current_log(self) -> None:
        """Display current log file in a viewer window."""
        log.info("Opening log viewer")
        try:
            log_path = LOGS_DIR / 'app.log'
            viewer_layout = [
                [sg.Multiline(key='_log_text_', size=(100, 25), autoscroll=True,
                             disabled=True, font=('Consolas', 9), expand_x=True,
                             expand_y=True)],
                [sg.Button('Refresh'), sg.Button('Close')]
            ]
            from core.config import ICON
            viewer = sg.Window('Current Log', viewer_layout, icon=ICON,
                             finalize=True, keep_on_top=True, resizable=True)
            
            def _load_tail():
                """Load last 500 lines of log file."""
                try:
                    if log_path.exists():
                        with open(log_path, 'rb') as f:
                            f.seek(0, os.SEEK_END)
                            size = f.tell()
                            cap = 1_000_000  # 1MB cap
                            start = max(0, size - cap)
                            f.seek(start)
                            data = f.read().decode('utf-8', errors='ignore')
                        lines = data.splitlines()[-500:]
                        viewer['_log_text_'].update("\n".join(lines))
                        log.debug("Loaded %d log lines", len(lines))
                except Exception as ex:
                    error_msg = f"Error reading log: {ex}"
                    viewer['_log_text_'].update(error_msg)
                    log.error(error_msg)
            
            _load_tail()
            
            while True:
                ve, vv = viewer.read(timeout=2000)
                if ve in (sg.WIN_CLOSED, 'Close'):
                    break
                if ve in (sg.TIMEOUT_KEY, 'Refresh'):
                    _load_tail()
            
            viewer.close()
            log.debug("Log viewer closed")
            
        except Exception as e:
            log.error("Failed to open log viewer: %s", e, exc_info=True)
            sg.popup_error(f"Failed to open log viewer: {e}")

    def handle_open_playlist(self, window_manager) -> None:
        """Open and load a playlist file."""
        log.info("Opening playlist file dialog")
        try:
            from core.models import IPTVFileType
            path = sg.popup_get_file(
                message="Select playlist",
                default_path=os.getcwd(),
                file_types=IPTVFileType.all_types(),
                no_window=True
            )
            
            if path:
                log.info("Playlist selected: %s", path)
                from core.app import get_categories, _rows
                from core.settings import _remember_last_m3u
                Data.filename = path
                Data.categories = get_categories()
                
                if window_manager.category_visible and window_manager.category_window:
                    window_manager.category_window["_table_countries_"].update(
                        _rows(Data.categories)
                    )
                    log.debug("Category window updated with new playlist")
                
                _remember_last_m3u(Data.filename)
                log.info("Playlist loaded successfully: %d categories", 
                        len(Data.categories or []))
            else:
                log.debug("No playlist selected")
                
        except Exception as e:
            log.error("Failed to handle playlist open: %s", e, exc_info=True)

    async def handle_custom_list(self, values: dict):
        """Create a custom playlist from selected categories."""
        log.info("Opening custom list generator")
        
        if not Data.filename:
            log.warning("No playlist loaded for custom list generation")
            sg.popup_error("Please load a playlist first", keep_on_top=True)
            return
        
        try:
            from core.config import ICON
            from core.app import generate_list
            import asyncio
            
            generate_window = sg.Window(
                "Custom List Generator",
                layout=[
                    [sg.SaveAs("Save as", target="_file_", key="_file_to_be_generated_"),
                     sg.I(key="_file_", disabled=True),
                     sg.B("Create", key="_create_list_")]
                ],
                icon=ICON,
            ).finalize()
            
            while True:
                generate_event, generate_values = generate_window.read()
                
                if generate_event in (sg.WIN_CLOSED, "Exit"):
                    log.debug("Custom list generation cancelled")
                    break
                
                if Path(generate_values["_file_to_be_generated_"]).name and generate_event == "_create_list_":
                    sel_vals = {"_table_countries_": Data.selected_category_indices or []}
                    
                    if not sel_vals["_table_countries_"]:
                        log.warning("No category selected for custom list")
                        sg.popup_error("No category selected. Select one from the Categories window first.",
                                     keep_on_top=True)
                        continue
                    
                    output_file = generate_values["_file_to_be_generated_"]
                    log.info("Generating custom list: %s", output_file)
                    
                    await asyncio.ensure_future(
                        generate_list(
                            values=sel_vals,
                            categories=Data.categories,
                            new_file=output_file,
                            do_file=True
                        ),
                        loop=asyncio.get_event_loop()
                    )
                    
                    sg.popup_ok(f"Custom list {output_file} has been created",
                              no_titlebar=True)
                    log.info("Custom list created successfully")
            
            generate_window.close()
            
        except Exception as e:
            log.error("Failed to handle custom list generation: %s", e, exc_info=True)

    def handle_add_account(self, window_manager):
        """Add a new Xtream account."""
        log.info("Adding Xtream account")
        try:
            from core.account import _add_account_window
            from core.settings import _remember_last_account, _load_xtream_into_app
            
            acc = _add_account_window()
            
            if acc:
                log.info("Account added: %s", acc.get("name") or acc["username"])
                Data.xtream_account = acc
                _remember_last_account(acc.get("name") or acc["username"])
                
                _load_xtream_into_app(
                    window_manager.main_window,
                    acc["base"],
                    acc["username"],
                    acc["password"],
                    window_manager.category_window if window_manager.category_visible else None
                )
                
                sg.popup("Xtream list loaded.", keep_on_top=True)
            else:
                log.debug("Account addition cancelled")
                
        except Exception as e:
            log.error("Failed to add account: %s", e, exc_info=True)

    def handle_choose_account(self, window_manager):
        """Choose and switch to an existing Xtream account."""
        log.info("Choosing Xtream account")
        try:
            from core.account import _choose_account_window
            from core.settings import _remember_last_account, _load_xtream_into_app
            
            choice = _choose_account_window()
            
            if choice and choice[0] == "use":
                _, name, acc = choice
                log.info("Switching to account: %s", name)
                
                Data.xtream_account = {"name": name, **acc}
                _remember_last_account(name)
                
                _load_xtream_into_app(
                    window_manager.main_window,
                    acc["base"],
                    acc["username"],
                    acc["password"],
                    window_manager.category_window if window_manager.category_visible else None
                )
                
                sg.popup(f"Using account: {name}", keep_on_top=True)
            else:
                log.debug("Account selection cancelled")
                
        except Exception as e:
            log.error("Failed to choose account: %s", e, exc_info=True)

    def handle_reload_account(self, window_manager):
        """Reload current Xtream account."""
        log.info("Reloading current Xtream account")
        try:
            from core.settings import _load_xtream_into_app
            
            acc = Data.xtream_account
            
            if acc:
                log.info("Reloading account: %s", acc.get("name") or acc.get("username"))
                _load_xtream_into_app(
                    window_manager.main_window,
                    acc["base"],
                    acc["username"],
                    acc["password"],
                    window_manager.category_window if window_manager.category_visible else None
                )
            else:
                log.warning("No current Xtream account to reload")
                sg.popup_error("No current Xtream account. Use Xtream → Add Account first.",
                             keep_on_top=True)
                
        except Exception as e:
            log.error("Failed to reload account: %s", e, exc_info=True)

    def handle_ui_settings(self, ui_settings) -> bool:
        """Show UI settings window. Returns True if app should exit for restart."""
        log.info("Opening UI settings")
        try:
            if _show_ui_settings_window(ui_settings):
                log.info("UI settings changed, restart required")
                sg.popup(
                    "UI settings have been saved.\n\n"
                    "The application will now close.\n"
                    "Please restart to see the changes.",
                    title="Restart Required",
                    keep_on_top=True
                )
                return True
            return False
        except Exception as e:
            log.error("Failed to handle UI settings: %s", e, exc_info=True)
            return False

    def handle_vlc_settings(self, vlc_settings) -> None:
        """Show VLC settings window."""
        log.info("Opening VLC settings")
        try:
            _show_vlc_settings_window(vlc_settings)
        except Exception as e:
            log.error("Failed to handle VLC settings: %s", e, exc_info=True)

    def handle_ip_info(self) -> None:
        """Display IP address information window."""
        log.info("Opening IP info window")
        try:
            import requests
            from core.models import IpModel
            
            ipinfo_layout = [
                [sg.Col([
                    [sg.T(key="_ip_address_info_",
                         text=IpModel(**Data.ip_info).get_results)]
                ], expand_y=True, expand_x=True)]
            ]
            
            ipinfo_window = sg.Window("IP Address Info", ipinfo_layout,
                                     icon="media/ico.ico", size=(300, 150))
            
            while True:
                ipinfo_event, ipinfo_values = ipinfo_window.read()
                
                if ipinfo_event in (sg.WIN_CLOSED, "Exit"):
                    break
                
                try:
                    Data.ip_info = requests.get("http://ipinfo.io/json").json()
                    ipinfo_window["_ip_address_info_"].Update(
                        IpModel(**Data.ip_info).get_results
                    )
                    log.debug("IP info updated")
                except ConnectionError as e:
                    log.warning("Failed to fetch IP info: %s", e)
                    continue
            
            ipinfo_window.close()
            log.debug("IP info window closed")
            
        except Exception as e:
            log.error("Failed to handle IP info: %s", e, exc_info=True)

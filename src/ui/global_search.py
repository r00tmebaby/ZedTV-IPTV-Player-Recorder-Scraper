"""
Global Search Window - Search across all channels/videos regardless of category.

Provides instant search filtering across the entire content catalog.
"""

import logging
from typing import Callable, List

from . import PySimpleGUI as sg
from core.config import ICON

log = logging.getLogger(__name__)


class GlobalSearch:
    """
    Global search window for searching across all channels/videos.

    Features:
    - Case-insensitive search
    - Starts-with matching approach
    - Instant filtering as you type
    - Double-click or Enter to play
    """

    def __init__(self, all_channels: List[dict], play_callback: Callable):
        """
        Initialize global search window.

        Args:
            all_channels: List of all channel dictionaries with 'title' and other metadata
            play_callback: Callback function to play selected channel
        """
        self.all_channels = all_channels
        self.play_callback = play_callback
        self.filtered_channels = []
        self.window = None

        # Precompute lowercase, cleaned names for fast filtering
        self._search_index: List[tuple[str, dict]] = []
        for ch in all_channels:
            title = ch.get("title", "")
            # Clean common prefixes for search purposes
            cleaned = title
            for prefix in ("[VOD]", "VOD -", "VOD:", "EU -", "EN -", "UK -", "US -"):
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            self._search_index.append((cleaned.casefold(), ch))

        log.info("GlobalSearch initialized with %d channels", len(all_channels))

    def show(self) -> None:
        """Show the global search window."""
        if self.window:
            self.window.bring_to_front()
            return

        # Initial data - show all channels
        self.filtered_channels = self.all_channels.copy()

        layout = [
            [sg.Text("Global Search", font=("Arial", 14, "bold"))],
            [sg.Text("Search across all channels and videos:")],
            [
                sg.Input(
                    key="_global_search_input_",
                    size=(60, 1),
                    enable_events=True,
                    focus=True,
                    font=("Arial", 11)
                ),
                sg.Button("Clear", key="_clear_search_", size=(8, 1))
            ],
            [sg.Text("", size=(60, 1), key="_result_count_", font=("Arial", 9))],
            [
                sg.Table(
                    values=self._format_table_data(self.filtered_channels),
                    headings=["Title", "Category", "Rating", "Year"],
                    key="_search_results_",
                    justification="left",
                    auto_size_columns=False,
                    col_widths=[40, 20, 8, 6],
                    num_rows=20,
                    font=("Arial", 10),
                    enable_events=True,
                    expand_x=True,
                    expand_y=True,
                    vertical_scroll_only=True,
                    select_mode=sg.TABLE_SELECT_MODE_BROWSE
                )
            ],
            [
                sg.Text("Tip: Double-click a row or press Enter to play", font=("Arial", 9, "italic")),
                sg.Push(),
                sg.Button("Close", key="_close_", size=(10, 1))
            ]
        ]

        self.window = sg.Window(
            "Global Search - ZedTV",
            layout,
            size=(900, 600),
            resizable=True,
            finalize=True,
            keep_on_top=False,
            modal=False,
            icon=ICON,
        )

        # Bind double-click on table to _PLAY_ event and Enter key to _PLAY_
        try:
            self.window["_search_results_"].bind("<Double-Button-1>", "_PLAY_")
            self.window.bind("<Return>", "_PLAY_")
        except Exception:
            pass

        # Update result count
        self._update_result_count()

        log.info("Global search window opened")
        self._run_event_loop()

    def _format_table_data(self, channels: List[dict]) -> List[List[str]]:
        """
        Format channel data for table display.

        Args:
            channels: List of channel dictionaries

        Returns:
            List of rows for table
        """
        rows = []
        for channel in channels:
            title = channel.get("title", "Unknown")
            category = channel.get("category", "")
            rating = channel.get("rating", "")
            year = channel.get("year", "")

            rows.append([title, category, rating, year])

        return rows

    def _update_result_count(self) -> None:
        """Update the result count display."""
        count = len(self.filtered_channels)
        total = len(self.all_channels)

        if count == total:
            text = f"Showing all {total} channels"
        else:
            text = f"Found {count} of {total} channels"

        if self.window:
            self.window["_result_count_"].update(text)

    def _filter_channels(self, search_text: str) -> None:
        """
        Filter channels based on search text (case-insensitive, starts-with).

        Args:
            search_text: Search query string
        """
        query = search_text.strip().casefold()
        if not query:
            # Show all channels if search is empty (from original list)
            self.filtered_channels = self.all_channels.copy()
        else:
            # Use precomputed index for fast startswith matching on cleaned names
            self.filtered_channels = [ch for name, ch in self._search_index if name.startswith(query)]

        # Minimize redraw cost by updating only if window exists
        if self.window:
            self.window["_search_results_"].update(values=self._format_table_data(self.filtered_channels))
            self._update_result_count()

        log.debug("Filtered to %d channels with query: '%s'", len(self.filtered_channels), query)

    def _play_selected_channel(self) -> None:
        """Play the selected channel."""
        try:
            selected_rows = self.window["_search_results_"].SelectedRows

            if not selected_rows:
                log.debug("No channel selected")
                return

            row_index = selected_rows[0]

            if 0 <= row_index < len(self.filtered_channels):
                channel = self.filtered_channels[row_index]
                log.info("Playing channel from search: %s", channel.get("title", "Unknown"))

                # Call play callback FIRST (schedules async task)
                try:
                    self.play_callback(channel)
                    log.debug("Play callback invoked successfully")
                except Exception as e:
                    log.error("Play callback failed: %s", e, exc_info=True)
                    sg.popup_error(f"Failed to start playback: {e}", title="Error", keep_on_top=True)

                # THEN close search window (allows event loop to process the task)
                self.close()
            else:
                log.warning("Invalid row index: %d", row_index)

        except Exception as e:
            log.error("Failed to play selected channel: %s", e, exc_info=True)
            sg.popup_error(f"Failed to play channel: {e}", title="Error", keep_on_top=True)

    def _run_event_loop(self) -> None:
        """Run the event loop for the search window with light debounce."""
        last_query = ""
        while True:
            if self.window is None:
                break
            event, values = self.window.read(timeout=120)

            if event in (sg.WIN_CLOSED, "_close_"):
                break

            elif event == "_global_search_input_":
                text = values.get("_global_search_input_", "")
                if text != last_query:
                    last_query = text
                    self._filter_channels(text)

            elif event == "_clear_search_":
                # Clear search and show all
                self.window["_global_search_input_"].update("")
                last_query = ""
                self._filter_channels("")

            elif event == "_PLAY_":
                # Double-click or Enter: play selected channel and exit
                self._play_selected_channel()
                break

        self.close()

    def close(self) -> None:
        """Close the search window."""
        if self.window:
            try:
                self.window.close()
                log.info("Global search window closed")
            except Exception as e:
                log.error("Error closing search window: %s", e)
            finally:
                self.window = None


def show_global_search(all_channels: List[dict], play_callback: Callable) -> None:
    """
    Show global search window.

    Args:
        all_channels: List of all channel dictionaries
        play_callback: Callback to play selected channel
    """
    search = GlobalSearch(all_channels, play_callback)
    search.show()

"""
Channel list manager with ACTUAL thumbnail images displayed inline
Creates visual rows with sg.Image() widgets showing real thumbnails
"""

from ui import PySimpleGUI as sg
from pathlib import Path
from typing import List, Dict
import threading

from .thumbnails import get_thumbnail_path


def create_channel_row_with_thumbnail(idx, title, rating, year, logo_url, ui_settings):
    """
    Create a single channel row with ACTUAL thumbnail image displayed.
    Returns a list that can be added to a Column.
    """
    show_thumbnails = ui_settings.settings.get("show_thumbnails", True)
    thumbnail_size = ui_settings.settings.get("thumbnail_size", 100)
    table_font = ui_settings.get_font("table")

    row_elements = []

    # Add thumbnail image if enabled and URL exists
    if show_thumbnails and logo_url:
        # Try to get thumbnail
        thumb_path = get_thumbnail_path(logo_url, thumbnail_size)

        if thumb_path and Path(thumb_path).exists():
            # REAL IMAGE!
            row_elements.append(
                sg.Image(
                    filename=thumb_path,
                    size=(thumbnail_size, thumbnail_size),
                    key=f"_thumb_{idx}_",
                    enable_events=True,
                    pad=(5, 5),
                )
            )
        else:
            # Placeholder while loading
            row_elements.append(
                sg.Text(
                    "⏳",
                    font=(table_font[0], thumbnail_size // 3),
                    size=(int(thumbnail_size/10), int(thumbnail_size/20)),
                    justification='center',
                    key=f"_thumb_placeholder_{idx}_",
                    pad=(5, 5),
                )
            )
    else:
        # No thumbnail - show icon
        row_elements.append(
            sg.Text(
                "📺",
                font=table_font,
                size=(3, 2),
                justification='center',
                pad=(5, 5),
            )
        )

    # Build info text
    info = f"{title}"
    if rating:
        info += f" ⭐{rating}"
    if year:
        info += f" 📅{year}"

    row_elements.append(
        sg.Text(
            info,
            font=table_font,
            size=(50, 2 if show_thumbnails else 1),
            key=f"_channel_text_{idx}_",
            enable_events=True,
            pad=(5, 5),
        )
    )

    # Wrap in a frame for visual grouping
    return [
        sg.Frame(
            "",
            [row_elements],
            key=f"_channel_row_{idx}_",
            relief=sg.RELIEF_RIDGE,
            border_width=1,
            expand_x=True,
            pad=(2, 2),
        )
    ]


def build_channel_rows(channel_data, ui_settings):
    """
    Build all channel rows with real thumbnails.
    channel_data: List of [icon, title, rating, year, logo_url]
    Returns: List of rows for Column widget
    """
    rows = []

    if not channel_data:
        return [[sg.Text("No channels loaded", font=ui_settings.get_font("table"))]]

    for idx, row in enumerate(channel_data):
        if len(row) >= 5:
            icon, title, rating, year, logo_url = row
        else:
            icon, title, rating, year = row[0], row[1], row[2], row[3]
            logo_url = ""

        channel_row = create_channel_row_with_thumbnail(
            idx, title, rating, year, logo_url, ui_settings
        )
        rows.extend(channel_row)

    return rows


def update_channel_column(window, channel_data, ui_settings):
    """
    Update the channel column with new rows containing real thumbnails.
    This rebuilds the entire channel list with Image widgets.
    """
    # Build new rows with thumbnails
    new_rows = build_channel_rows(channel_data, ui_settings)

    # Update the scrollable column
    try:
        window["_channel_scroll_col_"].update(new_rows)
    except Exception as e:
        print(f"Error updating channel column: {e}")


class ChannelListManager:
    """Manages channel data and provides access by index."""

    def __init__(self):
        self.channels = []
        self.selected_index = None

    def load_channels(self, channel_data):
        """
        Load channel data.
        channel_data: List of [icon, title, rating, year, logo_url]
        """
        self.channels = []

        for idx, row in enumerate(channel_data):
            if len(row) >= 5:
                icon, title, rating, year, logo_url = row
            else:
                icon, title, rating, year = row[0], row[1], row[2], row[3]
                logo_url = ""

            self.channels.append({
                'idx': idx,
                'title': title,
                'rating': rating,
                'year': year,
                'logo_url': logo_url,
            })

    def get_channel(self, idx):
        """Get channel data by index."""
        if 0 <= idx < len(self.channels):
            return self.channels[idx]
        return None

    def get_count(self):
        """Get number of channels."""
        return len(self.channels)


# Wrapper function for compatibility
def update_channel_list(window, channel_data, ui_settings, channel_manager):
    """
    Update channel list with real thumbnails displayed inline.
    """
    # Load data into manager
    channel_manager.load_channels(channel_data)

    # Update the visual column with thumbnail images
    update_channel_column(window, channel_data, ui_settings)



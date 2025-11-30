"""
Channel list with thumbnails displayed INLINE using PySimpleGUI Image elements
"""

from pathlib import Path

from ui_settings import UISettings

from ui import PySimpleGUI as sg

from .thumbnails import get_thumbnail_path


def create_channel_list_with_thumbnails(
    ui_settings: UISettings, initial_data=None
):
    """
    Create a channel list that displays actual thumbnail images.
    Uses a scrollable Column instead of Table.
    """
    show_thumbnails = ui_settings.settings.get("show_thumbnails", True)
    thumbnail_size = ui_settings.settings.get("thumbnail_size", 100)
    table_font = ui_settings.get_font("table")

    # Initial empty state
    if not initial_data:
        initial_data = []

    # Create column layout with thumbnails
    channel_rows = []
    for idx, (icon, title, rating, year, logo_url) in enumerate(initial_data):
        row = create_channel_row(
            idx,
            icon,
            title,
            rating,
            year,
            logo_url,
            show_thumbnails,
            thumbnail_size,
            table_font,
        )
        channel_rows.append(row)

    if not channel_rows:
        channel_rows = [[sg.Text("No channels loaded", font=table_font)]]

    # Scrollable column
    channel_column = sg.Column(
        channel_rows,
        key="_channel_list_col_",
        scrollable=True,
        vertical_scroll_only=True,
        expand_x=True,
        expand_y=True,
        size=(600, 400),
    )

    return channel_column


def create_channel_row(
    idx,
    icon,
    title,
    rating,
    year,
    logo_url,
    show_thumbnails,
    thumbnail_size,
    font,
):
    """Create a single channel row with thumbnail and info."""

    elements = []

    # Thumbnail or placeholder
    if show_thumbnails and logo_url:
        # Try to get thumbnail
        thumb_path = get_thumbnail_path(logo_url, thumbnail_size)
        if thumb_path and Path(thumb_path).exists():
            elements.append(
                sg.Image(
                    filename=thumb_path,
                    size=(thumbnail_size, thumbnail_size),
                    key=f"_thumb_{idx}_",
                )
            )
        else:
            # Placeholder if thumbnail fails
            elements.append(
                sg.Text(
                    "🖼️",
                    font=(font[0], thumbnail_size // 4),
                    size=(3, 1),
                    justification="center",
                )
            )
    else:
        # No thumbnail - show icon
        elements.append(
            sg.Text(
                icon,
                font=font,
                size=(3, 1),
                justification="center",
            )
        )

    # Channel info
    info_text = f"{title}"
    if rating:
        info_text += f" ⭐{rating}"
    if year:
        info_text += f" 📅{year}"

    elements.append(
        sg.Text(
            info_text,
            font=font,
            size=(50, 1),
            key=f"_channel_text_{idx}_",
            enable_events=True,
            relief=sg.RELIEF_FLAT,
            background_color=None,
        )
    )

    return [
        sg.Frame(
            "",
            [[*elements]],
            key=f"_channel_row_{idx}_",
            relief=sg.RELIEF_RIDGE,
            border_width=1,
            expand_x=True,
        )
    ]


def update_channel_list(window, channel_data, ui_settings):
    """
    Update the channel list with new data.
    Downloads thumbnails in background.
    """
    show_thumbnails = ui_settings.settings.get("show_thumbnails", True)
    thumbnail_size = ui_settings.settings.get("thumbnail_size", 100)
    table_font = ui_settings.get_font("table")

    # Clear existing column
    # Note: This is a limitation - we'd need to rebuild the window
    # For now, return the new layout
    channel_rows = []

    for idx, item in enumerate(channel_data):
        if len(item) >= 5:
            icon, title, rating, year, logo_url = (
                item[0],
                item[1],
                item[2],
                item[3],
                item[4] if len(item) > 4 else "",
            )
        else:
            icon, title, rating, year = item[0], item[1], item[2], item[3]
            logo_url = ""

        row = create_channel_row(
            idx,
            icon,
            title,
            rating,
            year,
            logo_url,
            show_thumbnails,
            thumbnail_size,
            table_font,
        )
        channel_rows.append(row)

    if not channel_rows:
        channel_rows = [[sg.Text("No channels", font=table_font)]]

    return channel_rows

from core.app import _rows
from core.models import Data

from . import PySimpleGUI as sg

"""UI layout builders (category panel, channel panel, main window).
Separated from main logic to keep window construction modular.
"""

menu_def = [
    ["&File", ["&Open", "&Custom List", "&Exit"]],
    ["&Xtream", ["&Add Account", "&Accounts...", "&Reload from Current"]],
    ["&View", ["Show &Categories", "Show C&hannels", "&Restore Layout"]],
    [
        "&Settings",
        ["&UI Settings", "&VLC Settings", "&Logging Settings", "&IP Info"],
    ],
    ["&Logs", ["&View Current Log", "Open &Logs Folder"]],
    ["&Help", ["&How to Use", "&About"]],
]


def build_category_panel_layout(table_font):
    """Build a fresh category panel layout (avoids element reuse)."""
    return [
        [
            sg.I(
                key="_cat_search_",
                expand_x=True,
                enable_events=True,
                size=(18, 1),
            )
        ],
        [
            sg.Table(
                values=_rows(Data.categories),
                headings=["Category"],
                key="_table_countries_",
                change_submits=True,
                expand_y=True,
                expand_x=True,
                justification="l",
                size=(15, 30),
                font=table_font,
                auto_size_columns=False,
                vertical_scroll_only=True,
            )
        ],
    ]


def build_channel_panel_layout(table_font):
    """Build a fresh channel panel layout (avoids element reuse)."""
    return [
        [
            sg.I(
                key="_ch_search_",
                expand_x=True,
                enable_events=True,
                size=(28, 1),
            )
        ],
        [
            sg.Table(
                values=[[" "]],
                headings=[
                    "Title                                                    ",
                    "Rate",
                    "Year",
                ],
                key="_iptv_content_",
                justification="l",
                expand_y=True,
                expand_x=True,
                right_click_menu=[
                    "&Menu",
                    [
                        "&Full Screen",
                        "&Record",
                        "&Play in VLC",
                        "&Send to Browser",
                        "&Stop",
                    ],
                ],
                bind_return_key=True,
                enable_click_events=True,
                size=(
                    55,
                    40,
                ),  # Increased from (45, 50) - wider and shows more rows
                font=table_font,
                auto_size_columns=False,
                vertical_scroll_only=True,
                col_widths=[
                    35,
                    6,
                    6,
                ],  # Title gets 40 chars, Rating and Year get 6 chars each
            )
        ],
    ]


def build_layout(ui_settings=None):
    """Build layout dynamically based on UI settings."""

    # Get settings
    if ui_settings:
        table_font = ui_settings.get_font("table")
    else:
        table_font = ("Arial", 10)

    # Always use horizontal layout
    # orientation = "horizontal"

    # List sizes for tables
    # list_size = (200, 300)  # (rows, height in pixels)

    # Video canvas - fixed size 857x552 (not resizable)
    video_canvas = sg.Canvas(
        key="_canvas_video_",
        background_color="black",
        expand_x=True,
        expand_y=True,
        size=(690, 390),  # Fixed size
        pad=(0, 0),
    )

    # Category panel with search box included
    category_panel_layout = [
        [
            sg.I(
                key="_cat_search_",
                expand_x=True,
                enable_events=True,
                size=(18, 1),
            ),
        ],
        [
            sg.Table(
                values=_rows(Data.categories),
                headings=["Category"],
                key="_table_countries_",
                change_submits=True,
                expand_y=True,
                expand_x=True,
                justification="l",
                size=(15, 30),  # rows, lines
                font=table_font,
                auto_size_columns=False,
                vertical_scroll_only=True,
            )
        ],
    ]

    # Channel panel with search box included
    channel_panel_layout = [
        [
            sg.I(
                key="_ch_search_",
                expand_x=True,
                enable_events=True,
                size=(28, 1),
            ),
        ],
        [
            sg.Table(
                values=[[" "]],
                headings=[
                    "Title                        ",
                    "Rating",
                    "Year",
                ],
                key="_iptv_content_",
                justification="l",
                expand_y=True,
                expand_x=True,
                right_click_menu=[
                    "&Menu",
                    [
                        "&Full Screen",
                        "&Record",
                        "&Play in VLC",
                        "&Send to Browser",
                        "&Stop",
                    ],
                ],
                bind_return_key=True,
                enable_click_events=True,
                size=(20, 30),  # rows, lines
                font=table_font,
                auto_size_columns=False,
                vertical_scroll_only=True,
            ),
        ],
    ]

    # Build main layout - ONLY video canvas (categories and channels are separate windows)
    layout = [
        [
            sg.Col(
                [
                    [sg.Menu(menu_def, pad=(200, 1))],
                    [
                        sg.Col(
                            [[video_canvas]],
                            expand_x=True,
                            expand_y=True,
                        ),
                    ],
                ],
                expand_x=True,
                expand_y=True,
            )
        ]
    ]

    return (
        layout,
        category_panel_layout,
        channel_panel_layout,
    )  # Return layouts for separate windows


# Default layout for backward compatibility
layout = build_layout()

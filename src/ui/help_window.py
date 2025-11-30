"""Rich help / documentation window for the application.
Provides a left-hand section list (acts like an accordion selector) and a right-hand
content area. Selecting a section updates the explanation pane.
Includes a quick search box to filter sections.
"""

from __future__ import annotations

import logging

from core.config import ICON

from . import PySimpleGUI as sg

log = logging.getLogger("zedtv.help")

# Help content definitions: (section id, title, body)
_SECTIONS = [
    (
        "getting_started",
        "Getting Started",
        "Open an M3U playlist via File -> Open or load an Xtream account. "
        "Categories and channels will then populate in their panels.",
    ),
    (
        "playlist_management",
        "Playlist Management",
        "Use Custom List to export only selected categories to a new playlist. "
        "Categories can be filtered live via the search field.",
    ),
    (
        "xtream_accounts",
        "Xtream Accounts",
        "Add accounts from Xtream menu. Switch accounts via Accounts... and Reload to refresh streams. "
        "Generated M3U is parsed automatically.",
    ),
    (
        "playback_controls",
        "Playback & Controls",
        "Double‑click a channel or press Enter to start playback. "
        "Right‑click channel list for Full Screen, Record, Play in VLC, Stop. ESC stops playback.",
    ),
    (
        "recording",
        "Recording",
        "Record saves an MP4 with timestamp and cleaned channel title to the records folder. "
        "During recording the stream is also displayed.",
    ),
    (
        "search_filter",
        "Search & Filtering",
        "Typing in the search boxes filters categories or channels instantly. "
        "Filtering channels preserves the underlying master list until cleared.",
    ),
    (
        "logging_troubleshooting",
        "Logging & Troubleshooting",
        "Adjust logging in Settings -> Logging Settings. View live logs via Help -> View Current Log. "
        "Send app.log when reporting issues.",
    ),
    (
        "keyboard_shortcuts",
        "Keyboard Shortcuts",
        "F: Toggle fullscreen mode. ESC: Exit fullscreen (if in fullscreen) or stop playback (if not in fullscreen).",
    ),
    (
        "known_limitations",
        "Known Limitations",
        "Some malformed M3U entries lacking URLs are skipped. "
        "Certain exotic stream protocols may require external VLC playback.",
    ),
    (
        "faq",
        "FAQ",
        "Q: Why is a category empty?\nA: Playlist may not contain streams in that category or "
        "attributes differ; check logs.\n\n"
        "Q: Recording file path?\nA: records/<timestamp - channel>.mp4\n\n"
        "Q: How do I rotate logs sooner?\nA: Lower max size or backup count in Logging Settings.",
    ),
]

_SECTION_MAP = {sid: (title, body) for sid, title, body in _SECTIONS}


def _filter_sections(query: str):
    q = (query or "").strip().lower()
    if not q:
        return _SECTIONS
    return [s for s in _SECTIONS if q in s[1].lower() or q in s[2].lower()]


def show_help_window():
    log.debug("Opening help window")
    sections = _SECTIONS
    left_col = [
        [
            sg.Text(
                "Help Topics",
                font=("Arial", 14, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Input(
                key="_help_search_",
                enable_events=True,
                size=(28, 1),
                tooltip="Type to filter help sections",
                pad=((5, 5), (5, 10)),
            )
        ],
        [
            sg.Listbox(
                values=[s[1] for s in sections],
                key="_help_list_",
                size=(28, 25),
                enable_events=True,
                select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,
                pad=((5, 5), (5, 10)),
            )
        ],
        [sg.Button("Close", size=(10, 1), pad=((5, 5), (5, 10)))],
    ]
    right_col = [
        [
            sg.Text(
                "Details", font=("Arial", 14, "bold"), pad=((5, 5), (10, 10))
            )
        ],
        [
            sg.Multiline(
                "Select a section on the left.",
                key="_help_body_",
                size=(70, 27),
                disabled=True,
                autoscroll=True,
                font=("Consolas", 10),
                pad=((5, 5), (5, 10)),
            )
        ],
    ]
    layout = [
        [
            sg.Column(left_col, pad=(10, 10), vertical_alignment="top"),
            sg.VerticalSeparator(pad=((5, 5), (10, 10))),
            sg.Column(right_col, pad=(10, 10), vertical_alignment="top"),
        ]
    ]
    win = sg.Window(
        "Help Contents",
        layout,
        icon=ICON,
        modal=True,
        finalize=True,
        resizable=True,
    )

    def _update_list(q=""):
        filtered = _filter_sections(q)
        win["_help_list_"].update(values=[s[1] for s in filtered])
        win["_help_body_"].update(
            "Select a section on the left." if not filtered else ""
        )
        win.metadata = {"filtered": filtered}

    _update_list()

    while True:
        ev, vals = win.read()
        if ev in (sg.WIN_CLOSED, "Close"):
            break
        if ev == "_help_search_":
            _update_list(vals.get("_help_search_"))
        if ev == "_help_list_":
            try:
                filtered = win.metadata.get("filtered", _SECTIONS)
                sel_title = vals.get("_help_list_")
                if sel_title:
                    # find section tuple
                    for sid, title, body in filtered:
                        if title == sel_title[0]:
                            win["_help_body_"].update(body)
                            log.debug("Help section selected: %s", sid)
                            break
            except Exception as e:
                log.warning("Failed updating help body: %s", e)
    win.close()
    log.debug("Help window closed")

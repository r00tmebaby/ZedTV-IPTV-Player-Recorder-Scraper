"""Dialogs that point the user at the project's GitHub page.

The star request is shown on the first start and can be postponed or turned
off. It never blocks the application.
"""

from __future__ import annotations

import logging
from typing import Optional

from __version__ import APP_AUTHOR, APP_NAME, __version__
from core.config import ICON
from core.star_prompt import (
    CHOICE_LATER,
    CHOICE_NEVER,
    CHOICE_STAR,
    ISSUES_URL,
    REPO_URL,
    StarPrompt,
    open_url,
    run_star_prompt,
)

from . import PySimpleGUI as sg

log = logging.getLogger("zedtv.star_prompt")

_STAR = "Star on GitHub"
_LATER = "Maybe later"
_NEVER = "Don't ask again"
_REPORT = "Report a problem"
_CLOSE = "Close"


def show_star_prompt() -> str:
    """Ask for a GitHub star and return one of the CHOICE_* values."""
    log.debug("Showing star prompt")
    layout = [
        [
            sg.Text(
                "Thanks for trying ZedTV",
                font=("Arial", 14, "bold"),
                pad=((15, 15), (15, 8)),
            )
        ],
        [
            sg.Text(
                "ZedTV is free and open source.\n"
                "If it is useful to you, a star on GitHub helps other "
                "people find it.",
                pad=((15, 15), (0, 6)),
            )
        ],
        [
            sg.Text(
                "It takes a few seconds and needs a GitHub account.",
                pad=((15, 15), (0, 14)),
            )
        ],
        [
            sg.Button(_STAR, size=(16, 1), pad=((15, 6), (0, 15))),
            sg.Button(_LATER, size=(13, 1), pad=((0, 6), (0, 15))),
            sg.Button(_NEVER, size=(15, 1), pad=((0, 15), (0, 15))),
        ],
    ]
    win = sg.Window(
        "Enjoying ZedTV?",
        layout,
        icon=ICON,
        modal=True,
        finalize=True,
        keep_on_top=True,
    )
    ev, _ = win.read()
    win.close()

    if ev == _STAR:
        open_url(REPO_URL)
        return CHOICE_STAR
    if ev == _NEVER:
        return CHOICE_NEVER
    return CHOICE_LATER


def maybe_show_star_prompt(prompt: Optional[StarPrompt] = None) -> None:
    """Count this launch and show the star request when one is due."""
    run_star_prompt(show_star_prompt, prompt)


def show_about_window() -> None:
    """Show the About dialog with links to the project page."""
    layout = [
        [
            sg.Text(
                f"{APP_NAME} & {APP_AUTHOR}",
                font=("Arial", 12, "bold"),
                pad=((15, 15), (15, 6)),
            )
        ],
        [
            sg.Text(
                f"v{__version__} Released on 22.09.2025",
                pad=((15, 15), (0, 14)),
            )
        ],
        [
            sg.Button(_STAR, size=(16, 1), pad=((15, 6), (0, 15))),
            sg.Button(_REPORT, size=(16, 1), pad=((0, 6), (0, 15))),
            sg.Button(_CLOSE, size=(8, 1), pad=((0, 15), (0, 15))),
        ],
    ]
    win = sg.Window(
        "About",
        layout,
        icon=ICON,
        modal=True,
        finalize=True,
        keep_on_top=True,
    )
    while True:
        ev, _ = win.read()
        if ev in (sg.WIN_CLOSED, _CLOSE):
            break
        if ev == _STAR:
            open_url(REPO_URL)
            # Someone who stars from here should not be asked again at start-up.
            StarPrompt().record_choice(CHOICE_STAR)
        elif ev == _REPORT:
            open_url(ISSUES_URL)
    win.close()

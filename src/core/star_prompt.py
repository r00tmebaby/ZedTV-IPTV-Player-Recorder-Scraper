"""
Decides when to ask the user for a GitHub star and remembers the answer.

The request is never a condition of using the application: every answer,
including closing the dialog, lets the user carry on.

This module holds no GUI code, so the rules can be tested without a display.
"""

from __future__ import annotations

import json
import logging
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .config import DATA_FOLDER

log = logging.getLogger("zedtv.star_prompt")

REPO_URL = "https://github.com/r00tmebaby/ZedTV-IPTV-Player-Recorder-Scraper"
ISSUES_URL = REPO_URL + "/issues"

STATE_FILE = Path(DATA_FOLDER) / "star_prompt.json"

# How many more launches to wait after "Maybe later".
REMIND_AFTER_LAUNCHES = 5

STATUS_PENDING = "pending"
STATUS_STARRED = "starred"
STATUS_DECLINED = "declined"
_STATUSES = (STATUS_PENDING, STATUS_STARRED, STATUS_DECLINED)

CHOICE_STAR = "star"
CHOICE_LATER = "later"
CHOICE_NEVER = "never"

# The first launch is number 1, so a fresh install is asked straight away.
DEFAULT_STATE: Dict[str, Any] = {
    "launch_count": 0,
    "status": STATUS_PENDING,
    "next_prompt_at": 1,
}


def _is_count(value: Any) -> bool:
    """True for a non-negative whole number (bool is not a count)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class StarPrompt:
    """Tracks launches and the user's answer to the star request."""

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = Path(state_file) if state_file else STATE_FILE
        self.state = self._load()

    def _load(self) -> Dict[str, Any]:
        """Read the saved state, falling back to defaults for anything unusable."""
        state = DEFAULT_STATE.copy()
        try:
            if self.state_file.exists():
                saved = json.loads(self.state_file.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    if _is_count(saved.get("launch_count")):
                        state["launch_count"] = saved["launch_count"]
                    if saved.get("status") in _STATUSES:
                        state["status"] = saved["status"]
                    if _is_count(saved.get("next_prompt_at")):
                        state["next_prompt_at"] = saved["next_prompt_at"]
        except Exception as e:
            log.debug("Could not read %s: %s", self.state_file, e)
        return state

    def save(self) -> None:
        """Write the state. A failure is logged and never raised."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(self.state, indent=2), encoding="utf-8"
            )
        except Exception as e:
            log.debug("Could not save %s: %s", self.state_file, e)

    def register_launch(self) -> None:
        """Count one start of the application."""
        self.state["launch_count"] += 1
        self.save()

    def is_due(self) -> bool:
        """True when the user has not answered yet and the wait is over."""
        return (
            self.state["status"] == STATUS_PENDING
            and self.state["launch_count"] >= self.state["next_prompt_at"]
        )

    def record_choice(self, choice: str) -> None:
        """
        Remember the answer.

        Anything other than a star or a refusal, such as closing the dialog,
        counts as "later" and postpones the next request.
        """
        if choice == CHOICE_STAR:
            self.state["status"] = STATUS_STARRED
        elif choice == CHOICE_NEVER:
            self.state["status"] = STATUS_DECLINED
        else:
            self.state["next_prompt_at"] = (
                self.state["launch_count"] + REMIND_AFTER_LAUNCHES
            )
        self.save()


def run_star_prompt(
    ask: Callable[[], str], prompt: Optional[StarPrompt] = None
) -> Optional[str]:
    """
    Count this launch and, when a request is due, ask and remember the answer.

    Args:
        ask: Shows the request and returns one of the CHOICE_* values.
        prompt: State to use; a new one backed by STATE_FILE when omitted.

    Returns:
        The answer, or None when the user was not asked this time.
    """
    prompt = prompt or StarPrompt()
    prompt.register_launch()
    if not prompt.is_due():
        return None
    choice = ask()
    prompt.record_choice(choice)
    log.info("Star prompt answered: %s", choice)
    return choice


def open_url(url: str) -> bool:
    """Open a page in the default browser. Returns False when that fails."""
    try:
        return bool(webbrowser.open(url))
    except Exception as e:
        log.warning("Could not open %s: %s", url, e)
        return False

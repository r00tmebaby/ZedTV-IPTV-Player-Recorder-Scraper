import json
import os
from pathlib import Path

from typing import Optional

from account import _accounts_load
from config import SETTINGS_FILE, DATA_FOLDER
from layout import sg
from models import Data
from app import get_categories, _rows, _build_m3u_from_xtream


def _settings_load() -> dict:
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _settings_save(d: dict) -> None:
    try:
        SETTINGS_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass


def _settings_set(**kwargs) -> None:
    d = _settings_load()
    for k, v in kwargs.items():
        if v is not None:
            d[k] = v
        else:
            d.pop(k, None)
    _settings_save(d)


def _load_xtream_into_app(
    window: sg.Window, base: str, username: str, password: str
):
    """Build M3U cache + rich catalog, point Data.filename"""
    text, catalog = _build_m3u_from_xtream(base, username, password)

    cache = Path(os.path.join(DATA_FOLDER, f"xtream_{username}.m3u"))
    cache.write_text(text, encoding="utf-8")
    Data.filename = str(cache)
    _remember_last_m3u(Data.filename)  # <— remember the generated M3U

    Data.xtream_catalog = catalog
    Data.categories = get_categories()
    window["_table_countries_"].update(_rows(Data.categories))


def _remember_last_account(name: str) -> None:
    _settings_set(last_choice="account", last_account=name)


def _remember_last_m3u(path: str) -> None:
    _settings_set(last_choice="m3u", last_m3u=path)


def _auto_restore_last(window: "sg.Window") -> Optional[str]:
    """
    Try to restore last session. Returns "account", "m3u" or None.
    Respects the last_choice field and gracefully falls back.
    """
    s = _settings_load()

    def _try_account() -> bool:
        accname = s.get("last_account")
        if not accname:
            return False
        accs = _accounts_load()
        acc = accs.get(accname)
        if not acc:
            return False
        try:
            Data.xtream_account = {"name": accname, **acc}
            _load_xtream_into_app(
                window, acc["base"], acc["username"], acc["password"]
            )
            return True
        except Exception:
            return False

    def _try_m3u() -> bool:
        p = s.get("last_m3u")
        if p and os.path.isfile(p):
            Data.filename = p
            Data.categories = get_categories()
            window["_table_countries_"].update(_rows(Data.categories))
            return True
        return False

    pref = s.get("last_choice")
    if pref == "account":
        if _try_account() or _try_m3u():
            return "account"
    elif pref == "m3u":
        if _try_m3u() or _try_account():
            return "m3u"
    else:
        if _try_account() or _try_m3u():
            return "account"
    return None

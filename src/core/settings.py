import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from services.xtream import _build_m3u_from_xtream
from ui.layout import sg

from .account import _accounts_load
from .config import DATA_FOLDER, SETTINGS_FILE
from .models import Data

logger = logging.getLogger("zedtv.settings")

# Constants
CACHE_TTL_MINUTES = 60  # Cache time-to-live in minutes


# Import get_categories and _rows from app (where they're defined)
def get_categories():
    """Import and call get_categories from app module to avoid circular import."""
    from .app import get_categories as _get_categories

    return _get_categories()


def _rows(xs):
    """Wrap list into rows for table display."""
    return [[x] for x in xs]


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


def _load_xtream_into_app(window: sg.Window, base: str, username: str, password: str, category_window=None):
    """Build M3U cache + rich catalog, point Data.filename.
    This now runs heavy network + parse work in a background thread while showing a progress popup.
    """
    start = time.time()

    # TTL pre-check: if recent cache exists, use it and return early
    cache = Path(os.path.join(DATA_FOLDER, f"xtream_{username}.m3u"))
    catalog_path = Path(os.path.join(DATA_FOLDER, f"xtream_{username}.catalog.json"))
    try:
        if cache.exists():
            mtime = datetime.fromtimestamp(cache.stat().st_mtime)
            if datetime.now() - mtime < timedelta(minutes=CACHE_TTL_MINUTES):
                logger.info("Using cached Xtream M3U (age < %dm)", CACHE_TTL_MINUTES)
                Data.filename = str(cache)
                if catalog_path.exists():
                    try:
                        Data.xtream_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                    except Exception:
                        Data.xtream_catalog = None
                # Parse categories from cached file
                Data.categories = get_categories()
                if category_window:
                    try:
                        category_window["_table_countries_"].update(_rows(Data.categories))
                    except Exception:
                        pass
                return
    except Exception:
        pass

    progress_win = sg.Window(
        "Loading Xtream",
        [
            [sg.Text("Contacting server...", key="_status_", size=(50, 1))],
            [sg.ProgressBar(100, orientation="h", size=(30, 15), key="_p_")],
        ],
        modal=True,
        keep_on_top=True,
        finalize=True,
        no_titlebar=False,
        grab_anywhere=True,
    )

    result_holder = {}
    done_flag = threading.Event()

    def worker():
        try:
            progress_win.write_event_value("_XTREAM_STAGE_", (5, "Fetching live categories"))
            text, catalog = _build_m3u_from_xtream(base, username, password)
            result_holder["text"] = text
            result_holder["catalog"] = catalog
            done_flag.set()
            progress_win.write_event_value("_XTREAM_DONE_", None)
        except Exception as e:
            result_holder["error"] = e
            done_flag.set()
            progress_win.write_event_value("_XTREAM_ERROR_", str(e))

    threading.Thread(target=worker, daemon=True).start()

    last_pulse = 0
    while True:
        ev, vals = progress_win.read(timeout=150)
        if ev in (sg.WIN_CLOSED, "_XTREAM_ERROR_"):
            break
        if ev == "_XTREAM_STAGE_":
            pct, msg = vals.get(ev, (0, "Working"))
            try:
                progress_win["_p_"].update(min(99, pct))
            except Exception:
                pass
            progress_win["_status_"].update(msg)
        if ev == "_XTREAM_DONE_":
            break
        # pulse bar
        if time.time() - last_pulse > 0.4:
            last_pulse = time.time()
            try:
                progress_win["_p_"].update_bar((int(last_pulse * 100) % 100))
            except Exception:
                pass
    progress_win.close()

    if "error" in result_holder:
        sg.popup_error(f"Failed to load Xtream list: {result_holder['error']}", keep_on_top=True)
        logger.error("Xtream load failed: %s", result_holder["error"])
        return

    text = result_holder.get("text", "")
    catalog = result_holder.get("catalog", {})
    if not text:
        sg.popup_error("Server returned empty playlist", keep_on_top=True)
        return

    cache = Path(os.path.join(DATA_FOLDER, f"xtream_{username}.m3u"))
    catalog_path = Path(os.path.join(DATA_FOLDER, f"xtream_{username}.catalog.json"))

    # Check TTL cache to skip fetch if recent
    try:
        if cache.exists():
            mtime = datetime.fromtimestamp(cache.stat().st_mtime)
            if datetime.now() - mtime < timedelta(minutes=CACHE_TTL_MINUTES):
                logger.info("Using cached Xtream M3U (age < %dm)", CACHE_TTL_MINUTES)
                Data.filename = str(cache)
                if catalog_path.exists():
                    try:
                        Data.xtream_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                # Parse categories from cached file
                Data.categories = get_categories()
                if category_window:
                    category_window["_table_countries_"].update(_rows(Data.categories))
                progress_win.close()
                return
    except Exception:
        pass

    try:
        cache.write_text(text, encoding="utf-8")
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed writing cache files for %s: %s", username, e)
    Data.filename = str(cache)
    _remember_last_m3u(Data.filename)
    Data.xtream_catalog = catalog

    # Delay category parsing until needed (lazy). Clear current categories first.
    Data.categories = []
    try:
        cats = get_categories()
        Data.categories = cats
    except Exception as e:
        logger.warning("Parsing categories post-load failed: %s", e)
    if category_window:
        try:
            category_window["_table_countries_"].update(_rows(Data.categories))
        except Exception:
            pass
    elapsed = time.time() - start
    logger.info(
        "Xtream load complete in %.2fs categories=%d live=%d vod=%d",
        elapsed,
        len(Data.categories),
        len(catalog.get("live", [])),
        len(catalog.get("vod", [])),
    )


def _remember_last_account(name: str) -> None:
    _settings_set(last_choice="account", last_account=name)


def _remember_last_m3u(path: str) -> None:
    _settings_set(last_choice="m3u", last_m3u=path)


def _auto_restore_last(window: "sg.Window", category_window=None) -> Optional[str]:
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
            _load_xtream_into_app(window, acc["base"], acc["username"], acc["password"], category_window)
            return True
        except Exception:
            return False

    def _try_m3u() -> bool:
        p = s.get("last_m3u")
        if p and os.path.isfile(p):
            Data.filename = p
            Data.categories = get_categories()
            if category_window:
                category_window["_table_countries_"].update(_rows(Data.categories))
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

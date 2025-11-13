"""Core data models and global Data container.

Data acts as in-memory state shared across UI modules. Avoid putting large objects or network results
at import time; populate after startup.
"""

import os
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class IPTVFileType(Enum):
    """Enumerated playlist file types used in file dialogs."""

    M3U = ("M3U files", "*.m3u")
    M3U8 = ("M3U8 files", "*.m3u8")
    TXT = ("Text files", "*.txt")

    @classmethod
    def all_types(cls):
        return tuple(ft.value for ft in cls)

    @classmethod
    def grouped(cls):
        return "IPTV Playlists", "*.m3u;*.m3u8;*.txt"


class IpModel(BaseModel):
    """Represents an IP info payload returned from ipinfo.io.

    Provides a printable summary via get_results property.
    """

    ip: str
    city: str
    region: str
    country: str
    loc: str
    org: str
    postal: str
    timezone: str

    @property
    def get_results(self) -> str:
        return (
            f"IP: {self.ip}\n"
            f"City: {self.city}\n"
            f"Region: {self.region}\n"
            f"Country: {self.country}\n"
            f"Location: {self.loc}\n"
            f"Organisation: {self.org}\n"
            f"Postal: {self.postal}\n"
            f"Timezone: {self.timezone}\n"
        )


class Data:
    """Global state holder (acts like a lightweight context).

    Attributes are mutated by UI/event handlers; prefer adding explicit
    fields here instead of scattering globals.
    """

    categories: List[str] = []
    categories_master: List[str] = []  # full list as loaded, for filtering
    xtream_account: Optional[dict] = None
    xtream_catalog: Optional[dict] = None
    selected_list: List[str] = []  # raw EXTINF blocks currently selected
    channels: List[str] = []  # parsed display rows
    media_instance = None  # VLC media object
    filename: str = os.path.join(os.getcwd(), "programs.py")
    data: str = ""  # raw M3U file contents
    ip_info = {}  # defer fetching until user opens IP Info
    # New robust parser instance and channel objects list
    m3u_parser = None  # will hold M3UParser instance
    parsed_channels: List[object] = []  # list of Channel dataclasses from m3u_parser
    selected_category_indices: List[int] = []  # newly added: track selected category table indices
    # Caches for fast channel filtering
    rows_cache: List[List[str]] = []  # rows for current selected_list (Title, Rating, Year)
    search_titles_lower: List[str] = []  # lowercase titles aligned to selected_list

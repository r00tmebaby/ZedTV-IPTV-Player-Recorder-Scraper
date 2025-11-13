"""ZedTV IPTV Player - source package.

Subpackages/modules:
- m3u_parser: parsing M3U playlists into structured Channel objects
- epg: XMLTV / JSON EPG ingestion and indexing
- app: application logic (parsing, filtering, recording helpers)
- settings: persistence, last-session restore, Xtream loading
- layout: PySimpleGUI layouts for main and panels
- account: account manager windows and snapshot utilities
- logger_setup: logging initialization with rotation & retention

UI entrypoint: main.py
"""

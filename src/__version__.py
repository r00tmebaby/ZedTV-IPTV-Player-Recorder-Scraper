"""
Version information for ZedTV IPTV Player.

This is the single source of truth for version numbers.
Update this file when bumping version numbers.
"""

__version__ = "2.0.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Application metadata
APP_NAME = "ZedTV IPTV Player"
APP_AUTHOR = "@r00tmebaby"
APP_YEAR = "2025"

# Version string for display
VERSION_STRING = f"v{__version__}"
FULL_VERSION_STRING = f"{APP_NAME} {VERSION_STRING}"

# For compatibility with setup tools and other tooling
__all__ = [
    "__version__",
    "__version_info__",
    "APP_NAME",
    "APP_AUTHOR",
    "APP_YEAR",
    "VERSION_STRING",
    "FULL_VERSION_STRING",
]

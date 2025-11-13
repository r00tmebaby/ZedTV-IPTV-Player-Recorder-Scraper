"""
Thumbnail manager for channel and movie icons
Downloads and caches thumbnails from stream metadata
"""

import hashlib
from pathlib import Path
from io import BytesIO
from typing import Optional

import httpx

try:
    from PIL import Image
except ImportError:
    Image = None  # Will handle missing Pillow gracefully

from core.config import DATA_FOLDER

THUMBNAIL_CACHE = Path(DATA_FOLDER) / "thumbnails"
THUMBNAIL_CACHE.mkdir(parents=True, exist_ok=True)


def get_thumbnail_path(url: str, size: int = 100) -> Optional[str]:
    """
    Download and cache a thumbnail from URL.
    Returns path to cached image or None if failed.
    """
    if not url or not url.startswith("http"):
        return None

    if Image is None:
        # Pillow not installed
        return None

    # Create cache key from URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = THUMBNAIL_CACHE / f"{url_hash}_{size}.png"

    # Return cached file if exists
    if cache_file.exists():
        return str(cache_file)

    # Download and resize thumbnail
    try:
        response = httpx.get(url, timeout=5, follow_redirects=True)
        response.raise_for_status()

        # Open image
        img = Image.open(BytesIO(response.content))

        # Resize to desired size
        img.thumbnail((size, size), Image.Resampling.LANCZOS)

        # Save to cache
        img.save(cache_file, "PNG")

        return str(cache_file)
    except Exception as e:
        print(f"Failed to download thumbnail {url}: {e}")
        return None


def clear_thumbnail_cache():
    """Clear all cached thumbnails."""
    try:
        for file in THUMBNAIL_CACHE.glob("*.png"):
            file.unlink()
    except Exception as e:
        print(f"Failed to clear thumbnail cache: {e}")


def get_cache_size() -> int:
    """Get total size of thumbnail cache in bytes."""
    try:
        return sum(f.stat().st_size for f in THUMBNAIL_CACHE.glob("*.png"))
    except Exception:
        return 0


"""Configuration and utilities for file caching."""

import logging
import os

logger = logging.getLogger(__name__)

DB_FILE: str = "file_cache.db"


def delete_cache() -> None:
    """Delete the cache file if it exists."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

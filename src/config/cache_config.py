"""Configuration and utilities for file caching."""

import logging
import os
import sys

logger = logging.getLogger(__name__)

DB_FILE: str = "file_cache.db"


def delete_cache() -> None:
    """Delete the cache file if it exists."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


def handle_signal() -> None:
    """Handle termination signals by deleting cache and exiting."""
    delete_cache()
    sys.exit(0)

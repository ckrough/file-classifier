"""
Cache initialization and management.

This module handles the lifecycle of the SQLite cache database,
including initialization, schema creation, and cleanup.
"""

import logging
import os
import sqlite3

from src.config.settings import DB_FILE

logger = logging.getLogger(__name__)

CREATE_FILES_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE,
        category TEXT,
        description TEXT,
        vendor TEXT,
        date TEXT,
        suggested_name TEXT
    )
"""


def initialize_cache() -> None:
    """
    Initialize the SQLite cache database, creating the necessary
    table if it does not exist.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute(CREATE_FILES_TABLE_SQL)
            conn.commit()
            logger.debug("Cache database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(
            "Error initializing cache database (%s): %s", DB_FILE, e, exc_info=True
        )


def delete_cache() -> None:
    """Delete the cache file if it exists."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        logger.debug("Cache database deleted successfully.")
